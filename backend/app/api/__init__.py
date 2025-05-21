from .auth import router as auth_router
from .daily_assessment import router as daily_assessment_router
from .impact_assessment import router as impact_assessment_router
from .history import router as history_router

__all__ = ["auth_router", "daily_assessment_router", "impact_assessment_router", "history_router"]
