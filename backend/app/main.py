from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import router, daily_assessment_router, impact_assessment_router, history_router
from app.core.database import create_tables

app = FastAPI(title="Automated Report Generation System")

# Create database tables on startup
@app.on_event("startup")
async def startup_event():
    create_tables()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(router, prefix="/api", tags=["auth"])
app.include_router(daily_assessment_router, prefix="/api/daily-assessment", tags=["daily_assessment"])
app.include_router(impact_assessment_router, prefix="/api/impact-assessment", tags=["impact_assessment"])
app.include_router(history_router, prefix="/api/history", tags=["history"])

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Welcome to Automated Report Generation System API",
        "docs_url": "/docs",
        "redoc_url": "/redoc"
    }

# Serve static files
from fastapi.staticfiles import StaticFiles

app.mount("/static", StaticFiles(directory="../Frontend"), name="static")