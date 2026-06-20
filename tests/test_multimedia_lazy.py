import unittest
from unittest.mock import patch, MagicMock
from src.kaggle_stream.multimedia import MultimediaManager

class TestMultimediaLazy(unittest.TestCase):
    def test_lazy_session_initialization(self):
        # Create manager - should NOT have _session initialized yet
        manager = MultimediaManager(hf_token="test_token")
        self.assertIsNone(manager._session)

        # Accessing session should trigger import and initialization
        # We mock requests to avoid actual network/import overhead during test if possible,
        # but here we want to see if it actually works.
        with patch('requests.Session') as mock_session_class:
            mock_session_instance = MagicMock()
            mock_session_class.return_value = mock_session_instance

            session = manager.session
            self.assertIsNotNone(session)
            mock_session_class.assert_called_once()
            self.assertEqual(manager._session, mock_session_instance)

            # Second access should not re-initialize
            session2 = manager.session
            self.assertIs(session, session2)
            mock_session_class.assert_called_once()

    def test_generate_audio_uses_session(self):
        manager = MultimediaManager(hf_token="test_token")

        with patch('requests.Session') as mock_session_class:
            mock_session_instance = MagicMock()
            mock_session_class.return_value = mock_session_instance

            # Mock response
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.content = b"fake audio content"
            mock_session_instance.post.return_value = mock_response

            # Mock open to avoid writing to disk
            with patch('builtins.open', unittest.mock.mock_open()):
                path = manager.generate_audio("Hello", "test.mp3")

            self.assertEqual(path, "test.mp3")
            mock_session_instance.post.assert_called_once()

if __name__ == "__main__":
    unittest.main()
