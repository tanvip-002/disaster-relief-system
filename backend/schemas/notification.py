from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional


#  INPUT schemas 

class NotificationCreate(BaseModel):
    """
    Used internally (by other modules or admin) to send a notification.
    Example: Module 3 calls this after assigning a volunteer.
    """
    user_id: int
    title: str
    message: str

    
    send_email: bool = False

    
    user_email: Optional[EmailStr] = None


class NotificationPermissionRequest(BaseModel):
    """
    Sent by the frontend when asking the user:
    'Do you want to receive email notifications?'
    user_consent = True means they clicked 'Yes, send me emails'
    """
    user_consent: bool


#  OUTPUT schemas 

class NotificationResponse(BaseModel):
    """
    Returned when fetching a user's notifications.
    """
    id: int
    user_id: int
    title: str
    message: str
    is_read: bool
    email_sent: bool
    created_at: datetime

    class Config:
        from_attributes = True