from sqlalchemy import Column, String, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import datetime

class History(Base):
    __tablename__ = "history"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"))
    activity_type = Column(String)  # e.g., "daily_assessment", "impact_assessment"
    file_id = Column(String)
    file_name = Column(String)
    report_id = Column(String, nullable=True)
    filters = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship with User
    user = relationship("User", back_populates="history")
