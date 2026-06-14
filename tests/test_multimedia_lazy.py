import unittest
from unittest.mock import MagicMock, patch
import os
import sys

# Ensure src is in path
sys.path.append(os.getcwd())

from src.kaggle_stream.multimedia import MultimediaManager

class TestMultimediaManagerLazy(unittest.TestCase):
    def test_lazy_session_initialization(self):
        # Initialize manager - session should be None
        manager = MultimediaManager(hf_token="test_token")
        self.assertIsNone(manager._session)

        # Accessing session property should trigger import and initialization
        with patch('requests.Session') as mock_session_class:
            mock_session_instance = MagicMock()
            mock_session_class.return_value = mock_session_instance

            session = manager.session
            self.assertIsNotNone(session)
            mock_session_class.assert_called_once()

            # Subsequent access should reuse the session
            session2 = manager.session
            self.assertEqual(session, session2)
            mock_session_class.assert_called_once()

    def test_generate_audio_uses_session(self):
        manager = MultimediaManager(hf_token="test_token")

        with patch('requests.Session') as mock_session_class:
            mock_session_instance = MagicMock()
            mock_session_class.return_value = mock_session_instance

            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.content = b"fake audio"
            mock_session_instance.post.return_value = mock_response

            # Clean up if file exists
            if os.path.exists("test_speech.mp3"):
                os.remove("test_speech.mp3")

            path = manager.generate_audio("Hello", "test_speech.mp3")

            self.assertEqual(path, "test_speech.mp3")
            mock_session_instance.post.assert_called_once()
            self.assertTrue(os.path.exists("test_speech.mp3"))

            # Cleanup
            if os.path.exists("test_speech.mp3"):
                os.remove("test_speech.mp3")

    def test_close_shuts_down_session(self):
        manager = MultimediaManager(hf_token="test_token")

        with patch('requests.Session') as mock_session_class:
            mock_session_instance = MagicMock()
            mock_session_class.return_value = mock_session_instance

            # Trigger session init
            _ = manager.session

            manager.close()
            mock_session_instance.close.assert_called_once()

if __name__ == "__main__":
    unittest.main()
