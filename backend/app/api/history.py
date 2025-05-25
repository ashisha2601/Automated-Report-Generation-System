from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.models.history import History
from app.models.user import User
from pydantic import BaseModel
from datetime import datetime
import logging
import csv
import os
from fastapi.responses import FileResponse

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()
__all__ = ["router"]

# ✅ Updated schema to match your model fields
class HistoryResponse(BaseModel):
    id: str
    user_id: str
    activity_type: str
    file_id: str
    file_name: Optional[str] = None
    report_id: Optional[str] = None
    filters: Optional[dict] = None
    created_at: datetime

    class Config:
        from_attributes = True

# ✅ Moved this route to be defined before /{user_id}
@router.get("/all", response_model=List[HistoryResponse])
async def get_all_history(db: Session = Depends(get_db)):
    try:
        logger.info("Fetching all history records")
        # Query all history records, ordered by creation date descending
        history = db.query(History).order_by(History.created_at.desc()).all()
        logger.info(f"Found {len(history)} total history records")
        return history
    except Exception as e:
        logger.error(f"Error fetching all history records: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/export/csv")
async def export_history_to_csv(db: Session = Depends(get_db)):
    try:
        logger.info("Exporting history records to CSV")
        
        # Create reports directory if it doesn't exist
        reports_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "reports")
        os.makedirs(reports_dir, exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"history_export_{timestamp}.csv"
        filepath = os.path.join(reports_dir, filename)
        
        # Get all history records
        history = db.query(History).order_by(History.created_at.desc()).all()
        
        # Write to CSV
        with open(filepath, 'w', newline='') as csvfile:
            fieldnames = ['id', 'user_id', 'activity_type', 'file_id', 'file_name', 'report_id', 'filters', 'created_at']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for record in history:
                writer.writerow({
                    'id': record.id,
                    'user_id': record.user_id,
                    'activity_type': record.activity_type,
                    'file_id': record.file_id,
                    'file_name': record.file_name,
                    'report_id': record.report_id,
                    'filters': str(record.filters) if record.filters else None,
                    'created_at': record.created_at.isoformat()
                })
        
        logger.info(f"Successfully exported {len(history)} records to {filepath}")
        
        # Return the file
        return FileResponse(
            path=filepath,
            filename=filename,
            media_type='text/csv'
        )
        
    except Exception as e:
        logger.error(f"Error exporting history to CSV: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

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

