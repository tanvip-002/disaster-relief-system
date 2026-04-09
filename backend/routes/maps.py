from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from schemas.location import LocationCreate, LocationResponse, NearbyRequest, NearbyLocationResponse
from schemas.notification import NotificationCreate, NotificationResponse, NotificationPermissionRequest
from services.maps_service import (
    get_map_locations,
    get_nearby_centers,
    send_notification,
    get_user_notifications,
    mark_notification_read
)





from services.auth_service import get_current_user





router = APIRouter(
    prefix="/maps",       
    tags=["Maps & Notifications"]   
)



# MAP ENDPOINTS

@router.get("/locations", response_model=List[LocationResponse])
def fetch_all_locations(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)   # requires login
):
    """
    GET /maps/locations

    Returns all relief center locations stored in the database.
    Used by the frontend to render all pins on the map.

    Requires: Valid JWT token in Authorization header.
    """
    return get_map_locations(db)


@router.post("/locations", response_model=LocationResponse, status_code=201)
def add_location(
    location_data: LocationCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    POST /maps/locations

    Adds a new relief center location to the database.
    Only admins should be able to do this.

    Requires: Valid JWT token + user must be an admin.
    """
    # Role check 
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Only admins can add new locations."
        )

    from models.location import Location
    new_location = Location(
        name=location_data.name,
        type=location_data.type,
        latitude=location_data.latitude,
        longitude=location_data.longitude
    )
    db.add(new_location)
    db.commit()
    db.refresh(new_location)

    return new_location


@router.post("/locations/nearby", response_model=List[NearbyLocationResponse])
def fetch_nearby_centers(
    request: NearbyRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    POST /maps/locations/nearby

    Accepts the user's GPS coordinates + search radius.
    Returns all relief centers within that radius, sorted by distance.

    Request body example:
    {
        "latitude": 19.0760,
        "longitude": 72.8777,
        "radius_km": 10
    }

    Requires: Valid JWT token.
    """
    return get_nearby_centers(
        lat=request.latitude,
        lon=request.longitude,
        radius_km=request.radius_km,
        db=db
    )



# NOTIFICATION ENDPOINTS


@router.post("/notifications/send", response_model=NotificationResponse, status_code=201)
def send_notification_endpoint(
    notification_data: NotificationCreate,
    permission: NotificationPermissionRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    POST /maps/notifications/send

    Sends a notification to a user.
    - Always saves an in-app notification to the DB.
    - Sends an email ONLY IF:
        1. send_email=True in the request body
        2. The user gave consent (permission.user_consent=True)
        3. A valid user_email was provided

    Only admins can trigger notifications for other users.
    Regular users can only notify themselves (edge case for testing).

    Request body example:
    {
        "user_id": 5,
        "title": "Help Request Update",
        "message": "A volunteer has been assigned to your request.",
        "send_email": true,
        "user_email": "victim@example.com"
    }
    + permission body:
    {
        "user_consent": true
    }

    Requires: Valid JWT token.
    """
    
    if current_user.role != "admin" and notification_data.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You can only send notifications to yourself unless you are an admin."
        )

    return send_notification(
        user_id=notification_data.user_id,
        title=notification_data.title,
        message=notification_data.message,
        db=db,
        send_email=notification_data.send_email,
        user_email=notification_data.user_email,
        user_consent=permission.user_consent
    )


@router.get("/notifications", response_model=List[NotificationResponse])
def fetch_my_notifications(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    GET /maps/notifications

    Returns all notifications for the currently logged-in user.
    Sorted by newest first.

    Requires: Valid JWT token.
    """
    return get_user_notifications(user_id=current_user.id, db=db)


@router.patch("/notifications/{notification_id}/read", response_model=NotificationResponse)
def mark_as_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    PATCH /maps/notifications/{id}/read

    Marks a specific notification as read (is_read = True).
    Users can only mark their own notifications as read.

    Requires: Valid JWT token.
    """
    return mark_notification_read(
        notification_id=notification_id,
        user_id=current_user.id,
        db=db
    )