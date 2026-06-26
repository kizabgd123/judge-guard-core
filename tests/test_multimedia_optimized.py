import pytest
from unittest.mock import MagicMock, patch
import sys
import os

# Add project root to sys.path
sys.path.append(os.getcwd())

from src.kaggle_stream.multimedia import MultimediaManager

def test_multimedia_lazy_session():
    # Ensure requests is NOT in sys.modules yet (if possible, though it might be from other tests)
    # Instead, we check if _session is None initially
    manager = MultimediaManager(hf_token="test_token")
    assert manager._session is None

    # Access session property, which should trigger import and initialization
    with patch("requests.Session") as mock_session_cls:
        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session

        session = manager.session
        assert session == mock_session
        assert manager._session == mock_session
        mock_session_cls.assert_called_once()

def test_multimedia_caching_thread_safety():
    manager = MultimediaManager(hf_token="test_token")

    # Mock session.post
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = b"fake_audio_content"

    with patch("requests.Session") as mock_session_cls:
        manager._session = mock_session_cls.return_value
        manager._session.post.return_value = mock_response

        # First call
        path1 = manager.generate_audio("Hello", "hello1.mp3")
        assert path1 == "hello1.mp3"
        assert manager._audio_cache["Hello"] == b"fake_audio_content"

        # Second call (should hit cache)
        manager._session.post.reset_mock()
        path2 = manager.generate_audio("Hello", "hello2.mp3")
        assert path2 == "hello2.mp3"
        manager._session.post.assert_not_called()

        # Verify file content
        with open("hello2.mp3", "rb") as f:
            assert f.read() == b"fake_audio_content"

        # Cleanup
        if os.path.exists("hello1.mp3"): os.remove("hello1.mp3")
        if os.path.exists("hello2.mp3"): os.remove("hello2.mp3")

if __name__ == "__main__":
    pytest.main([__file__])
