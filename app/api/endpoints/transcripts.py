import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, List

from app.core.deps import check_rate_limit, get_redis, verify_api_key
from app.models.api import (ErrorResponse, Provider, TranscriptRequest,
                          TranscriptResponse, TranscriptSegment)
from app.providers.tiktok import TikTokProvider
from app.providers.youtube import YouTubeProvider
from app.providers.base import BaseProvider

# Configure structured logging
logger = structlog.get_logger()

# Create API router
router = APIRouter()

# Provider factory
PROVIDERS: Dict[Provider, BaseProvider] = {
    Provider.YOUTUBE: YouTubeProvider(),
    Provider.TIKTOK: TikTokProvider(),
    # Add other providers here
}

EXAMPLE_URLS = {
    Provider.YOUTUBE: "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    Provider.TIKTOK: "https://www.tiktok.com/@username/video/1234567890123456789",
}

@router.post(
    "",
    response_model=TranscriptResponse,
    responses={
        401: {
            "model": ErrorResponse,
            "description": "Invalid or missing API key"
        },
        429: {
            "model": ErrorResponse,
            "description": "Rate limit exceeded"
        },
        404: {
            "model": ErrorResponse,
            "description": "No captions available for this video"
        },
        500: {
            "model": ErrorResponse,
            "description": "Internal server error"
        },
    },
    dependencies=[Depends(verify_api_key), Depends(check_rate_limit)],
    summary="Get Video Transcript",
    description="""
    Get transcript for a video from supported providers (YouTube, TikTok).
    
    The endpoint will:
    1. Try to get native captions in English
    2. If no English captions, try to get captions in other languages and translate to English
    3. If no captions available, return 404 error
    
    Rate limiting is applied per provider and client IP.
    Results are cached for 1 hour.
    
    Example URLs:
    - YouTube: https://www.youtube.com/watch?v=dQw4w9WgXcQ
    - TikTok: https://www.tiktok.com/@username/video/1234567890123456789
    """,
)

async def get_transcript(
    request: TranscriptRequest,
    redis_client=Depends(get_redis),
) -> TranscriptResponse:
    """Get transcript for a video.
    
    Args:
        request: The transcript request containing provider and video URL
        redis_client: Redis client for caching (injected)
        
    Returns:
        The transcript response containing video ID, provider, full text and timed segments
        
    Raises:
        HTTPException: If request is invalid or processing fails
    """
    try:
        # Get provider
        provider = PROVIDERS.get(request.provider)
        if not provider:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported provider: {request.provider}"
            )

        # Extract video ID
        video_id = await provider.extract_video_id(str(request.video_url))
        
        # Check cache
        cache_key = f"transcript:{request.provider}:{video_id}"
        cached = await redis_client.get(cache_key)
        if cached:
            return TranscriptResponse.model_validate_json(cached)

        # Get captions
        captions = await provider.download_captions(video_id)
        
        # Check if captions are available
        if not captions:
            logger.info(f"No captions found for {request.provider} video {video_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No captions available for this video"
            )

        # Create response
        response = TranscriptResponse(
            video_id=video_id,
            provider=request.provider,
            transcript=captions.full_text,
            segments=[
                TranscriptSegment(
                    start=seg.start,
                    end=seg.end,
                    text=seg.text
                )
                for seg in captions.segments
            ]
        )

        # Cache response
        await redis_client.set(
            cache_key,
            response.model_dump_json(),
            ex=3600  # 1 hour
        )

        return response

    except HTTPException:
        # Re-raise HTTPExceptions (like 404 Not Found) without modification
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.exception("Error processing transcript request", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        ) 