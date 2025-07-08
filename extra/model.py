from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime

class UserCreate(BaseModel):
    email: EmailStr
    name: str

class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    created_at: datetime
    is_active: bool
    
    class Config:
        from_attributes = True

class EmailResponse(BaseModel):
    id: int
    message_id: str  # Fixed: changed from gmail_id to message_id
    subject: str
    sender: str
    recipient: str
    body_text: Optional[str]
    body_html: Optional[str]
    is_read: bool
    is_starred: bool
    labels: Optional[str]
    received_at: datetime
    
    class Config:
        from_attributes = True

class EmailListResponse(BaseModel):
    emails: List[EmailResponse]
    total: int
    page: int
    per_page: int

class EmailSendRequest(BaseModel):
    email: EmailStr  # User's email (sender)
    to: EmailStr     # Recipient email
    subject: str
    body: str

# Draft Models
class DraftCreateRequest(BaseModel):
    email: EmailStr     # User's email (sender)
    to: EmailStr        # Recipient email
    subject: str
    body: str
    cc: Optional[str] = None
    bcc: Optional[str] = None

class DraftUpdateRequest(BaseModel):
    email: EmailStr     # User's email (sender)
    to: EmailStr        # Recipient email
    subject: str
    body: str
    cc: Optional[str] = None
    bcc: Optional[str] = None

class DraftResponse(BaseModel):
    id: str
    message: dict
    
    class Config:
        from_attributes = True

# --- Calendar Models ---

class EventDateTime(BaseModel):
    dateTime: Optional[datetime] = None
    # date: Optional[str] = None # For all-day events, e.g., "2024-07-07"
    # timeZone: Optional[str] = None

# class EventAttendee(BaseModel):
#     email: EmailStr
#     # displayName: Optional[str] = None
#     # responseStatus: Optional[str] = None # 'accepted', 'declined', 'needsAction'

# class EventReminder(BaseModel):
#     method: str # 'email', 'popup'
#     minutes: int

# class EventReminders(BaseModel):
#     useDefault: Optional[bool] = None
#     overrides: Optional[List[EventReminder]] = None

class CalendarEventCreate(BaseModel):
    summary: str
    description: Optional[str] = None
    start: EventDateTime
    end: EventDateTime
    location: Optional[str] = None
    # attendees: Optional[List[EventAttendee]] = None
    # reminders: Optional[EventReminders] = None
    # Add other common fields as needed, e.g., recurrence, transparency, visibility

class CalendarEventUpdateRequest(BaseModel):
    summary: Optional[str] = None
    description: Optional[str] = None
    start: Optional[EventDateTime] = None
    end: Optional[EventDateTime] = None
    location: Optional[str] = None
    # attendees: Optional[List[EventAttendee]] = None
    # reminders: Optional[EventReminders] = None

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
