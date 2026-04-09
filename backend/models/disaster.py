from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.sql import func
from backend.database import Base

class DisasterReport(Base):
    __tablename__ = "disaster_reports"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String, nullable=False)
    description = Column(String)
    location = Column(String)
    status = Column(String, default="reported") 
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class HelpRequest(Base):
    __tablename__ = "help_requests"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    type = Column(String) 
    description = Column(String)
    status = Column(String, default="reported")
    created_at = Column(DateTime(timezone=True), server_default=func.now())