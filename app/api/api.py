from fastapi import APIRouter

from app.api.endpoints import health, transcripts, youtube

api_router = APIRouter()

api_router.include_router(
    transcripts.router,
    prefix="/transcript",
    tags=["transcripts"],
)

api_router.include_router(
    health.router,
    prefix="/health",
    tags=["health"],
)

api_router.include_router(
    youtube.router,
    prefix="/youtube",
    tags=["youtube"],
) 