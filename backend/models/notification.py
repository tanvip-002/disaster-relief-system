from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from database import Base


class Notification(Base):
    """
    Stores in-app notifications for users.
    Each row is one notification sent to one user.
    Maps to the 'notifications' table in PostgreSQL.
    """
    __tablename__ = "notifications"

   
    id = Column(Integer, primary_key=True, index=True)

    

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

   
    title = Column(String, nullable=False)

    
    message = Column(String, nullable=False)

  
    is_read = Column(Boolean, default=False)


    email_sent = Column(Boolean, default=False)


    created_at = Column(DateTime(timezone=True), server_default=func.now())