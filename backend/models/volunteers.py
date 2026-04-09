from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from backend.database import Base

class Volunteer(Base):
    __tablename__ = "volunteers"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    availability = Column(Boolean, default=True)

class Assignment(Base):
    __tablename__ = "assignments"
    id = Column(Integer, primary_key=True, index=True)
    volunteer_id = Column(Integer, ForeignKey("volunteers.id"))
    request_id = Column(Integer, ForeignKey("help_requests.id"))
    status = Column(String, default="assigned") 

class Resource(Base):
    __tablename__ = "resources"
    id = Column(Integer, primary_key=True, index=True)
    type = Column(String)
    quantity = Column(Integer)
    location = Column(String)