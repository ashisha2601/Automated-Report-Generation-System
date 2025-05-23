from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.models.history import History
from app.models.user import User
from pydantic import BaseModel
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()
__all__ = ["router"]

# ✅ Updated schema to match your model fields
class HistoryResponse(BaseModel):
    id: str
    activity_type: str
    file_id: str
    file_name: Optional[str] = None
    report_id: Optional[str] = None
    filters: Optional[dict] = None
    created_at: datetime

    class Config:
        from_attributes = True

@router.get("/{user_id}", response_model=List[HistoryResponse])
async def get_user_history(user_id: str, db: Session = Depends(get_db)):
    try:
        logger.info(f"Fetching history for user: {user_id}")
        
        # First check if user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.warning(f"User not found: {user_id}")
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get user's history
        history = db.query(History).filter(History.user_id == user_id).order_by(History.created_at.desc()).all()
        logger.info(f"Found {len(history)} history records for user {user_id}")
        return history
    except Exception as e:
        logger.error(f"Error fetching history for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{user_id}/activity/{activity_type}", response_model=List[HistoryResponse])
async def get_user_activity_history(
    user_id: str, 
    activity_type: str, 
    db: Session = Depends(get_db)
):
    try:
        logger.info(f"Fetching {activity_type} history for user: {user_id}")
        
        # First check if user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.warning(f"User not found: {user_id}")
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get user's history for specific activity type
        history = db.query(History).filter(
            History.user_id == user_id,
            History.activity_type == activity_type
        ).order_by(History.created_at.desc()).all()
        
        logger.info(f"Found {len(history)} {activity_type} history records for user {user_id}")
        return history
    except Exception as e:
        logger.error(f"Error fetching {activity_type} history for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

