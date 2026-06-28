import sys
import unittest
from unittest.mock import MagicMock

class TestMultimediaLazyLoading(unittest.TestCase):
    def test_requests_lazy_loading(self):
        # Ensure requests is NOT in sys.modules for a clean test
        # (Though in a real test suite it might be there from other tests)
        # We can at least check if MultimediaManager has it at top level or not

        from src.kaggle_stream.multimedia import MultimediaManager

        # In the unoptimized version, requests is already imported here.
        # We want it to NOT be imported until .session is accessed.

        # To truly test this without interference from other tests,
        # we'd usually use a subprocess, but for a simple check:
        manager = MultimediaManager(hf_token="dummy")

        # We can check if 'requests' was already imported by the module
        # by looking at the globals of the module.
        import src.kaggle_stream.multimedia as mm
        self.assertNotIn('requests', vars(mm), "requests should not be in module globals")

        # Now access session
        session = manager.session
        self.assertIsNotNone(session)

        # After access, requests should be available (locally or in sys.modules)
        self.assertIn('requests', sys.modules)

if __name__ == "__main__":
    unittest.main()
