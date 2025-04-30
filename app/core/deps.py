import asyncio
from typing import AsyncGenerator, Dict, Optional

import structlog
import redis.asyncio as redis
from redis.exceptions import ConnectionError as RedisConnectionError
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import APIKeyHeader

from app.core.config import Settings, get_settings

logger = structlog.get_logger()
api_key_header = APIKeyHeader(name=get_settings().API_KEY_NAME)


class MockRedis:
    """A mock Redis implementation for when Redis is not available."""
    
    def __init__(self):
        self.storage: Dict[str, str] = {}
        logger.warning("Using MockRedis - data will not persist between app restarts")
    
    async def get(self, key: str) -> Optional[str]:
        return self.storage.get(key)
    
    async def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        self.storage[key] = value
        return True
    
    async def incr(self, key: str) -> int:
        if key not in self.storage:
            self.storage[key] = "0"
        self.storage[key] = str(int(self.storage[key]) + 1)
        return int(self.storage[key])
    
    async def expire(self, key: str, seconds: int) -> bool:
        # We don't implement actual expiry in the mock
        return True
    
    def pipeline(self):
        return MockRedisPipeline(self)
    
    async def close(self):
        pass


class MockRedisPipeline:
    """A mock Redis pipeline implementation."""
    
    def __init__(self, mock_redis: MockRedis):
        self.mock_redis = mock_redis
        self.commands = []
    
    def incr(self, key: str):
        self.commands.append(("incr", key))
        return self
    
    def expire(self, key: str, seconds: int):
        self.commands.append(("expire", key, seconds))
        return self
    
    async def execute(self):
        results = []
        for cmd in self.commands:
            if cmd[0] == "incr":
                results.append(await self.mock_redis.incr(cmd[1]))
            elif cmd[0] == "expire":
                results.append(await self.mock_redis.expire(cmd[1], cmd[2]))
        self.commands = []
        return results


async def get_redis() -> AsyncGenerator[redis.Redis, None]:
    """Get Redis connection or a mock if Redis is not available."""
    settings = get_settings()
    
    try:
        redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD,
            decode_responses=True
        )
        
        # Test the connection
        await redis_client.ping()
        logger.info("Connected to Redis successfully")
        
        try:
            yield redis_client
        finally:
            await redis_client.close()
    
    except (RedisConnectionError) as e:
        logger.warning(f"Redis connection failed: {str(e)}. Using MockRedis instead")
        mock_redis = MockRedis()
        yield mock_redis


async def verify_api_key(
    api_key: str = Depends(api_key_header),
    settings: Settings = Depends(get_settings)
) -> None:
    """Verify the API key."""
    if api_key != settings.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )


async def check_rate_limit(
    request: Request,
    redis_client: redis.Redis = Depends(get_redis),
    settings: Settings = Depends(get_settings)
) -> None:
    """Check rate limits for the provider."""
    provider = request.path_params.get("provider", "default")
    key = f"rate_limit:{provider}:{request.client.host}"
    
    try:
        # Get current request count
        count = await redis_client.get(key)
        count = int(count) if count else 0
        
        # Check if limit exceeded
        max_requests = settings.RATE_LIMIT_MAX_REQUESTS.get(provider, 100)
        if count >= max_requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded for provider {provider}"
            )
        
        # Increment counter and set expiry if not exists
        pipe = redis_client.pipeline()
        pipe.incr(key)
        pipe.expire(key, settings.RATE_LIMIT_WINDOW)
        await pipe.execute()
    
    except (RedisConnectionError) as e:
        logger.error(f"Redis error in rate limiter: {str(e)}")
        # Continue without rate limiting if Redis is not available
        pass
    except Exception as e:
        logger.error(f"Unexpected error in rate limiter: {str(e)}")
        # Continue without rate limiting for unexpected errors 