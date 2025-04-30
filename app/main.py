import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.api import api_router
from app.core.config import get_settings

# Configure structured logging
logger = structlog.get_logger()

# Create FastAPI app
app = FastAPI(
    title=get_settings().PROJECT_NAME,
    openapi_url=f"{get_settings().API_V1_STR}/openapi.json",
    docs_url="/docs",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix=get_settings().API_V1_STR)


@app.get("/")
async def root():
    """Root endpoint for health check."""
    return {
        "status": "ok",
        "message": "Transcript API is running",
        "docs_url": "/docs",
    } 