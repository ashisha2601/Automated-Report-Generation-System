from .auth import router
from .daily_assessment import router as daily_assessment_router
from .impact_assessment import router as impact_assessment_router
from .history import router as history_router

__all__ = ["router", "daily_assessment_router", "impact_assessment_router", "history_router"]
