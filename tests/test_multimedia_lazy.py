import unittest
from unittest.mock import patch, MagicMock
from src.kaggle_stream.multimedia import MultimediaManager
import os
import sys

class TestMultimediaLazy(unittest.TestCase):
    def test_lazy_session_initialization(self):
        # Initialize manager - session should be None
        manager = MultimediaManager(hf_token="test_token")
        self.assertIsNone(manager._session)

        # Access session property - it should be initialized
        session = manager.session
        self.assertIsNotNone(manager._session)

        # Check if it behaves like a session
        self.assertTrue(hasattr(session, 'post'))
        self.assertEqual(session.headers["Authorization"], "Bearer test_token")

    def test_session_cleanup(self):
        manager = MultimediaManager(hf_token="test_token")
        session = manager.session  # Trigger initialization

        # Mock the session's close method
        with patch.object(session, 'close') as mock_close:
            manager.close()
            mock_close.assert_called_once()
            self.assertIsNone(manager._session)

    def test_mock_mode_avoids_network(self):
        # In mock mode (no token), we still might access session if logic flow leads there
        # but generate methods should skip it.
        manager = MultimediaManager(hf_token=None)
        with patch('os.getenv', return_value=None):
            manager.hf_token = None # Ensure it's None

            # This should NOT trigger session initialization
            audio_path = manager.generate_audio("Hello")
            self.assertIsNone(audio_path)
            self.assertIsNone(manager._session)

    def test_generate_audio_triggers_session(self):
        manager = MultimediaManager(hf_token="test_token")
        self.assertIsNone(manager._session)

        # Accessing session should trigger initialization even if post is mocked
        session = manager.session
        with patch.object(session, 'post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.content = b"fake audio content"
            mock_post.return_value = mock_response

            with patch('builtins.open', unittest.mock.mock_open()):
                manager.generate_audio("Hello", "test.mp3")

            mock_post.assert_called_once()

if __name__ == "__main__":
    unittest.main()
