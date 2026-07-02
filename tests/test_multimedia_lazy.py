import sys
import unittest
from unittest.mock import MagicMock, patch

class TestMultimediaLazy(unittest.TestCase):
    def test_lazy_session_loading(self):
        # 1. Ensure 'requests' is NOT in sys.modules before we start
        if 'requests' in sys.modules:
            del sys.modules['requests']

        # 2. Import MultimediaManager
        from src.kaggle_stream.multimedia import MultimediaManager

        # 3. Verify 'requests' is STILL NOT in sys.modules
        self.assertNotIn('requests', sys.modules, "requests should not be imported on module load")

        # 4. Instantiate MultimediaManager
        mm = MultimediaManager(hf_token="test_token")

        # 5. Verify 'requests' is STILL NOT in sys.modules after instantiation
        self.assertNotIn('requests', sys.modules, "requests should not be imported on instantiation")

        # 6. Access the session property (this should trigger the import)
        _ = mm.session
        self.assertIn('requests', sys.modules, "requests should be imported after session access")

    def test_multimedia_functionality_with_lazy_session(self):
        # Test that generate_audio still works with the lazy session
        from src.kaggle_stream.multimedia import MultimediaManager
        mm = MultimediaManager(hf_token="test_token")

        # We need to make sure requests is imported before we patch it if we are using string patching
        import requests
        with patch('requests.Session') as mock_session_cls:
            mock_session = mock_session_cls.return_value
            mock_session.post.return_value.status_code = 200
            mock_session.post.return_value.content = b"fake audio"

            # This should trigger lazy session init (or just return it if already init)
            path = mm.generate_audio("Hello", output_path="test_audio.mp3")

            self.assertEqual(path, "test_audio.mp3")
            mock_session.post.assert_called_once()

            # Cleanup
            import os
            if os.path.exists("test_audio.mp3"):
                os.remove("test_audio.mp3")

if __name__ == "__main__":
    unittest.main()
