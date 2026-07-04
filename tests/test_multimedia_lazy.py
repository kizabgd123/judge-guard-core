import sys
import unittest
from unittest.mock import MagicMock, patch

class TestMultimediaLazy(unittest.TestCase):
    def test_requests_lazy_load(self):
        # 1. Ensure requests is NOT in sys.modules
        if 'requests' in sys.modules:
            del sys.modules['requests']

        from src.kaggle_stream.multimedia import MultimediaManager

        # 2. Instantiate - should NOT trigger requests import
        manager = MultimediaManager(hf_token="dummy")
        self.assertNotIn('requests', sys.modules)

        # 3. Access session - SHOULD trigger requests import
        session = manager.session
        self.assertIn('requests', sys.modules)
        self.assertIsNotNone(session)

if __name__ == "__main__":
    unittest.main()
