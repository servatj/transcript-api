import re
from typing import Optional, List

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import JSONFormatter

from app.providers.base import BaseProvider, RawCaptions, Segment
from app.models.api import ChannelVideoInfo


class YouTubeProvider(BaseProvider):
    """Provider implementation for YouTube videos."""

    VIDEO_ID_PATTERNS = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',  # Standard and embedded URLs
        r'(?:embed\/|v\/|youtu.be\/)([0-9A-Za-z_-]{11})',  # Short URLs
        r'(?:watch\?v=)([0-9A-Za-z_-]{11})'  # Standard watch URLs
    ]
    
    CHANNEL_ID_PATTERNS = [
        r'(?:youtube\.com\/channel\/)([A-Za-z0-9_-]+)',  # Channel ID format
        r'(?:youtube\.com\/@)([A-Za-z0-9_-]+)',  # Handle format
        r'(?:youtube\.com\/c\/)([A-Za-z0-9_-]+)',  # Custom channel format
        r'(?:youtube\.com\/user\/)([A-Za-z0-9_-]+)',  # User format
    ]

    async def extract_video_id(self, url: str) -> str:
        """Extract video ID from YouTube URL.
        
        Args:
            url: The YouTube URL in various possible formats
            
        Returns:
            The extracted video ID
            
        Raises:
            ValueError: If the URL is invalid or no video ID found
        """
        for pattern in self.VIDEO_ID_PATTERNS:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        raise ValueError(f"Invalid YouTube URL: {url}")

    async def download_captions(self, video_id: str) -> Optional[RawCaptions]:
        """Download captions from YouTube video.
        
        Args:
            video_id: The YouTube video ID
            
        Returns:
            The captions data if available, None if no captions found
            
        Raises:
            RuntimeError: If caption download fails
        """
        try:
            # Add some delay to avoid rate limiting
            import time
            time.sleep(0.5)
            
            # Try to get English transcript directly first
            try:
                transcript_data = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])
            except Exception:
                # If direct English not available, try more comprehensive approach
                try:
                    transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
                    
                    # Try to find a transcript that can be translated to English
                    for transcript_item in transcript_list:
                        if transcript_item.is_translatable:
                            translated_transcript = transcript_item.translate('en')
                            transcript_data = translated_transcript.fetch()
                            break
                    else:
                        # If no translatable transcript, get any available transcript
                        available_transcripts = list(transcript_list)
                        if available_transcripts:
                            transcript_data = available_transcripts[0].fetch()
                        else:
                            return None
                except Exception:
                    return None
            
            # Convert to segments - handle both dict and object formats
            segments = []
            for entry in transcript_data:
                # Handle both dict and object formats
                if isinstance(entry, dict):
                    start = float(entry['start'])
                    duration = float(entry.get('duration', 0))
                    text = entry['text']
                else:
                    # Handle object format
                    start = float(entry.start)
                    duration = float(getattr(entry, 'duration', 0))
                    text = entry.text
                
                end_time = start + duration
                segments.append(Segment(
                    start=start,
                    end=end_time,
                    text=text
                ))
            
            # Create full text
            full_text = " ".join(seg.text for seg in segments)
            
            return RawCaptions(
                full_text=full_text,
                segments=segments
            )

        except Exception as e:
            # For XML parsing errors and other transcript issues, return None instead of raising
            error_msg = str(e).lower()
            if any(phrase in error_msg for phrase in [
                "no element found",
                "xml.etree.elementtree.parseerror", 
                "subtitles are disabled",
                "could not retrieve a transcript",
                "transcript not available"
            ]):
                return None
            # For other unexpected errors, still raise
            raise RuntimeError(f"Failed to download captions: {str(e)}")


    async def extract_channel_id(self, url: str) -> str:
        """Extract channel ID from YouTube channel URL.
        
        Args:
            url: The YouTube channel URL in various possible formats
            
        Returns:
            The extracted channel ID
            
        Raises:
            ValueError: If the URL is invalid or no channel ID found
        """
        for pattern in self.CHANNEL_ID_PATTERNS:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        raise ValueError(f"Invalid YouTube channel URL: {url}")

    async def get_channel_videos(self, channel_url: str, limit: Optional[int] = 50) -> List[ChannelVideoInfo]:
        """Get list of videos from a YouTube channel.
        
        Args:
            channel_url: The YouTube channel URL
            limit: Maximum number of videos to return (default: 50)
            
        Returns:
            List of ChannelVideoInfo objects containing video information
            
        Raises:
            ValueError: If the channel URL is invalid
            RuntimeError: If video extraction fails
        """
        try:
            # Extract channel ID for validation
            channel_id = await self.extract_channel_id(channel_url)
            
            from yt_dlp import YoutubeDL
            
            # Ensure we're getting the videos tab specifically
            if '/videos' not in channel_url:
                if channel_url.endswith('/'):
                    videos_url = f"{channel_url}videos"
                else:
                    videos_url = f"{channel_url}/videos"
            else:
                videos_url = channel_url
            
            # Configure yt-dlp to extract video info only
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': True,  # Get basic info without downloading
                'playlistend': limit,
                'ignoreerrors': True,
                'playlistreverse': False,  # Get latest videos first
            }
            
            with YoutubeDL(ydl_opts) as ydl:
                # Extract channel videos
                info = ydl.extract_info(videos_url, download=False)
                
                if not info or 'entries' not in info:
                    return []
                
                videos = []
                for entry in info['entries']:
                    if not entry:  # Skip None entries
                        continue
                        
                    video_info = ChannelVideoInfo(
                        video_id=entry.get('id', ''),
                        title=entry.get('title', ''),
                        description=entry.get('description'),
                        upload_date=entry.get('upload_date'),
                        duration=entry.get('duration'),
                        view_count=entry.get('view_count'),
                        url=entry.get('webpage_url', f"https://www.youtube.com/watch?v={entry.get('id', '')}")
                    )
                    videos.append(video_info)
                
                return videos[:limit] if limit else videos

        except Exception as e:
            raise RuntimeError(f"Failed to get channel videos: {str(e)}")