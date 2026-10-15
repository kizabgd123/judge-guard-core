import time
import os
import unittest
import requests
from unittest.mock import patch, MagicMock
from src.kaggle_stream.multimedia import MultimediaManager

class TestMultimediaCaching(unittest.TestCase):
    def setUp(self):
        # Initialize with a dummy token to avoid mock mode bypass
        self.manager = MultimediaManager(hf_token="test_token")
        self.test_audio_path_1 = "test_speech_1.mp3"
        self.test_audio_path_2 = "test_speech_2.mp3"
        self.test_image_path_1 = "test_mood_1.png"
        self.test_image_path_2 = "test_mood_2.png"

    def tearDown(self):
        for p in [self.test_audio_path_1, self.test_audio_path_2, self.test_image_path_1, self.test_image_path_2]:
            if os.path.exists(p):
                os.remove(p)

    @patch('requests.Session.post')
    def test_audio_caching(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"fake audio content"
        mock_post.return_value = mock_response

        text = "Hello, this is a test for caching."

        # First call - should trigger API call
        self.manager.generate_audio(text, self.test_audio_path_1)
        self.assertEqual(mock_post.call_count, 1)

        # Second call - should NOT trigger API call
        self.manager.generate_audio(text, self.test_audio_path_2)
        self.assertEqual(mock_post.call_count, 1)

        with open(self.test_audio_path_2, "rb") as f:
            self.assertEqual(f.read(), b"fake audio content")

    @patch('requests.Session.post')
    def test_image_caching(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"fake image content"
        mock_post.return_value = mock_response

        mood = "happy"

        # First call - should trigger API call
        self.manager.generate_mood_image(mood, self.test_image_path_1)
        self.assertEqual(mock_post.call_count, 1)

        # Second call - should NOT trigger API call
        self.manager.generate_mood_image(mood, self.test_image_path_2)
        self.assertEqual(mock_post.call_count, 1)

        with open(self.test_image_path_2, "rb") as f:
            self.assertEqual(f.read(), b"fake image content")

    @patch('requests.Session.post')
    def test_disk_write_avoidance(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"fake audio content"
        mock_post.return_value = mock_response

        text = "Test disk write avoidance"
        output_path = self.test_audio_path_1

        # First call: not cached. Should write to disk.
        self.manager.generate_audio(text, output_path)
        self.assertTrue(os.path.exists(output_path))

        # We will mock 'builtins.open' to verify that the next call does NOT open/write to the file.
        with patch('builtins.open', MagicMock()) as mock_open:
            # Second call: cached in memory AND file exists on disk with identical tracked content.
            # It should skip opening the file completely.
            self.manager.generate_audio(text, output_path)
            mock_open.assert_not_called()

if __name__ == "__main__":
    unittest.main()
