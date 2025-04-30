from fastapi import APIRouter

router = APIRouter()


@router.get("")
async def get_health():
    """Get API health status."""
    return {
        "status": "healthy",
        "version": "1.0.0"
    }


@router.get("/ping")
async def ping():
    """Simple ping endpoint for lightweight health checks."""
    return {"ping": "pong"} 