import time
import os
import unittest
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
                try:
                    os.remove(p)
                except OSError:
                    pass

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

    @patch('src.kaggle_stream.multimedia.open')
    @patch('requests.Session.post')
    def test_write_avoidance_caching(self, mock_post, mock_open):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"content bytes"
        mock_post.return_value = mock_response

        # Setup mock open
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file

        # Let's mock os.path.exists to simulate the file existing after the first write
        with patch('os.path.exists', return_value=True):
            # First write (e.g. cached memory hit writes to disk)
            self.manager._audio_cache["hello"] = b"content bytes"
            self.manager.generate_audio("hello", self.test_audio_path_1)
            # Since path wasn't in _audio_file_cache yet, open must have been called
            self.assertEqual(mock_open.call_count, 1)

            mock_open.reset_mock()

            # Second write with same content and same output path
            self.manager.generate_audio("hello", self.test_audio_path_1)
            # This time open should NOT be called because of write avoidance caching!
            self.assertEqual(mock_open.call_count, 0)

if __name__ == "__main__":
    unittest.main()
