from fastapi import FastAPI
from database import engine, Base


from models.location import Location
from models.notification import Notification


from routes import maps

app = FastAPI(
    title="Disaster Relief Coordination System",
    description="API for coordinating disaster relief efforts.",
    version="1.0.0"
)


Base.metadata.create_all(bind=engine)



app.include_router(maps.router)



@app.get("/")
def root():
    return {"message": "Disaster Relief Coordination System is running."}