import os
import pytest
from src.kaggle_stream.log_streamer import LogStreamer


# ---------------------------------------------------------------------------
# Shared helper: redirect "WORK_LOG.md" to a tmp_path file
# ---------------------------------------------------------------------------

def _patch_log_path(monkeypatch, log_file):
    """Patch os.path.exists and builtins.open so LogStreamer uses log_file."""
    original_open = open

    def mocked_open(path, mode="r", *args, **kwargs):
        if path == "WORK_LOG.md":
            return original_open(log_file, mode, *args, **kwargs)
        return original_open(path, mode, *args, **kwargs)

    monkeypatch.setattr("builtins.open", mocked_open)
    monkeypatch.setattr(
        "os.path.exists",
        lambda p: True if p == "WORK_LOG.md" else os.path.exists(p),
    )


# ---------------------------------------------------------------------------
# File-not-found path
# ---------------------------------------------------------------------------

def test_file_not_found_returns_sentinel(monkeypatch):
    """When WORK_LOG.md does not exist, get_context returns the sentinel string."""
    monkeypatch.setattr("os.path.exists", lambda p: False)
    assert LogStreamer.get_context() == "No project logs found."


# ---------------------------------------------------------------------------
# Empty file
# ---------------------------------------------------------------------------

def test_empty_file_returns_empty_string(monkeypatch, tmp_path):
    """An empty log file should decode to an empty string."""
    log_file = tmp_path / "WORK_LOG.md"
    log_file.write_bytes(b"")
    _patch_log_path(monkeypatch, log_file)

    result = LogStreamer.get_context()
    assert result == ""


# ---------------------------------------------------------------------------
# Files smaller than the 1500-byte tail window
# ---------------------------------------------------------------------------

def test_small_file_returns_full_content(monkeypatch, tmp_path):
    """Files shorter than 1500 bytes should be returned in full."""
    log_file = tmp_path / "WORK_LOG.md"
    log_file.write_text("Short log content", encoding="utf-8")
    _patch_log_path(monkeypatch, log_file)

    assert LogStreamer.get_context() == "Short log content"


def test_file_exactly_1500_bytes_returns_all(monkeypatch, tmp_path):
    """A file of exactly 1500 bytes should be returned in full (seek to byte 0)."""
    log_file = tmp_path / "WORK_LOG.md"
    content = b"X" * 1500
    log_file.write_bytes(content)
    _patch_log_path(monkeypatch, log_file)

    result = LogStreamer.get_context()
    assert result == "X" * 1500
    assert len(result) == 1500


# ---------------------------------------------------------------------------
# Files larger than the 1500-byte tail window
# ---------------------------------------------------------------------------

def test_file_exactly_1501_bytes_returns_last_1500(monkeypatch, tmp_path):
    """A 1501-byte file should drop exactly the first byte."""
    log_file = tmp_path / "WORK_LOG.md"
    # First byte is 'H' (head); remaining 1500 bytes are 'T' (tail)
    content = b"H" + b"T" * 1500
    log_file.write_bytes(content)
    _patch_log_path(monkeypatch, log_file)

    result = LogStreamer.get_context()
    assert len(result) == 1500
    assert result == "T" * 1500
    assert "H" not in result


def test_large_file_returns_last_1500_bytes(monkeypatch, tmp_path):
    """Files much larger than 1500 bytes must return only the tail."""
    log_file = tmp_path / "WORK_LOG.md"
    content = "A" * 1000 + "B" * 1000
    log_file.write_text(content, encoding="utf-8")
    _patch_log_path(monkeypatch, log_file)

    result = LogStreamer.get_context()
    assert len(result) == 1500
    assert result == content[-1500:]


def test_tail_content_is_correct_not_head(monkeypatch, tmp_path):
    """Verify the returned bytes are the tail, not the head, of a large file."""
    log_file = tmp_path / "WORK_LOG.md"
    head = "HEAD:" + "X" * 995   # 1000 bytes
    tail = "TAIL:" + "Y" * 1495  # 1500 bytes
    content = head + tail
    log_file.write_text(content, encoding="utf-8")
    _patch_log_path(monkeypatch, log_file)

    result = LogStreamer.get_context()
    assert result.startswith("TAIL:")
    assert "HEAD" not in result


# ---------------------------------------------------------------------------
# Unicode / multi-byte character handling
# ---------------------------------------------------------------------------

