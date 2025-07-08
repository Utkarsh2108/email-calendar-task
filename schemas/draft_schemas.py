from pydantic import BaseModel, EmailStr
from typing import Optional

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