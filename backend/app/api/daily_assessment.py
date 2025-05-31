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
from app.report_generator.da_analysis import DailyAssessmentAnalyzer
from fastapi.responses import FileResponse

router = APIRouter()

# Create upload directory if it doesn't exist
UPLOAD_DIR = "uploads/daily_assessment"
os.makedirs(UPLOAD_DIR, exist_ok=True)

class ReportRequest(BaseModel):
    userId: str
    filters: Dict[str, List[str]]
    reportId: str
    fileId: str

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...), 
    userId: str = Form(None), 
    fileId: str = Form(None),
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

        # Find the uploaded file based on fileId and userId
        file_entry = db.query(History).filter(
            History.user_id == request.userId,
            History.file_id == request.fileId,
            History.activity_type == "daily_assessment_upload"
        ).first()

        if not file_entry:
            raise HTTPException(status_code=404, detail="Uploaded file not found for this user.")

        # Construct the path to the uploaded file
        uploaded_file_path = os.path.join(UPLOAD_DIR, f"{request.fileId}_{file_entry.file_name}")

        if not os.path.exists(uploaded_file_path):
             # This might happen if the file was deleted or upload failed silently earlier
            raise HTTPException(status_code=404, detail="Uploaded file not found on server.")

        # Initialize the analyzer with the uploaded file path
        analyzer = DailyAssessmentAnalyzer(uploaded_file_path)

        # Generate the report, passing the reportId and filters
        report_path = analyzer.generate_report(request.reportId, request.filters) # Pass report_id and filters

        # Record in history
        history_entry = History(
            id=str(uuid.uuid4()),
            user_id=request.userId,
            activity_type="daily_assessment_report",
            file_id=request.fileId, # Associate report with the uploaded file
            report_id=request.reportId,
            filters=request.filters,
            file_name=file_entry.file_name # Store the name of the file that was analyzed
        )
        db.add(history_entry)
        db.commit()

        return {
            "message": "Report generated successfully",
            "reportId": request.reportId,
            "reportPath": report_path, # Return the generated path
            "generatedAt": datetime.now().isoformat()
        }
    except Exception as e:
        db.rollback()
        print(f"Error during report generation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {e}")

# Add GET endpoint to download the report
@router.get("/report/{report_id}")
async def download_report(report_id: str, db: Session = Depends(get_db)):
    try:
        # Optional: Check if the report exists in history before serving (for security/validation)
        report_history_entry = db.query(History).filter(
            History.report_id == report_id,
            History.activity_type == "daily_assessment_report"
            # Add user_id check here if you want to restrict downloads to the user who generated the report
            # History.user_id == current_user.id
        ).first()

        if not report_history_entry:
            raise HTTPException(status_code=404, detail="Report history not found.")

        # Construct the expected path of the report file
        report_file_path = os.path.join("reports", "daily_assessment", f"{report_id}.pptx")

        # Check if the file actually exists on the server
        if not os.path.exists(report_file_path):
            # This could happen if generation failed partially or file was deleted manually
            raise HTTPException(status_code=404, detail="Report file not found on server.")

        # Return the file as a FileResponse
        return FileResponse(
            path=report_file_path,
            media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            filename=f"daily_assessment_report_{report_id}.pptx" # Suggest a filename for download
        )

    except Exception as e:
        print(f"Error during report download: {e}")
        raise HTTPException(status_code=500, detail=str(e))

__all__ = ["router"]
