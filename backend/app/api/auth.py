from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from typing import Optional
import random
import string
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User
from datetime import datetime

router = APIRouter()

# In-memory storage for OTPs (replace with database in production)
otp_store = {}

class LoginRequest(BaseModel):
    email: EmailStr

class OTPVerification(BaseModel):
    email: EmailStr
    otp: str
    userId: str

class UserResponse(BaseModel):
    email: str
    name: str
    userId: str
    memberSince: str

@router.post("/login")
async def request_otp(request: LoginRequest):
    if not request.email.endswith("@agastya.org"):
        raise HTTPException(status_code=400, detail="Invalid email domain")
    
    # Generate a 4-digit OTP
    otp = ''.join(random.choices(string.digits, k=4))
    otp_store[request.email] = otp
    
    # In production, send OTP via email
    print(f"OTP for {request.email}: {otp}")
    
    return {"message": "OTP sent successfully"}

@router.post("/verify-otp")
async def verify_otp(verification: OTPVerification, db: Session = Depends(get_db)):
    stored_otp = otp_store.get(verification.email)
    
    if not stored_otp or stored_otp != verification.otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")
    
    # Clear OTP after successful verification
    del otp_store[verification.email]
    
    # Check if user exists, if not create them
    user = db.query(User).filter(User.id == verification.userId).first()
    if not user:
        user = User(
            id=verification.userId,
            email=verification.email,
            name=verification.email.split("@")[0].title(),
            created_at=datetime.utcnow()
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    
    return UserResponse(
        email=user.email,
        name=user.name,
        userId=user.id,
        memberSince=user.created_at.isoformat()
    )

__all__ = ["router"]
