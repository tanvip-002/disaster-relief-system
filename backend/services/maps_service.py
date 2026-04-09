import math
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from sqlalchemy.orm import Session
from fastapi import HTTPException
from dotenv import load_dotenv

from models.location import Location
from models.notification import Notification

load_dotenv()



#  MAP LOGIC


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculates the straight-line distance between two GPS coordinates
    using the Haversine formula. Returns distance in kilometers.

    Why Haversine? Because the Earth is a sphere — you can't use
    simple subtraction on lat/long values. This formula accounts
    for the Earth's curvature.

    lat1, lon1 = user's current location
    lat2, lon2 = relief center's location
    """
    R = 6371  # Earth's radius (kms)

    
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    # Haversine formula
    a = (math.sin(delta_phi / 2) ** 2 +
         math.cos(phi1) * math.cos(phi2) *
         math.sin(delta_lambda / 2) ** 2)

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return round(R * c, 2)  


def get_map_locations(db: Session):
    """
    Fetches ALL locations from the database.
    Used to render the full map with all relief centers marked.
    """
    locations = db.query(Location).all()

    if not locations:
        raise HTTPException(status_code=404, detail="No locations found.")

    return locations


def get_nearby_centers(lat: float, lon: float, radius_km: float, db: Session):
    """
    Fetches locations within a given radius from the user's coordinates.

    Strategy:
    1. Load all locations from DB
    2. Calculate distance from user to each location
    3. Filter to only those within radius_km
    4. Sort by closest first
    5. Attach the distance to each result so the user can see it
    """
    all_locations = db.query(Location).all()

    if not all_locations:
        raise HTTPException(status_code=404, detail="No locations in the database.")

    nearby = []

    for loc in all_locations:
        distance = haversine_distance(lat, lon, loc.latitude, loc.longitude)

        if distance <= radius_km:
          
            loc.distance_km = distance
            nearby.append(loc)

    if not nearby:
        raise HTTPException(
            status_code=404,
            detail=f"No relief centers found within {radius_km} km of your location."
        )

    
    nearby.sort(key=lambda x: x.distance_km)

    return nearby



#  NOTIFICATION LOGIC


def send_email_notification(to_email: str, title: str, message: str) -> bool:
    """
    Sends a real email using Gmail SMTP.
    Returns True if successful, False if it fails.

    Only called when:
    - send_email=True in the request
    - AND the user has given consent (checked in the route)
    """
    try:
        mail_user = os.getenv("MAIL_USERNAME")
        mail_pass = os.getenv("MAIL_PASSWORD")
        mail_from = os.getenv("MAIL_FROM")
        mail_server = os.getenv("MAIL_SERVER", "smtp.gmail.com")
        mail_port = int(os.getenv("MAIL_PORT", 587))

        
        msg = MIMEMultipart("alternative")
        msg["Subject"] = title
        msg["From"] = mail_from
        msg["To"] = to_email

       
        text_part = MIMEText(message, "plain")

     
        html_body = f"""
        <html>
          <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2 style="color: #c0392b;">🚨 Disaster Relief System</h2>
            <h3>{title}</h3>
            <p>{message}</p>
            <hr/>
            <small style="color: grey;">
              You received this because you opted in to email notifications.
              This is an automated message — please do not reply.
            </small>
          </body>
        </html>
        """
        html_part = MIMEText(html_body, "html")

        msg.attach(text_part)
        msg.attach(html_part)

     
        with smtplib.SMTP(mail_server, mail_port) as server:
            server.starttls()                        
            server.login(mail_user, mail_pass)       
            server.sendmail(mail_from, to_email, msg.as_string())

        return True

    except Exception as e:
     
        print(f"[EMAIL ERROR] Failed to send email to {to_email}: {e}")
        return False


def send_notification(
    user_id: int,
    title: str,
    message: str,
    db: Session,
    send_email: bool = False,
    user_email: str = None,
    user_consent: bool = False
):
    """
    Main notification function. Does two things:
    1. Always saves an in-app notification to the DB
    2. Optionally sends an email IF:
       - send_email is True (caller requested it)
       - user_consent is True (user said yes to emails)
       - user_email is provided

    Returns the saved Notification object.
    """
    email_was_sent = False

  
    notification = Notification(
        user_id=user_id,
        title=title,
        message=message,
        is_read=False,
        email_sent=False  
    )
    db.add(notification)
    db.flush()  


    if send_email and user_consent and user_email:
        email_was_sent = send_email_notification(user_email, title, message)
        notification.email_sent = email_was_sent

    
    db.commit()
    db.refresh(notification)

    return notification


def get_user_notifications(user_id: int, db: Session):
    """
    Fetches all notifications for a specific user.
    Most recent first.
    """
    notifications = (
        db.query(Notification)
        .filter(Notification.user_id == user_id)
        .order_by(Notification.created_at.desc())
        .all()
    )

    if not notifications:
        raise HTTPException(status_code=404, detail="No notifications found.")

    return notifications


def mark_notification_read(notification_id: int, user_id: int, db: Session):
    """
    Marks a single notification as read.
    Checks that the notification belongs to the requesting user
    so users can't mark each other's notifications.
    """
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == user_id
    ).first()

    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found.")

    notification.is_read = True
    db.commit()
    db.refresh(notification)

    return notification