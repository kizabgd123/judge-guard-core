import pytest
from unittest.mock import MagicMock, patch
from src.kaggle_stream.multimedia import MultimediaManager

def test_multimedia_manager_lazy_session():
    # Ensure requests is NOT imported yet in this process
    import sys
    if 'requests' in sys.modules:
        # This is tricky in a test runner, but we can check if _session is None
        pass

    manager = MultimediaManager(hf_token="dummy_token")
    assert manager._session is None

    # Mock requests.Session
    with patch('requests.Session') as mock_session_cls:
        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session

        # Access session property
        session = manager.session
        assert manager._session is not None
        mock_session_cls.assert_called_once()
        assert session == mock_session

def test_generate_audio_uses_session():
    manager = MultimediaManager(hf_token="valid_token")

    with patch('requests.Session') as mock_session_cls:
        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"fake audio content"
        mock_session.post.return_value = mock_response

        with patch('builtins.open', MagicMock()):
            path = manager.generate_audio("Hello world", "test.mp3")
            assert path == "test.mp3"
            mock_session.post.assert_called_once()

            # Test cache
            path2 = manager.generate_audio("Hello world", "test2.mp3")
            assert path2 == "test2.mp3"
            # Should not call post again
            mock_session.post.assert_called_once()

def test_kaggle_agent_lazy_executor():
    from src.kaggle_stream.kaggle_agent import KaggleAgent
    agent = KaggleAgent(name="TestAgent")
    assert agent._executor is None

    # Access executor
    executor = agent.executor
    assert agent._executor is not None
    assert executor is not None
    agent.close()
