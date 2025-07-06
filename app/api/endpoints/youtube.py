import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from app.core.deps import check_rate_limit, get_redis, verify_api_key
from app.models.api import (
    ErrorResponse, 
    ChannelVideosRequest, 
    ChannelVideosResponse,
    ChannelVideoInfo
)
from app.providers.youtube import YouTubeProvider

# Configure structured logging
logger = structlog.get_logger()

# Create API router
router = APIRouter()

# YouTube provider instance
youtube_provider = YouTubeProvider()

@router.post(
    "/channel/videos",
    response_model=ChannelVideosResponse,
    responses={
        401: {
            "model": ErrorResponse,
            "description": "Invalid or missing API key"
        },
        429: {
            "model": ErrorResponse,
            "description": "Rate limit exceeded"
        },
        400: {
            "model": ErrorResponse,
            "description": "Invalid channel URL"
        },
        500: {
            "model": ErrorResponse,
            "description": "Internal server error"
        },
    },
    dependencies=[Depends(verify_api_key), Depends(check_rate_limit)],
    summary="Get YouTube Channel Videos",
    description="""
    Get a list of videos from a YouTube channel.
    
    The endpoint supports various YouTube channel URL formats:
    - Channel ID: https://www.youtube.com/channel/UC_x5XG1OV2P6uZZ5FSM9Ttw
    - Handle: https://www.youtube.com/@username
    - Custom URL: https://www.youtube.com/c/channelname
    - User URL: https://www.youtube.com/user/username
    
    Results are cached for 1 hour to improve performance.
    Rate limiting is applied per client IP.
    
    Example:
    ```json
    {
        "channel_url": "https://www.youtube.com/channel/UC_x5XG1OV2P6uZZ5FSM9Ttw",
        "limit": 20
    }
    ```
    """,
)
async def get_channel_videos(
    request: ChannelVideosRequest,
    redis_client=Depends(get_redis),
) -> ChannelVideosResponse:
    """Get videos from a YouTube channel.
    
    Args:
        request: The channel videos request containing channel URL and optional limit
        redis_client: Redis client for caching (injected)
        
    Returns:
        The channel videos response containing channel ID and list of videos
        
    Raises:
        HTTPException: If request is invalid or processing fails
    """
    try:
        # Extract channel ID for caching key
        channel_id = await youtube_provider.extract_channel_id(str(request.channel_url))
        
        # Check cache
        cache_key = f"channel_videos:{channel_id}:{request.limit}"
        cached = await redis_client.get(cache_key)
        if cached:
            logger.info(f"Returning cached channel videos for {channel_id}")
            return ChannelVideosResponse.model_validate_json(cached)

        # Get videos from channel
        logger.info(f"Fetching videos from YouTube channel {channel_id}")
        videos = await youtube_provider.get_channel_videos(
            str(request.channel_url), 
            limit=request.limit
        )
        
        # Create response
        response = ChannelVideosResponse(
            channel_id=channel_id,
            videos=videos,
            total_count=len(videos)
        )

        # Cache response for 1 hour
        await redis_client.set(
            cache_key,
            response.model_dump_json(),
            ex=3600  # 1 hour
        )
        
        logger.info(f"Successfully fetched {len(videos)} videos from channel {channel_id}")
        return response

    except ValueError as e:
        logger.warning(f"Invalid channel URL: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.exception("Error processing channel videos request", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )