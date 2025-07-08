from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from database import get_db, User
from extra.model import DraftCreateRequest, DraftUpdateRequest, DraftResponse
from extra.service import GmailService

router = APIRouter()
gmail_service = GmailService()

@router.post("/drafts", tags=["Drafts"])
async def create_draft(
    request: DraftCreateRequest,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    try:
        # Build Gmail service
        service = gmail_service.build_service(user.access_token, user.refresh_token, service_name='gmail')
        
        # Create draft in Gmail
        result = gmail_service.create_draft(
            service, 
            request.to, 
            request.subject, 
            request.body,
            request.cc,
            request.bcc
        )
        
        if result:
            return {
                "message": "Draft created successfully", 
                "draft_id": result['id'],
                "draft": result
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to create draft")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Draft creation failed: {str(e)}")

@router.get("/drafts", tags=["Drafts"])
async def get_drafts(
    email: str = Query(...),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    try:
        # Build Gmail service
        service = gmail_service.build_service(user.access_token, user.refresh_token, service_name='gmail')
        
        # Get drafts from Gmail
        results = service.users().drafts().list(userId='me').execute()
        drafts = results.get('drafts', [])
        
        return {"drafts": drafts, "total": len(drafts)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get drafts: {str(e)}")

@router.get("/drafts/{draft_id}", tags=["Drafts"])
async def get_draft(
    draft_id: str,
    email: str = Query(...),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    try:
        # Build Gmail service
        service = gmail_service.build_service(user.access_token, user.refresh_token, service_name='gmail')
        
        # Get specific draft
        draft = service.users().drafts().get(userId='me', id=draft_id).execute()
        
        return {"draft": draft}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get draft: {str(e)}")

@router.put("/drafts/{draft_id}", tags=["Drafts"])
async def update_draft(
    draft_id: str,
    request: DraftUpdateRequest,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    try:
        # Build Gmail service
        service = gmail_service.build_service(user.access_token, user.refresh_token, service_name='gmail')
        
        # Update draft in Gmail
        result = gmail_service.update_draft(
            service, 
            draft_id,
            request.to, 
            request.subject, 
            request.body,
            request.cc,
            request.bcc
        )
        
        if result:
            return {
                "message": "Draft updated successfully", 
                "draft_id": result['id'],
                "draft": result
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to update draft")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Draft update failed: {str(e)}")

@router.delete("/drafts/{draft_id}", tags=["Drafts"])
async def delete_draft(
    draft_id: str,
    email: str = Query(...),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    try:
        # Build Gmail service
        service = gmail_service.build_service(user.access_token, user.refresh_token, service_name='gmail')
        
        # Delete draft from Gmail
        success = gmail_service.delete_draft(service, draft_id)
        
        if success:
            return {"message": "Draft deleted successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete draft")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Draft deletion failed: {str(e)}")

@router.post("/drafts/{draft_id}/send", tags=["Drafts"])
async def send_draft(
    draft_id: str,
    email: str = Query(...),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    try:
        # Build Gmail service
        service = gmail_service.build_service(user.access_token, user.refresh_token, service_name='gmail')
        
        # Send draft
        result = gmail_service.send_draft(service, draft_id)
        
        if result:
            return {
                "message": "Draft sent successfully", 
                "message_id": result['id']
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to send draft")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Draft send failed: {str(e)}")