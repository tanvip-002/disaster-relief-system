from sqlalchemy import Column, Integer, String, Float
from backend.database import Base

class Location(Base):
    __tablename__ = "locations"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    type = Column(String) 
    latitude = Column(Float)
    longitude = Column(Float)