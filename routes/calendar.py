import json
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from database import get_db, User
from extra.model import CalendarEventCreate, CalendarEventUpdateRequest, CalendarEventResponse, CalendarEventListResponse
from extra.service import GmailService
from typing import Optional
from datetime import datetime
from googleapiclient.errors import HttpError 

router = APIRouter()
gmail_service = GmailService()

@router.post("/calendar/events", response_model=CalendarEventResponse, tags=["Calendar Events"])
async def create_calendar_event(
    event_data: CalendarEventCreate,
    email: str = Query(...),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    try:
        # Build Calendar service
        calendar_service = gmail_service.build_service(user.access_token, user.refresh_token, service_name='calendar', version='v3')
        
        # Convert Pydantic model to dictionary for Google Calendar API
        event_body = event_data.model_dump(exclude_unset=True, by_alias=True)
        
        # Ensure dateTime is correctly formatted for Google Calendar API
        if event_body.get('start') and event_body['start'].get('dateTime'):
            start_dt = event_body['start']['dateTime']
            if isinstance(start_dt, datetime):
                # Ensure it's timezone-aware (UTC) if no timezone was provided by the user
                # If it's naive, assume UTC and add 'Z'
                if start_dt.tzinfo is None:
                    event_body['start']['dateTime'] = start_dt.isoformat() + 'Z'
                else:
                    event_body['start']['dateTime'] = start_dt.isoformat()
        if event_body.get('end') and event_body['end'].get('dateTime'):
            end_dt = event_body['end']['dateTime']
            if isinstance(end_dt, datetime):
                if end_dt.tzinfo is None:
                    event_body['end']['dateTime'] = end_dt.isoformat() + 'Z'
                else:
                    event_body['end']['dateTime'] = end_dt.isoformat()
        
        print(f"Attempting to create calendar event with body:\n{json.dumps(event_body, indent=2)}") # Debug print

        created_event = gmail_service.create_calendar_event(calendar_service, event_body)
        
        if created_event:
            return CalendarEventResponse(**created_event)
        else:
            raise HTTPException(status_code=500, detail="Failed to create calendar event: No event returned from Google API.")
            
    except HttpError as e:
        # Capture and re-raise HttpError with more details
        print(f"Google API Error: Status {e.resp.status}, Content: {e.content.decode()}") # Decode content for readability
        raise HTTPException(status_code=e.resp.status, detail=f"Calendar event creation failed: {e.content.decode()}")
    except Exception as e:
        # Catch any other exceptions and provide their string representation
        print(f"Unexpected error during calendar event creation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Calendar event creation failed: {str(e)}")

@router.get("/calendar/events", response_model=CalendarEventListResponse, tags=["Calendar Events"])
async def list_calendar_events(
    email: str = Query(...),
    # time_min: Optional[datetime] = Query(None, description="Start date/time for events (ISO 8601 format)"),
    # time_max: Optional[datetime] = Query(None, description="End date/time for events (ISO 8601 format)"),
    max_results: int = Query(10, ge=1, le=2500),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    try:
        calendar_service = gmail_service.build_service(user.access_token, user.refresh_token, service_name='calendar', version='v3')
        
        # Format time_min and time_max to ISO 8601 with 'Z' for UTC if they are present
        # time_min_iso = time_min.isoformat() + 'Z' if time_min else None
        # time_max_iso = time_max.isoformat() + 'Z' if time_max else None

        events = gmail_service.list_calendar_events(
            calendar_service, 
            # time_min=time_min_iso, 
            # time_max=time_max_iso, 
            max_results=max_results
        )
        
        return CalendarEventListResponse(
            events=[CalendarEventResponse(**event) for event in events],
            total=len(events)
        )
            
    except HttpError as e:
        print(f"Google API Error: Status {e.resp.status}, Content: {e.content.decode()}")
        raise HTTPException(status_code=e.resp.status, detail=f"Failed to list calendar events: {e.content.decode()}")
    except Exception as e:
        print(f"Unexpected error during calendar event listing: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list calendar events: {str(e)}")
    
@router.get("/calendar/events/{event_id}", response_model=CalendarEventResponse, tags=["Calendar Events"])
async def get_calendar_event(
    event_id: str,
    email: str = Query(...),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    try:
        calendar_service = gmail_service.build_service(user.access_token, user.refresh_token, service_name='calendar', version='v3')
        event = gmail_service.get_calendar_event(calendar_service, event_id)
        
        if event:
            return CalendarEventResponse(**event)
        else:
            raise HTTPException(status_code=404, detail="Calendar event not found")
            
    except HttpError as e:
        print(f"Google API Error: Status {e.resp.status}, Content: {e.content.decode()}")
        raise HTTPException(status_code=e.resp.status, detail=f"Failed to get calendar event: {e.content.decode()}")
    except Exception as e:
        print(f"Unexpected error during calendar event retrieval: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get calendar event: {str(e)}")

@router.put("/calendar/events/{event_id}", response_model=CalendarEventResponse, tags=["Calendar Events"])
async def update_calendar_event(
    event_id: str,
    event_data: CalendarEventUpdateRequest,
    email: str = Query(...),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    try:
        calendar_service = gmail_service.build_service(user.access_token, user.refresh_token, service_name='calendar', version='v3')
        
        # Convert Pydantic model to dictionary for Google Calendar API
        event_body = event_data.model_dump(exclude_unset=True, by_alias=True)

        # Ensure dateTime is correctly formatted for Google Calendar API
        if event_body.get('start') and event_body['start'].get('dateTime'):
            start_dt = event_body['start']['dateTime']
            if isinstance(start_dt, datetime):
                if start_dt.tzinfo is None:
                    event_body['start']['dateTime'] = start_dt.isoformat() + 'Z'
                else:
                    event_body['start']['dateTime'] = start_dt.isoformat()
        if event_body.get('end') and event_body['end'].get('dateTime'):
            end_dt = event_body['end']['dateTime']
            if isinstance(end_dt, datetime):
                if end_dt.tzinfo is None:
                    event_body['end']['dateTime'] = end_dt.isoformat() + 'Z'
                else:
                    event_body['end']['dateTime'] = end_dt.isoformat()
        
        print(f"Attempting to update calendar event with body:\n{json.dumps(event_body, indent=2)}") # Debug print

        updated_event = gmail_service.update_calendar_event(calendar_service, event_id, event_body)
        
        if updated_event:
            return CalendarEventResponse(**updated_event)
        else:
            raise HTTPException(status_code=500, detail="Failed to update calendar event: No event returned from Google API.")
            
    except HttpError as e:
        print(f"Google API Error: Status {e.resp.status}, Content: {e.content.decode()}")
        raise HTTPException(status_code=e.resp.status, detail=f"Calendar event update failed: {e.content.decode()}")
    except Exception as e:
        print(f"Unexpected error during calendar event update: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Calendar event update failed: {str(e)}")

@router.delete("/calendar/events/{event_id}", tags=["Calendar Events"])
async def delete_calendar_event(
    event_id: str,
    email: str = Query(...),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    try:
        calendar_service = gmail_service.build_service(user.access_token, user.refresh_token, service_name='calendar', version='v3')
        success = gmail_service.delete_calendar_event(calendar_service, event_id)
        
        if success:
            return {"message": "Calendar event deleted successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete calendar event: Google API did not confirm deletion.")
            
    except HttpError as e:
        print(f"Google API Error: Status {e.resp.status}, Content: {e.content.decode()}")
        raise HTTPException(status_code=e.resp.status, detail=f"Calendar event deletion failed: {e.content.decode()}")
    except Exception as e:
        print(f"Unexpected error during calendar event deletion: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Calendar event deletion failed: {str(e)}")
