from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from database import get_db, User, Email
from extra.model import EmailSendRequest, EmailResponse, EmailListResponse
from extra.service import GmailService
from typing import Optional

router = APIRouter()
gmail_service = GmailService()

@router.post("/emails/sync", tags=["Inbox"])
async def sync_emails(email: str = Query(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    try:
        # Build Gmail service
        service = gmail_service.build_service(user.access_token, user.refresh_token, service_name='gmail')
        
        # Get messages from Gmail
        messages = gmail_service.list_messages(service, max_results=100)
        
        synced_count = 0
        for msg in messages:
            # Check if email already exists (fixed: use message_id instead of gmail_id)
            existing_email = db.query(Email).filter(Email.message_id == msg['id']).first()
            if existing_email:
                continue
            
            # Get full message
            full_message = gmail_service.get_message(service, msg['id'])
            if not full_message:
                continue
            
            # Parse message
            parsed_message = gmail_service.parse_message(full_message)
            
            # Create email record
            email_record = Email(
                user_id=user.id,
                **parsed_message
            )
            db.add(email_record)
            synced_count += 1
        
        db.commit()
        return {"message": f"Synced {synced_count} new emails"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")

@router.get("/emails", response_model=EmailListResponse, tags=["Inbox"])
async def get_emails(
    email: str = Query(...),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    query: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Calculate offset
    offset = (page - 1) * per_page
    
    # Build query
    email_query = db.query(Email).filter(Email.user_id == user.id, Email.is_deleted == False)
    
    if query:
        email_query = email_query.filter(
            Email.subject.contains(query) | 
            Email.sender.contains(query) | 
            Email.body_text.contains(query)
        )
    
    # Get total count
    total = email_query.count()
    
    # Get emails with pagination
    emails = email_query.order_by(Email.received_at.desc()).offset(offset).limit(per_page).all()
    
    return EmailListResponse(
        emails=emails,
        total=total,
        page=page,
        per_page=per_page
    )

@router.get("/emails/{email_id}", response_model=EmailResponse, tags=["Email Actions"])
async def get_email(
    email_id: int,
    email: str = Query(...),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    email_record = db.query(Email).filter(
        Email.id == email_id,
        Email.user_id == user.id,
        Email.is_deleted == False
    ).first()
    
    if not email_record:
        raise HTTPException(status_code=404, detail="Email not found")
    
    # Mark as read
    if not email_record.is_read:
        email_record.is_read = True
        db.commit()
    
    return email_record

@router.post("/emails/send", tags=["Email Sending"])
async def send_email(
    request: EmailSendRequest,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    try:
        # Build Gmail service
        service = gmail_service.build_service(user.access_token, user.refresh_token, service_name='gmail')
        
        # Send email
        result = gmail_service.send_email(service, request.to, request.subject, request.body)
        
        if result:
            return {"message": "Email sent successfully", "message_id": result['id']}
        else:
            raise HTTPException(status_code=500, detail="Failed to send email")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Send failed: {str(e)}")

@router.put("/emails/{email_id}/star", tags=["Email Star"])
async def toggle_star_email(
    email_id: int,
    email: str = Query(...),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    email_record = db.query(Email).filter(
        Email.id == email_id,
        Email.user_id == user.id,
        Email.is_deleted == False
    ).first()
    
    if not email_record:
        raise HTTPException(status_code=404, detail="Email not found")
    
    # Toggle star status
    email_record.is_starred = not email_record.is_starred
    db.commit()
    
    # Also update in Gmail if possible
    try:
        service = gmail_service.build_service(user.access_token, user.refresh_token, service_name='gmail')
        if email_record.is_starred:
            gmail_service.modify_message(service, email_record.message_id, add_labels=['STARRED'])
        else:
            gmail_service.modify_message(service, email_record.message_id, remove_labels=['STARRED'])
    except Exception as e:
        # If Gmail update fails, just log it but don't fail the request
        print(f"Failed to update star status in Gmail: {e}")
    
    return {
        "message": f"Email {'starred' if email_record.is_starred else 'unstarred'}",
        "is_starred": email_record.is_starred
    }

@router.put("/emails/{email_id}/star/add", tags=["Email Star"])
async def star_email(
    email_id: int,
    email: str = Query(...),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    email_record = db.query(Email).filter(
        Email.id == email_id,
        Email.user_id == user.id,
        Email.is_deleted == False
    ).first()
    
    if not email_record:
        raise HTTPException(status_code=404, detail="Email not found")
    
    if email_record.is_starred:
        return {"message": "Email is already starred", "is_starred": True}
    
    # Star the email
    email_record.is_starred = True
    db.commit()
    
    # Also update in Gmail if possible
    try:
        service = gmail_service.build_service(user.access_token, user.refresh_token, service_name='gmail')
        gmail_service.modify_message(service, email_record.message_id, add_labels=['STARRED'])
    except Exception as e:
        print(f"Failed to star email in Gmail: {e}")
    
    return {"message": "Email starred successfully", "is_starred": True}

@router.put("/emails/{email_id}/star/remove", tags=["Email Star"])
async def unstar_email(
    email_id: int,
    email: str = Query(...),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    email_record = db.query(Email).filter(
        Email.id == email_id,
        Email.user_id == user.id,
        Email.is_deleted == False
    ).first()
    
    if not email_record:
        raise HTTPException(status_code=404, detail="Email not found")
    
    if not email_record.is_starred:
        return {"message": "Email is not starred", "is_starred": False}
    
    # Unstar the email
    email_record.is_starred = False
    db.commit()
    
    # Also update in Gmail if possible
    try:
        service = gmail_service.build_service(user.access_token, user.refresh_token, service_name='gmail')
        gmail_service.modify_message(service, email_record.message_id, remove_labels=['STARRED'])
    except Exception as e:
        print(f"Failed to unstar email in Gmail: {e}")
    
    return {"message": "Email unstarred successfully", "is_starred": False}

@router.delete("/emails/{email_id}", tags=["Email Actions"])
async def delete_email(
    email_id: int,
    email: str = Query(...),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    email_record = db.query(Email).filter(
        Email.id == email_id,
        Email.user_id == user.id,
    ).first()
    
    if not email_record:
        raise HTTPException(status_code=404, detail="Email not found")
    
    email_record.is_deleted = True
    db.commit()
    
    return {"message": "Email deleted"}