import unittest
from unittest.mock import MagicMock, patch
from src.kaggle_stream.multimedia import MultimediaManager

class TestMultimediaManager(unittest.TestCase):
    def setUp(self):
        self.manager = MultimediaManager(hf_token="dummy")

    def test_lazy_initialization(self):
        """Verify that session and logger are NOT initialized in __init__."""
        self.assertIsNone(self.manager._session)
        self.assertIsNone(self.manager._logger)

    def test_lazy_logger(self):
        """Verify logger is initialized on first access."""
        logger = self.manager.logger
        self.assertIsNotNone(self.manager._logger)
        self.assertEqual(logger.name, "src.kaggle_stream.multimedia")

    @patch("requests.Session")
    def test_lazy_session(self, mock_session_class):
        """Verify session is initialized on first access and uses the correct headers."""
        mock_session_instance = MagicMock()
        mock_session_class.return_value = mock_session_instance

        session = self.manager.session
        self.assertIsNotNone(self.manager._session)
        mock_session_class.assert_called_once()
        mock_session_instance.headers.update.assert_called_with({"Authorization": "Bearer dummy"})

    @patch("requests.Session.post")
    def test_generate_audio_mock(self, mock_post):
        """Verify generate_audio uses the session and handles mock mode (token='dummy')."""
        # When token is 'dummy', it should return None and log mock message
        result = self.manager.generate_audio("Hello")
        self.assertIsNone(result)
        mock_post.assert_not_called()

    @patch("requests.Session.post")
    def test_generate_audio_real(self, mock_post):
        """Verify generate_audio makes a real API call when token is present."""
        manager = MultimediaManager(hf_token="real_token")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"audio_data"
        mock_post.return_value = mock_response

        with patch("builtins.open", unittest.mock.mock_open()) as mocked_file:
            result = manager.generate_audio("Hello", "test.mp3")

            self.assertEqual(result, "test.mp3")
            mocked_file.assert_called_once_with("test.mp3", "wb")
            mocked_file().write.assert_called_once_with(b"audio_data")

            # Check cache
            self.assertEqual(manager._audio_cache["Hello"], b"audio_data")

    def test_cache_reuse(self):
        """Verify that content is reused from cache without calling the API."""
        self.manager._audio_cache["Hello"] = b"cached_data"

        with patch("builtins.open", unittest.mock.mock_open()) as mocked_file:
            result = self.manager.generate_audio("Hello", "test.mp3")
            self.assertEqual(result, "test.mp3")
            mocked_file().write.assert_called_once_with(b"cached_data")

if __name__ == "__main__":
    unittest.main()
