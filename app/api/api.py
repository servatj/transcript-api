from fastapi import APIRouter

from app.api.endpoints import health, transcripts

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

# Add additional endpoint routers here
# Example:
# api_router.include_router(
#     health.router,
#     prefix="/health",
#     tags=["health"],
# ) 