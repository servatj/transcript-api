import re
from typing import Optional

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import JSONFormatter

from app.providers.base import BaseProvider, RawCaptions, Segment


class YouTubeProvider(BaseProvider):
    """Provider implementation for YouTube videos."""

    VIDEO_ID_PATTERNS = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',  # Standard and embedded URLs
        r'(?:embed\/|v\/|youtu.be\/)([0-9A-Za-z_-]{11})',  # Short URLs
        r'(?:watch\?v=)([0-9A-Za-z_-]{11})'  # Standard watch URLs
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
            # Get available transcripts
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            
            # Try to get English transcript, fallback to auto-translated
            try:
                transcript = transcript_list.find_transcript(['en'])
            except:
                try:
                    transcript = transcript_list.find_manually_created_transcript()
                    transcript = transcript.translate('en')
                except:
                    try:
                        transcript = transcript_list.find_generated_transcript()
                        transcript = transcript.translate('en')
                    except:
                        return None

            # Get transcript data
            transcript_data = transcript.fetch()
            
            # Convert to segments
            segments = [
                Segment(
                    start=float(entry['start']),
                    end=float(entry['start'] + entry['duration']),
                    text=entry['text']
                )
                for entry in transcript_data
            ]
            
            # Create full text
            full_text = " ".join(seg.text for seg in segments)
            
            return RawCaptions(
                full_text=full_text,
                segments=segments
            )

        except Exception as e:
            raise RuntimeError(f"Failed to download captions: {str(e)}")

    async def download_audio(self, video_id: str) -> bytes:
        """Download audio from YouTube video.
        
        Args:
            video_id: The YouTube video ID
            
        Returns:
            The audio data as bytes
            
        Raises:
            RuntimeError: If audio download fails
        """
        try:
            from yt_dlp import YoutubeDL
            
            # Configure yt-dlp to download audio only
            ydl_opts = {
                'format': 'bestaudio/best',
                'quiet': True,
                'no_warnings': True,
                'outtmpl': '-',  # Output to stdout
                'logtostderr': True,
            }
            
            with YoutubeDL(ydl_opts) as ydl:
                # Download to memory
                url = f"https://www.youtube.com/watch?v={video_id}"
                audio_data = ydl.download([url])
                return audio_data

        except Exception as e:
            raise RuntimeError(f"Failed to download audio: {str(e)}")