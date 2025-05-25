from fastapi import APIRouter, HTTPException, Depends, Form
from pydantic import BaseModel, EmailStr
from typing import Optional
import random
import string
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User
from datetime import datetime
import uuid # Import uuid to generate a unique ID

router = APIRouter()

# In-memory storage for OTPs (replace with database in production)
otp_store = {}

class LoginRequest(BaseModel):
    email: EmailStr

# Keep userId in the verification request, frontend still sends it,
# but backend will generate its own if creating a new user.
class OTPVerification(BaseModel):
    email: EmailStr
    otp: str
    userId: str # Frontend still provides this, but backend's takes precedence for new users

class UserResponse(BaseModel):
    email: str
    name: str
    userId: str # Ensure this returns the backend's authoritative ID
    memberSince: str

class ProfileUpdateRequest(BaseModel):
    userId: str
    fullName: Optional[str] = None
    designation: Optional[str] = None
    department: Optional[str] = None

@router.post("/login")
async def request_otp(request: LoginRequest):
    if not request.email.endswith("@agastya.org"):
        raise HTTPException(status_code=400, detail="Invalid email domain")
    
    # Generate a 4-digit OTP
    otp = ''.join(random.choices(string.digits, k=4))
    otp_store[request.email] = otp
    print(f"OTP for {request.email}: {otp}")  # <-- This should print in your backend terminal
    
    # In production, send OTP via email (this print simulates sending)
    print(f"Simulating sending OTP to {request.email}: {otp}")
    
    return {"message": "OTP sent successfully"}

@router.post("/verify-otp")
async def verify_otp(verification: OTPVerification, db: Session = Depends(get_db)):
    stored_otp = otp_store.get(verification.email)
    
    if not stored_otp or stored_otp != verification.otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")
    
    # Clear OTP after successful verification
    # del otp_store[verification.email] # Keep OTP for a short time for potential retries or reloads

    # --- Modified Logic: Check by email first ---
    user = db.query(User).filter(User.email == verification.email).first()

    if user is None:
        # If user with this email doesn't exist, create a new one
        # *** GENERATE UNIQUE ID ON THE BACKEND ***
        new_user_id = str(uuid.uuid4()) # Generate a standard UUID
        user = User(
            id=new_user_id, # Use the backend-generated unique ID
            email=verification.email,
            name=verification.email.split("@")[0].title(), # Use a simple default name from email
            created_at=datetime.utcnow()
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        print(f"Created new user during OTP verification: {user.email} with backend-generated ID {user.id}") # Log creation
    else:
        # If user with this email exists, use the existing user's ID
        # The frontend might have generated an ID, but the backend's existing ID is authoritative.
        print(f"User already exists: {user.email} with existing ID {user.id}. Using existing user.") # Log existing
        # The frontend receives this user.id and uses it to fetch history.

    # --- End Modified Logic ---

    return UserResponse(
        email=user.email,
        name=user.name,
        userId=user.id, # Return the actual ID from the database (newly created or existing)
        memberSince=user.created_at.isoformat() if user.created_at else datetime.utcnow().isoformat() # Ensure memberSince is always a string
    )

@router.put("/users/{userId}")
async def update_user_profile(userId: str, profile_data: ProfileUpdateRequest, db: Session = Depends(get_db)):
    print(f"Attempting to update profile for userId: {userId}")
    user = db.query(User).filter(User.id == userId).first()
    
    if not user:
        print(f"User not found: {userId}")
        raise HTTPException(status_code=404, detail="User not found")

    # Update user fields if provided in the request body
    if profile_data.fullName is not None:
        user.name = profile_data.fullName
    if profile_data.designation is not None:
        user.designation = profile_data.designation
    if profile_data.department is not None:
        user.department = profile_data.department

    try:
        db.commit()
        db.refresh(user)
        print(f"Profile updated successfully for userId: {userId}")
        return {"message": "Profile updated successfully", "user": user}
    except Exception as e:
        db.rollback()
        print(f"Error updating profile for userId {userId}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update profile: {e}")

@router.get("/users/{userId}")
async def get_user_profile(userId: str, db: Session = Depends(get_db)):
    print(f"Attempting to fetch profile for userId: {userId}")
    user = db.query(User).filter(User.id == userId).first()

    if not user:
        print(f"User not found: {userId}")
        raise HTTPException(status_code=404, detail="User not found")

    # Return user data, including potentially updated fields
    return {
        "userId": user.id,
        "email": user.email,
        "name": user.name, # This now comes from the database (updated name)
        "designation": user.designation,
        "department": user.department,
        "memberSince": user.created_at.isoformat() if user.created_at else None
    }

__all__ = ["router"]
