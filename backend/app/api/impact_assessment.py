from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Form
from pydantic import BaseModel
from typing import Dict, List
import shutil
import os
from datetime import datetime
import uuid
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.history import History
from app.models.user import User

router = APIRouter()

# Create upload directory if it doesn't exist
UPLOAD_DIR = "uploads/impact_assessment"
os.makedirs(UPLOAD_DIR, exist_ok=True)

class ReportRequest(BaseModel):
    userId: str
    filters: Dict[str, List[str]]
    reportId: str

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...), 
    userId: str = Form(None), 
    fileId: str = Form(None),
    db: Session = Depends(get_db)
):
    if not userId or not fileId:
        raise HTTPException(status_code=400, detail="Missing userId or fileId")
    
    # Check if user exists
    user = db.query(User).filter(User.id == userId).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    try:
        # Save file with unique ID
        file_path = os.path.join(UPLOAD_DIR, f"{fileId}_{file.filename}")
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Record in history
        history_entry = History(
            id=str(uuid.uuid4()),
            user_id=userId,
            activity_type="impact_assessment",
            file_id=fileId,
            file_name=file.filename
        )
        db.add(history_entry)
        db.commit()
        
        return {
            "message": "File uploaded successfully",
            "fileId": fileId,
            "fileName": file.filename
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/report")
async def generate_report(
    request: ReportRequest,
    db: Session = Depends(get_db)
):
    try:
        # Check if user exists
        user = db.query(User).filter(User.id == request.userId).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Record in history
        history_entry = History(
            id=str(uuid.uuid4()),
            user_id=request.userId,
            activity_type="impact_assessment",
            file_id=request.reportId,
            report_id=request.reportId,
            filters=request.filters
        )
        db.add(history_entry)
        db.commit()
        
        return {
            "message": "Report generated successfully",
            "reportId": request.reportId,
            "generatedAt": datetime.now().isoformat()
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

__all__ = ["router"]
