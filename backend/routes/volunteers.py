from fastapi import APIRouter


router = APIRouter()

@router.get("/test")
def test_module():
    return {"message": "Module is connected and ready!"}