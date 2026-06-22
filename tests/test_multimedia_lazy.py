import unittest
from unittest.mock import MagicMock, patch
from src.kaggle_stream.multimedia import MultimediaManager
import os

class TestMultimediaLazy(unittest.TestCase):
    def test_lazy_initialization(self):
        manager = MultimediaManager(hf_token="test_token")

        # Backend attributes should be None initially
        self.assertIsNone(manager._session)
        self.assertIsNone(manager._logger)
        self.assertIsNone(manager._lock)

        # Accessing session should initialize session and lock
        _ = manager.session
        self.assertIsNotNone(manager._session)
        self.assertIsNotNone(manager._lock)
        self.assertIsNone(manager._logger) # Still None

        # Accessing logger should initialize it
        _ = manager.logger
        self.assertIsNotNone(manager._logger)

    def test_cache_logic(self):
        manager = MultimediaManager(hf_token="test_token")
        manager._audio_cache["hello"] = b"fake_audio"

        with patch("builtins.open", unittest.mock.mock_open()) as mocked_file:
            path = manager.generate_audio("hello", "out.mp3")
            self.assertEqual(path, "out.mp3")
            mocked_file().write.assert_called_once_with(b"fake_audio")

if __name__ == "__main__":
    unittest.main()
