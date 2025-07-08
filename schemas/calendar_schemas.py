from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime

class EventDateTime(BaseModel):
    dateTime: Optional[datetime] = None
    timeZone: Optional[str] = None

# class EventAttendee(BaseModel):
#     email: EmailStr
#     displayName: Optional[str] = None
#     responseStatus: Optional[str] = None # 'accepted', 'declined', 'needsAction'

class CalendarEventCreate(BaseModel):
    summary: str
    description: Optional[str] = None
    start: EventDateTime
    end: EventDateTime
    location: Optional[str] = None
    # attendees: Optional[List[EventAttendee]] = None

class CalendarEventUpdateRequest(BaseModel):
    summary: Optional[str] = None
    description: Optional[str] = None
    start: Optional[EventDateTime] = None
    end: Optional[EventDateTime] = None
    location: Optional[str] = None
    # attendees: Optional[List[EventAttendee]] = None

class CalendarEventResponse(BaseModel):
    id: str
    summary: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    start: EventDateTime
    end: EventDateTime
    creator: Optional[Dict[str, Any]] = None
    organizer: Optional[Dict[str, Any]] = None
    # attendees: Optional[List[EventAttendee]] = None
    status: Optional[str] = None
    htmlLink: Optional[str] = None
    created: Optional[datetime] = None
    updated: Optional[datetime] = None
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class CalendarEventListResponse(BaseModel):
    events: List[CalendarEventResponse]
    total: int