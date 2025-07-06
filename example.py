from youtube_transcript_api import YouTubeTranscriptApi
import sys
import re

def extract_video_id(url_or_id):
    """Extract video ID from YouTube URL or return as is if already an ID."""
    # Patterns to match different YouTube URL formats
    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',  # Standard and embedded URLs
        r'(?:embed\/|v\/|youtu.be\/)([0-9A-Za-z_-]{11})',  # Short URLs
        r'(?:watch\?v=)([0-9A-Za-z_-]{11})'  # Standard watch URLs
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url_or_id)
        if match:
            return match.group(1)
    
    # If no pattern matches, assume it's already a video ID
    return url_or_id

def download_transcript(video_url_or_id, language='en'):
    try:
        # Extract video ID from URL if needed
        video_id = extract_video_id(video_url_or_id)
        
        # Fetch transcript with fallback options
        try:
            # Try to get the requested language directly
            transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=[language])
        except Exception:
            # If direct language not available, try to get auto-generated and translate
            try:
                transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
                # Try to find a transcript that can be translated to the target language
                for transcript_item in transcript_list:
                    if transcript_item.is_translatable:
                        translated_transcript = transcript_item.translate(language)
                        transcript = translated_transcript.fetch()
                        break
                else:
                    # If no translatable transcript, get any available transcript
                    available_transcripts = list(transcript_list)
                    if available_transcripts:
                        transcript = available_transcripts[0].fetch()
                        print(f"Note: Using {available_transcripts[0].language} transcript instead of {language}")
                    else:
                        raise Exception("No transcripts available for this video")
            except Exception as e:
                raise Exception(f"No transcripts available: {str(e)}")
        
        # Save transcript to file
        filename = f"{video_id}_{language}_transcript.txt"
        with open(filename, 'w', encoding='utf-8') as f:
            for entry in transcript:
                # Handle both dict and object formats
                if isinstance(entry, dict):
                    start = entry['start']
                    duration = entry.get('duration', 0)
                    text = entry['text']
                else:
                    # Handle object format
                    start = entry.start
                    duration = getattr(entry, 'duration', 0)
                    text = entry.text
                
                end_time = start + duration
                f.write(f"{start:.2f} --> {end_time:.2f}\n")
                f.write(f"{text}\n\n")
        
        print(f"Transcript saved to {filename}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python download_transcript.py <YouTube Video ID or URL> [language code]")
    else:
        video_input = sys.argv[1]
        language = sys.argv[2] if len(sys.argv) >= 3 else 'en'
        download_transcript(video_input, language)


download_transcript("https://www.youtube.com/watch?v=hTfprtjjKuE", "en")  # Example with URL