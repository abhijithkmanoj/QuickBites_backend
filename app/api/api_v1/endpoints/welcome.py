from fastapi import APIRouter

router = APIRouter()


@router.get("", summary="Welcome message")
def welcome():
    return {"message": "Welcome to QuickBites backend"}
