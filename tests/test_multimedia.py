import unittest
from unittest.mock import patch, MagicMock
from src.kaggle_stream.multimedia import MultimediaManager
import os

class TestMultimediaManager(unittest.TestCase):
    def setUp(self):
        self.manager = MultimediaManager(hf_token="test_token")
        self.test_audio_path = "test_audio.mp3"
        self.test_image_path = "test_image.png"

    def tearDown(self):
        if os.path.exists(self.test_audio_path):
            os.remove(self.test_audio_path)
        if os.path.exists(self.test_image_path):
            os.remove(self.test_image_path)

    @patch('requests.Session.post')
    def test_lazy_session_initialization(self, mock_post):
        # Initial state: session should be None
        self.assertIsNone(self.manager._session)

        # Trigger session property
        session = self.manager.session
        self.assertIsNotNone(self.manager._session)
        self.assertEqual(session.headers["Authorization"], "Bearer test_token")

    @patch('requests.Session.post')
    def test_generate_audio_caching(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"audio_content"
        mock_post.return_value = mock_response

        text = "Hello world"

        # First call
        res1 = self.manager.generate_audio(text, self.test_audio_path)
        self.assertEqual(res1, self.test_audio_path)
        self.assertEqual(mock_post.call_count, 1)

        # Second call (cached)
        res2 = self.manager.generate_audio(text, "test_audio_2.mp3")
        self.assertEqual(res2, "test_audio_2.mp3")
        self.assertEqual(mock_post.call_count, 1)

        if os.path.exists("test_audio_2.mp3"):
            os.remove("test_audio_2.mp3")

    @patch('requests.Session.post')
    def test_generate_mood_image_caching(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"image_content"
        mock_post.return_value = mock_response

        mood = "happy"

        # First call
        res1 = self.manager.generate_mood_image(mood, self.test_image_path)
        self.assertEqual(res1, self.test_image_path)
        self.assertEqual(mock_post.call_count, 1)

        # Second call (cached)
        res2 = self.manager.generate_mood_image(mood, "test_image_2.png")
        self.assertEqual(res2, "test_image_2.png")
        self.assertEqual(mock_post.call_count, 1)

        if os.path.exists("test_image_2.png"):
            os.remove("test_image_2.png")

if __name__ == "__main__":
    unittest.main()