def test_unicode_intact_when_no_boundary_split(monkeypatch, tmp_path):
    """Multi-byte characters that fit entirely in the tail window are preserved."""
    log_file = tmp_path / "WORK_LOG.md"
    # 1490 ASCII chars + 2 rockets = 1490 + 8 = 1498 bytes → fits in window
    content = "A" * 1490 + "🚀🚀"
    log_file.write_text(content, encoding="utf-8")
    _patch_log_path(monkeypatch, log_file)

    result = LogStreamer.get_context()
    assert result == content
    assert result.endswith("🚀🚀")


def test_unicode_split_at_seek_boundary(monkeypatch, tmp_path):
    """
    When the seek position lands inside a multi-byte UTF-8 sequence,
    errors='ignore' silently drops the invalid leading bytes so the
    result is still a valid Python str.
    """
    log_file = tmp_path / "WORK_LOG.md"
    # 🚀 encodes to 4 bytes: b'\xf0\x9f\x9a\x80'
    # Place the rocket first so the seek at byte 2 lands inside its encoding.
    rocket_bytes = "🚀".encode("utf-8")          # 4 bytes
    body = b"A" * 1498
    content_bytes = rocket_bytes + body          # 1502 bytes total
    log_file.write_bytes(content_bytes)
    _patch_log_path(monkeypatch, log_file)

    # seek → max(0, 1502 - 1500) = 2
    # reads b'\x9a\x80' + b'A'*1498; invalid start bytes → ignored
    result = LogStreamer.get_context()
    assert isinstance(result, str)
    assert result == "A" * 1498  # the two invalid bytes are dropped


def test_unicode_large_file_tail_ends_with_emoji(monkeypatch, tmp_path):
    """Emoji at the very end of a large file should survive the tail read."""
    log_file = tmp_path / "WORK_LOG.md"
    content = "A" * 1498 + "🚀🚀"
    log_file.write_text(content, encoding="utf-8")
    _patch_log_path(monkeypatch, log_file)

    result = LogStreamer.get_context()
    assert isinstance(result, str)
    assert result.endswith("🚀🚀")


# ---------------------------------------------------------------------------
# Exception / error handling
# ---------------------------------------------------------------------------

def test_exception_during_read_returns_error_string(monkeypatch):
    """If an exception is raised while opening the file, a descriptive string is returned."""
    monkeypatch.setattr("os.path.exists", lambda p: True)

    def failing_open(path, mode="r", *args, **kwargs):
        if path == "WORK_LOG.md":
            raise OSError("disk read error")
        return open(path, mode, *args, **kwargs)

    monkeypatch.setattr("builtins.open", failing_open)

    result = LogStreamer.get_context()
    assert result.startswith("Error reading logs:")
    assert "disk read error" in result


def test_exception_message_format(monkeypatch):
    """The error message should follow the f'Error reading logs: {e}' pattern."""
    monkeypatch.setattr("os.path.exists", lambda p: True)

    sentinel = ValueError("sentinel_error_42")

    def failing_open(path, mode="r", *args, **kwargs):
        if path == "WORK_LOG.md":
            raise sentinel
        return open(path, mode, *args, **kwargs)

    monkeypatch.setattr("builtins.open", failing_open)

    result = LogStreamer.get_context()
    assert result == f"Error reading logs: {sentinel}"


# ---------------------------------------------------------------------------
# Regression / combined scenario
# ---------------------------------------------------------------------------

def test_combined_seek_existing_test(monkeypatch, tmp_path):
    """
    Regression test preserving the logic from the original PR test:
    small file, large file, and unicode split all in one parametrised check.
    """
    log_file = tmp_path / "WORK_LOG.md"
    _patch_log_path(monkeypatch, log_file)

    # Small file
    log_file.write_text("Short log content", encoding="utf-8")
    assert LogStreamer.get_context() == "Short log content"

    # Large file
    content = "A" * 1000 + "B" * 1000
    log_file.write_text(content, encoding="utf-8")
    context = LogStreamer.get_context()
    assert len(context) == 1500
    assert context == content[-1500:]

    # Unicode split: 🚀 is 4 bytes; 1498 'A's + 2 rockets = 1506 bytes.
    # Seek to 6 → reads 1500 bytes starting inside the A region, both rockets intact.
    content = "A" * 1498 + "🚀🚀"
    with open(log_file, "w", encoding="utf-8") as f:
        f.write(content)

    context = LogStreamer.get_context()
    assert isinstance(context, str)
    assert context.endswith("🚀🚀")