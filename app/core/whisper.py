import io
import tempfile
from typing import List, Optional

import structlog
import openai
from pydub import AudioSegment

from app.core.config import get_settings
from app.providers.base import RawCaptions, Segment

logger = structlog.get_logger()


class WhisperService:
    """Service for transcribing audio using OpenAI's Whisper model."""
    
    def __init__(self):
        """Initialize the Whisper service."""
        settings = get_settings()
        self.api_key = settings.OPENAI_API_KEY
        self.is_available = self.api_key is not None
        
        if self.is_available:
            # Configure OpenAI client
            openai.api_key = self.api_key
            logger.info("WhisperService initialized with API key")
        else:
            logger.warning("OPENAI_API_KEY is not set, Whisper transcription will not be available")
    
    async def transcribe_audio(self, audio_data: bytes) -> Optional[RawCaptions]:
        """Transcribe audio using OpenAI's Whisper model.
        
        Args:
            audio_data: Raw audio bytes
            
        Returns:
            Transcription with segments, or None if the service is not available
            
        Raises:
            RuntimeError: If transcription fails
        """
        if not self.is_available:
            logger.error("Cannot transcribe: OPENAI_API_KEY is not set")
            return None
            
        try:
            # Save audio bytes to a temporary file
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=True) as temp_file:
                # Convert audio to MP3 format
                audio = AudioSegment.from_file(io.BytesIO(audio_data))
                audio.export(temp_file.name, format="mp3")
                
                # Reset file pointer to beginning
                temp_file.seek(0)
                
                # Transcribe with Whisper
                response = openai.Audio.transcribe(
                    model="whisper-1",
                    file=temp_file,
                    response_format="verbose_json",
                    timestamp_granularities=["segment"]
                )
                
                # Process response
                full_text = response.get("text", "")
                segments: List[Segment] = []
                
                for segment in response.get("segments", []):
                    start = segment.get("start", 0)
                    end = segment.get("end", 0)
                    text = segment.get("text", "").strip()
                    
                    if text:
                        segments.append(Segment(
                            start=start,
                            end=end,
                            text=text
                        ))
                
                return RawCaptions(
                    full_text=full_text,
                    segments=segments
                )
                
        except Exception as e:
            logger.exception("Failed to transcribe audio", error=str(e))
            raise RuntimeError(f"Failed to transcribe audio: {str(e)}")
            
            
# Singleton instance
whisper_service = WhisperService() 