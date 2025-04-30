from enum import Enum
from typing import List

from pydantic import BaseModel, HttpUrl


class Provider(str, Enum):
    """Supported video providers."""
    YOUTUBE = "youtube"
    TIKTOK = "tiktok"
    REELS = "reels"


class TranscriptSegment(BaseModel):
    """A segment of transcribed text with timing information."""
    start: float
    end: float
    text: str


class TranscriptRequest(BaseModel):
    """Request model for transcript endpoint."""
    provider: Provider
    video_url: HttpUrl

    class Config:
        json_schema_extra = {
            "example": {
                "provider": "youtube",
                "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
            }
        }


class TranscriptResponse(BaseModel):
    """Response model for transcript endpoint."""
    video_id: str
    provider: Provider
    transcript: str
    segments: List[TranscriptSegment]

    class Config:
        json_schema_extra = {
            "example": {
                "video_id": "dQw4w9WgXcQ",
                "provider": "youtube",
                "transcript": "Never gonna give you up...",
                "segments": [
                    {
                        "start": 0.0,
                        "end": 3.2,
                        "text": "Never gonna give you up"
                    }
                ]
            }
        }


class ErrorResponse(BaseModel):
    """Error response model."""
    detail: str 