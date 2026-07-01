import sys
import unittest
from unittest.mock import patch, MagicMock
from src.kaggle_stream.multimedia import MultimediaManager

class TestMultimediaManagerLazy(unittest.TestCase):
    def test_lazy_session_initialization(self):
        # Ensure requests is NOT in sys.modules (or at least we can check if it's initialized)
        manager = MultimediaManager(hf_token="dummy")

        # Internal _session should be None initially
        self.assertIsNone(manager._session)

        # Accessing session property should initialize it
        with patch('requests.Session') as mock_session_cls:
            mock_session = MagicMock()
            mock_session_cls.return_value = mock_session

            session = manager.session
            self.assertIsNotNone(session)
            mock_session_cls.assert_called_once()

            # Subsequent access should reuse the same session
            session2 = manager.session
            self.assertIs(session, session2)
            mock_session_cls.assert_called_once()

    def test_thread_safety(self):
        import threading
        manager = MultimediaManager(hf_token="dummy")
        sessions = []
        def get_session():
            sessions.append(manager.session)

        threads = [threading.Thread(target=get_session) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All threads should have received the same session object
        self.assertEqual(len(sessions), 10)
        for s in sessions:
            self.assertIs(s, sessions[0])

    def test_cache_reuse(self):
        manager = MultimediaManager(hf_token="dummy")
        # Mock open to avoid actual file I/O
        with patch('builtins.open', unittest.mock.mock_open()) as mocked_file:
            # Manually seed cache
            manager._audio_cache["hello"] = b"audio_bytes"

            path = manager.generate_audio("hello", "test.mp3")
            self.assertEqual(path, "test.mp3")
            mocked_file.assert_called_with("test.mp3", "wb")
            mocked_file().write.assert_called_with(b"audio_bytes")

    def test_context_manager(self):
        with patch('requests.Session') as mock_session_cls:
            mock_session = MagicMock()
            mock_session_cls.return_value = mock_session

            with MultimediaManager(hf_token="dummy") as manager:
                _ = manager.session

            mock_session.close.assert_called_once()

if __name__ == "__main__":
    unittest.main()
