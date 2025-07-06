from abc import ABC, abstractmethod
from typing import List, Optional

from pydantic import BaseModel


class Segment(BaseModel):
    """A segment of text with start and end timestamps."""
    start: float
    end: float
    text: str


class RawCaptions(BaseModel):
    """Raw captions data with full text and timed segments."""
    full_text: str
    segments: List[Segment]


class BaseProvider(ABC):
    """Base class for video providers (TikTok, YouTube, etc.)."""

    @abstractmethod
    async def extract_video_id(self, url: str) -> str:
        """Extract video ID from URL.
        
        Args:
            url: The video URL
            
        Returns:
            The extracted video ID
            
        Raises:
            ValueError: If the URL is invalid
        """
        pass

    @abstractmethod
    async def download_captions(self, video_id: str) -> Optional[RawCaptions]:
        """Download captions for a video.
        
        Args:
            video_id: The video ID
            
        Returns:
            The captions data if available, None otherwise
            
        Raises:
            RuntimeError: If caption download fails
        """
        pass

 