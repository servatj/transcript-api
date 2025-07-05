import pytest
from unittest.mock import MagicMock, patch
from app.providers.youtube import YouTubeProvider
from app.models.api import ChannelVideoInfo


class TestYouTubeProvider:
    """Test suite for YouTube provider functionality."""
    
    @pytest.fixture
    def youtube_provider(self):
        """Create a YouTubeProvider instance for testing."""
        return YouTubeProvider()

    @pytest.mark.asyncio
    async def test_extract_video_id_standard_url(self, youtube_provider):
        """Test extracting video ID from standard YouTube URL."""
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        video_id = await youtube_provider.extract_video_id(url)
        assert video_id == "dQw4w9WgXcQ"

    @pytest.mark.asyncio
    async def test_extract_video_id_short_url(self, youtube_provider):
        """Test extracting video ID from short YouTube URL."""
        url = "https://youtu.be/dQw4w9WgXcQ"
        video_id = await youtube_provider.extract_video_id(url)
        assert video_id == "dQw4w9WgXcQ"

    @pytest.mark.asyncio
    async def test_extract_video_id_embed_url(self, youtube_provider):
        """Test extracting video ID from embed YouTube URL."""
        url = "https://www.youtube.com/embed/dQw4w9WgXcQ"
        video_id = await youtube_provider.extract_video_id(url)
        assert video_id == "dQw4w9WgXcQ"

    @pytest.mark.asyncio
    async def test_extract_video_id_invalid_url(self, youtube_provider):
        """Test that invalid URLs raise ValueError."""
        with pytest.raises(ValueError, match="Invalid YouTube URL"):
            await youtube_provider.extract_video_id("https://example.com/invalid")

    @pytest.mark.asyncio
    async def test_extract_channel_id_from_url(self, youtube_provider):
        """Test extracting channel ID from various YouTube channel URL formats."""
        # Test different channel URL formats
        test_cases = [
            ("https://www.youtube.com/channel/UC_x5XG1OV2P6uZZ5FSM9Ttw", "UC_x5XG1OV2P6uZZ5FSM9Ttw"),
            ("https://www.youtube.com/@username", "@username"),
            ("https://www.youtube.com/c/channelname", "channelname"),
            ("https://www.youtube.com/user/username", "username"),
        ]
        
        for url, expected_id in test_cases:
            channel_id = await youtube_provider.extract_channel_id(url)
            assert channel_id == expected_id

    @pytest.mark.asyncio
    async def test_extract_channel_id_invalid_url(self, youtube_provider):
        """Test that invalid channel URLs raise ValueError."""
        with pytest.raises(ValueError, match="Invalid YouTube channel URL"):
            await youtube_provider.extract_channel_id("https://example.com/invalid")

    @pytest.mark.asyncio
    @patch('app.providers.youtube.YoutubeDL')
    async def test_get_channel_videos_success(self, mock_ydl_class, youtube_provider):
        """Test successful retrieval of channel videos."""
        # Mock yt-dlp response
        mock_ydl = MagicMock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl
        mock_ydl.extract_info.return_value = {
            'entries': [
                {
                    'id': 'video1',
                    'title': 'Test Video 1',
                    'description': 'Test description 1',
                    'upload_date': '20231201',
                    'duration': 120,
                    'view_count': 1000,
                    'webpage_url': 'https://www.youtube.com/watch?v=video1'
                },
                {
                    'id': 'video2',
                    'title': 'Test Video 2',
                    'description': 'Test description 2',
                    'upload_date': '20231202',
                    'duration': 180,
                    'view_count': 2000,
                    'webpage_url': 'https://www.youtube.com/watch?v=video2'
                }
            ]
        }

        channel_url = "https://www.youtube.com/channel/UC_x5XG1OV2P6uZZ5FSM9Ttw"
        videos = await youtube_provider.get_channel_videos(channel_url)
        
        assert len(videos) == 2
        assert videos[0].video_id == "video1"
        assert videos[0].title == "Test Video 1"
        assert videos[0].description == "Test description 1"
        assert videos[0].upload_date == "20231201"
        assert videos[0].duration == 120
        assert videos[0].view_count == 1000
        assert videos[0].url == "https://www.youtube.com/watch?v=video1"

    @pytest.mark.asyncio
    @patch('app.providers.youtube.YoutubeDL')
    async def test_get_channel_videos_with_limit(self, mock_ydl_class, youtube_provider):
        """Test retrieval of channel videos with limit."""
        # Mock yt-dlp response with more videos than limit
        mock_ydl = MagicMock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl
        mock_ydl.extract_info.return_value = {
            'entries': [
                {
                    'id': f'video{i}',
                    'title': f'Test Video {i}',
                    'description': f'Test description {i}',
                    'upload_date': '20231201',
                    'duration': 120,
                    'view_count': 1000,
                    'webpage_url': f'https://www.youtube.com/watch?v=video{i}'
                }
                for i in range(1, 11)  # 10 videos
            ]
        }

        channel_url = "https://www.youtube.com/channel/UC_x5XG1OV2P6uZZ5FSM9Ttw"
        videos = await youtube_provider.get_channel_videos(channel_url, limit=5)
        
        assert len(videos) == 5
        assert videos[0].video_id == "video1"
        assert videos[4].video_id == "video5"

    @pytest.mark.asyncio
    @patch('app.providers.youtube.YoutubeDL')
    async def test_get_channel_videos_handles_missing_fields(self, mock_ydl_class, youtube_provider):
        """Test that missing fields are handled gracefully."""
        # Mock yt-dlp response with missing fields
        mock_ydl = MagicMock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl
        mock_ydl.extract_info.return_value = {
            'entries': [
                {
                    'id': 'video1',
                    'title': 'Test Video 1',
                    # Missing description, upload_date, duration, view_count
                    'webpage_url': 'https://www.youtube.com/watch?v=video1'
                }
            ]
        }

        channel_url = "https://www.youtube.com/channel/UC_x5XG1OV2P6uZZ5FSM9Ttw"
        videos = await youtube_provider.get_channel_videos(channel_url)
        
        assert len(videos) == 1
        assert videos[0].video_id == "video1"
        assert videos[0].title == "Test Video 1"
        assert videos[0].description is None
        assert videos[0].upload_date is None
        assert videos[0].duration is None
        assert videos[0].view_count is None

    @pytest.mark.asyncio
    @patch('app.providers.youtube.YoutubeDL')
    async def test_get_channel_videos_error_handling(self, mock_ydl_class, youtube_provider):
        """Test error handling when yt-dlp fails."""
        # Mock yt-dlp to raise an exception
        mock_ydl = MagicMock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl
        mock_ydl.extract_info.side_effect = Exception("yt-dlp error")

        channel_url = "https://www.youtube.com/channel/UC_x5XG1OV2P6uZZ5FSM9Ttw"
        
        with pytest.raises(RuntimeError, match="Failed to get channel videos"):
            await youtube_provider.get_channel_videos(channel_url)

    @pytest.mark.asyncio
    async def test_get_channel_videos_invalid_url(self, youtube_provider):
        """Test that invalid channel URLs are handled properly."""
        with pytest.raises(ValueError, match="Invalid YouTube channel URL"):
            await youtube_provider.get_channel_videos("https://example.com/invalid")