from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


#  INPUT schemas 

class LocationCreate(BaseModel):
    """
    Used when an admin adds a new location/relief center.
    All 4 fields are required.
    """
    name: str
    type: str                        
    latitude: float = Field(..., ge=-90, le=90) 
    longitude: float = Field(..., ge=-180, le=180) 


class NearbyRequest(BaseModel):
    """
    Used when a user wants to find centers near their location.
    They send their GPS coordinates + how far to search (in km).
    """
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    radius_km: float = Field(default=10.0, gt=0)  


# OUTPUT schemas 

class LocationResponse(BaseModel):
    """
    Returned when fetching locations.
    Includes the DB-generated id and timestamp.
    """
    id: int
    name: str
    type: str
    latitude: float
    longitude: float
    created_at: datetime

    class Config:
        from_attributes = True  


class NearbyLocationResponse(LocationResponse):
    """
    Same as LocationResponse but also includes the calculated distance
    so the user knows how far each center is from them.
    """
    distance_km: float