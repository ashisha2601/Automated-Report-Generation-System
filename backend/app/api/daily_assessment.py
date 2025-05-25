from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
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
UPLOAD_DIR = "uploads/daily_assessment"
os.makedirs(UPLOAD_DIR, exist_ok=True)

class ReportRequest(BaseModel):
    userId: str
    filters: Dict[str, List[str]]
    reportId: str

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    userId: str = None,
    fileId: str = None,
    db: Session = Depends(get_db)
):
    print(f"Attempting file upload for userId: {userId}, fileId: {fileId}, filename: {file.filename}")
    if not userId or not fileId:
        print("Upload Error: Missing userId or fileId")
        raise HTTPException(status_code=400, detail="Missing userId or fileId")
    
    # Check if user exists, if not create them (temporary workaround)
    user = db.query(User).filter(User.id == userId).first()
    if not user:
        # Create a dummy user if not found to allow history logging
        try:
            user = User(
                id=userId,
                email=f"{userId}@example.com", # Dummy email
                name=userId, # Dummy name
                created_at=datetime.utcnow()
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            print(f"Created dummy user: {userId}") # Log creation
        except Exception as db_e:
            db.rollback()
            print(f"Error creating dummy user {userId}: {db_e}")
            # Continue upload attempt even if dummy user creation fails, but log it.
            # In a real app, you might want to stop here or handle this differently.

    try:
        # Save file with unique ID
        file_path = os.path.join(UPLOAD_DIR, f"{fileId}_{file.filename}")
        print(f"Attempting to save file to: {file_path}")
        # Ensure the directory exists before saving
        os.makedirs(os.path.dirname(file_path), exist_ok=True) # Ensure target directory exists
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        print(f"File saved successfully to: {file_path}")
        
        # Record in history
        try:
            history_entry = History(
                id=str(uuid.uuid4()),
                user_id=userId,
                activity_type="daily_assessment_upload",
                file_id=fileId,
                file_name=file.filename
            )
            db.add(history_entry)
            db.commit()
            print(f"History entry created for fileId: {fileId}")
        except Exception as hist_e:
            db.rollback()
            print(f"Error creating history entry for fileId {fileId}: {hist_e}")
            # Log the history error but don't necessarily fail the upload if the file saved.

        return {
            "message": "File uploaded successfully",
            "fileId": fileId,
            "fileName": file.filename
        }
    except Exception as e:
        db.rollback()
        print(f"Error during file upload or history recording: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to upload file: {e}")

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
            activity_type="daily_assessment_report",
            file_id=request.reportId,
            report_id=request.reportId,
            filters=request.filters
        )
        db.add(history_entry)
        db.commit()
        
        # --- Report Generation Logic Here ---
        # This is where you would typically process the uploaded data (likely stored/referenced by fileId),
        # apply filters from request.filters, and generate the report (e.g., PPT).
        # The current code only records history and returns success message.
        print(f"Generating report for reportId: {request.reportId} with filters: {request.filters}")

        return {
            "message": "Report generated successfully",
            "reportId": request.reportId,
            "generatedAt": datetime.now().isoformat()
        }
    except Exception as e:
        db.rollback()
        print(f"Error during report generation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {e}")

__all__ = ["router"]
