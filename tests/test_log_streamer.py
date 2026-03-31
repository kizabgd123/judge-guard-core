import os
import pytest
import tempfile
from src.kaggle_stream.log_streamer import LogStreamer

@pytest.fixture
def temp_log_file(monkeypatch):
    with tempfile.NamedTemporaryFile(mode='w+', delete=False, encoding='utf-8') as f:
        temp_path = f.name

    # Patch the log_path in LogStreamer
    # Since LogStreamer.get_context defines log_path inside the method,
    # we need to patch os.path.exists and open to point to our temp file
    # or just rely on the fact that we can't easily patch local variables without refactoring.

    # Better: Refactor LogStreamer.get_context to accept an optional path for testing,
    # but the task says "identify and implement ONE small performance improvement"
    # and "don't make architectural changes".

    # Let's try to patch the 'WORK_LOG.md' string if it was a class attribute, but it's not.
    # We'll refactor LogStreamer slightly to make it testable WITHOUT changing its behavior.
    return temp_path

def test_log_streamer_get_context_logic(monkeypatch, tmp_path):
    log_file = tmp_path / "WORK_LOG.md"

    # Mock the log_path inside the method? No, let's just mock the 'open' call.
    original_open = open

    def mocked_open(path, mode="r", *args, **kwargs):
        if path == "WORK_LOG.md":
            return original_open(log_file, mode, *args, **kwargs)
        return original_open(path, mode, *args, **kwargs)

    monkeypatch.setattr("builtins.open", mocked_open)
    monkeypatch.setattr("os.path.exists", lambda p: True if p == "WORK_LOG.md" else os.path.exists(p))

    # Test small file
    log_file.write_text("Short log content")
    assert LogStreamer.get_context() == "Short log content"

    # Test large file
    content = "A" * 1000 + "B" * 1000
    log_file.write_text(content)
    context = LogStreamer.get_context()
    assert len(context) == 1500
    assert context == content[-1500:]

    # Test unicode split
    # 🚀 is 4 bytes. 1498 'A's + 2 rockets = 1498 + 8 = 1506 bytes.
    # We read last 1500 bytes.
    # 1506 - 1500 = 6 bytes skipped.
    # skip first rocket (4 bytes) + 2 bytes of second rocket.
    # 'errors=ignore' should handle this.
    content = "A" * 1498 + "🚀🚀"
    with open(log_file, "w", encoding="utf-8") as f:
        f.write(content)

    context = LogStreamer.get_context()
    assert isinstance(context, str)
    assert context.endswith("🚀🚀")
