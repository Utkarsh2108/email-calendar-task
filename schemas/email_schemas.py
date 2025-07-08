from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

class EmailResponse(BaseModel):
    id: int
    message_id: str
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