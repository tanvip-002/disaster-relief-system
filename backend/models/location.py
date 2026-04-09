from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func
from database import Base


class Location(Base):
    """
    Represents a physical location/relief center on the map.
    Maps to the 'locations' table in PostgreSQL.
    """
    __tablename__ = "locations"

   
    id = Column(Integer, primary_key=True, index=True)

    
    name = Column(String, nullable=False)

   
    type = Column(String, nullable=False)

    
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)

    
    created_at = Column(DateTime(timezone=True), server_default=func.now())