from enum import Enum
from typing import List, Optional

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


class ChannelVideoInfo(BaseModel):
    """Information about a video in a YouTube channel."""
    video_id: str
    title: str
    description: Optional[str] = None
    upload_date: Optional[str] = None
    duration: Optional[int] = None
    view_count: Optional[int] = None
    url: str

    class Config:
        json_schema_extra = {
            "example": {
                "video_id": "dQw4w9WgXcQ",
                "title": "Rick Astley - Never Gonna Give You Up",
                "description": "The official video for 'Never Gonna Give You Up'",
                "upload_date": "20091025",
                "duration": 212,
                "view_count": 1000000000,
                "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
            }
        }


class ChannelVideosRequest(BaseModel):
    """Request model for channel videos endpoint."""
    channel_url: HttpUrl
    limit: Optional[int] = 50

    class Config:
        json_schema_extra = {
            "example": {
                "channel_url": "https://www.youtube.com/channel/UC_x5XG1OV2P6uZZ5FSM9Ttw",
                "limit": 20
            }
        }


class ChannelVideosResponse(BaseModel):
    """Response model for channel videos endpoint."""
    channel_id: str
    videos: List[ChannelVideoInfo]
    total_count: int

    class Config:
        json_schema_extra = {
            "example": {
                "channel_id": "UC_x5XG1OV2P6uZZ5FSM9Ttw",
                "videos": [
                    {
                        "video_id": "dQw4w9WgXcQ",
                        "title": "Rick Astley - Never Gonna Give You Up",
                        "description": "The official video for 'Never Gonna Give You Up'",
                        "upload_date": "20091025",
                        "duration": 212,
                        "view_count": 1000000000,
                        "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
                    }
                ],
                "total_count": 1
            }
        } 