import unittest
from unittest.mock import patch, MagicMock
from src.kaggle_stream.multimedia import MultimediaManager
import os

class TestMultimediaManager(unittest.TestCase):
    def setUp(self):
        self.manager = MultimediaManager(hf_token="test_token")

    def test_lazy_logger(self):
        # Initial state
        self.assertIsNone(self.manager._logger)
        # Access property
        logger = self.manager.logger
        self.assertIsNotNone(self.manager._logger)
        self.assertEqual(logger.name, "src.kaggle_stream.multimedia")

    def test_lazy_session(self):
        # Initial state
        self.assertIsNone(self.manager._session)
        # Access property
        with patch('requests.Session') as mock_session_cls:
            mock_session = MagicMock()
            mock_session_cls.return_value = mock_session

            session = self.manager.session
            self.assertIsNotNone(self.manager._session)
            mock_session_cls.assert_called_once()
            mock_session.headers.update.assert_called_with({"Authorization": "Bearer test_token"})

    @patch('src.kaggle_stream.multimedia.MultimediaManager.session', new_callable=unittest.mock.PropertyMock)
    def test_generate_audio(self, mock_session_prop):
        mock_session = MagicMock()
        mock_session_prop.return_value = mock_session

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"fake audio content"
        mock_session.post.return_value = mock_response

        output_path = "test_speech.mp3"
        result = self.manager.generate_audio("Hello world", output_path)

        self.assertEqual(result, output_path)
        self.assertTrue(os.path.exists(output_path))
        self.assertEqual(self.manager._audio_cache["Hello world"], b"fake audio content")

        # Cleanup
        if os.path.exists(output_path):
            os.remove(output_path)

    @patch('src.kaggle_stream.multimedia.MultimediaManager.session', new_callable=unittest.mock.PropertyMock)
    def test_generate_mood_image(self, mock_session_prop):
        mock_session = MagicMock()
        mock_session_prop.return_value = mock_session

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"fake image content"
        mock_session.post.return_value = mock_response

        output_path = "test_mood.png"
        result = self.manager.generate_mood_image("happy", output_path)

        self.assertEqual(result, output_path)
        self.assertTrue(os.path.exists(output_path))
        self.assertEqual(self.manager._image_cache["happy"], b"fake image content")

        # Cleanup
        if os.path.exists(output_path):
            os.remove(output_path)

if __name__ == "__main__":
    unittest.main()
