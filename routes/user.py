from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from database import get_db, User
from extra.model import UserResponse

router = APIRouter()

@router.get("/users/me", response_model=UserResponse, tags=["Users"])
async def get_current_user(email: str = Query(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user