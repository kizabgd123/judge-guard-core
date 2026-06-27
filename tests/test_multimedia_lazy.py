import pytest
from unittest.mock import MagicMock, patch
from src.kaggle_stream.multimedia import MultimediaManager

def test_multimedia_manager_lazy_session():
    # Patch requests.Session to avoid real network calls
    with patch('requests.Session') as mock_session_cls:
        mock_session = mock_session_cls.return_value
        # Initialize manager - session should NOT be initialized now
        manager = MultimediaManager(hf_token="test_token")

        # Verify private field is None
        assert manager._session is None
        assert not mock_session_cls.called

        # Trigger session property
        session = manager.session
        assert session is not None
        assert manager._session is not None
        assert mock_session_cls.called

def test_multimedia_manager_cache_usage():
    manager = MultimediaManager(hf_token="dummy")
    manager._audio_cache["hello"] = b"cached_audio"

    with patch("builtins.open", MagicMock()) as mock_open:
        path = manager.generate_audio("hello", "test.mp3")
        assert path == "test.mp3"
        # Should NOT have initialized session for a cache hit
        assert manager._session is None
