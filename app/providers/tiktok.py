import re
from typing import Optional

import yt_dlp

from app.providers.base import BaseProvider, RawCaptions, Segment


class TikTokProvider(BaseProvider):
    """Provider implementation for TikTok videos."""

    VIDEO_ID_PATTERN = r"tiktok\.com\/@[\w\.]+\/video\/(\d+)"

    async def extract_video_id(self, url: str) -> str:
        """Extract video ID from TikTok URL."""
        match = re.search(self.VIDEO_ID_PATTERN, url)
        if not match:
            raise ValueError(f"Invalid TikTok URL: {url}")
        return match.group(1)

    async def download_captions(self, video_id: str) -> Optional[RawCaptions]:
        """Download captions from TikTok video."""
        try:
            # Construct video URL
            video_url = f"https://www.tiktok.com/video/{video_id}"
            
            # Extract info with yt-dlp
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'writesubtitles': True,
                'writeautomaticsub': True,
                'skip_download': True,
                'subtitleslangs': ['en'],
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=False)
                
                # Check if subtitles are available
                if info.get('subtitles') and 'en' in info['subtitles']:
                    # Parse subtitles
                    subtitles = info['subtitles']['en'][0]['data']
                    segments = []
                    full_text_parts = []
                    
                    # Process subtitle entries
                    for entry in subtitles:
                        if 'start' in entry and 'end' in entry and 'text' in entry:
                            start = float(entry['start'])
                            end = float(entry['end'])
                            text = entry['text']
                            
                            if text:
                                segments.append(Segment(start=start, end=end, text=text))
                                full_text_parts.append(text)
                    
                    if segments:
                        return RawCaptions(
                            full_text=" ".join(full_text_parts),
                            segments=segments
                        )
            
            return None

        except Exception as e:
            raise RuntimeError(f"Failed to download captions: {str(e)}")

    async def download_audio(self, video_id: str) -> bytes:
        """Download audio from TikTok video."""
        try:
            video_url = f"https://www.tiktok.com/video/{video_id}"
            
            # Configure yt-dlp to download audio only
            ydl_opts = {
                'format': 'bestaudio/best',
                'quiet': True,
                'no_warnings': True,
                'outtmpl': '-',  # Output to stdout
                'logtostderr': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Download to memory
                audio_data = ydl.download([video_url])
                return audio_data

        except Exception as e:
            raise RuntimeError(f"Failed to download audio: {str(e)}") 