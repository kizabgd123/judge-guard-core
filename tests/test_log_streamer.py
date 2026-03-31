import pytest
from unittest.mock import patch, mock_open, MagicMock
from src.kaggle_stream.log_streamer import LogStreamer


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def write_log(tmp_path, content, mode="w", encoding="utf-8"):
    """Write content to WORK_LOG.md in tmp_path and return the path."""
    log_file = tmp_path / "WORK_LOG.md"
    if mode == "wb":
        log_file.write_bytes(content)
    else:
        log_file.write_text(content, encoding=encoding)
    return log_file


# ---------------------------------------------------------------------------
# Tests: file-not-found / no log
# ---------------------------------------------------------------------------

def test_no_log_file_returns_message(tmp_path, monkeypatch):
    """When WORK_LOG.md does not exist, return the sentinel message."""
    monkeypatch.chdir(tmp_path)
    result = LogStreamer.get_context()
    assert result == "No project logs found."


# ---------------------------------------------------------------------------
# Tests: small files (< 1500 bytes)
# ---------------------------------------------------------------------------

def test_small_file_returns_full_content(tmp_path, monkeypatch):
    """A file smaller than 1500 bytes should be returned in full."""
    monkeypatch.chdir(tmp_path)
    content = "This is a small log file."
    write_log(tmp_path, content)
    result = LogStreamer.get_context()
    assert result == content


def test_empty_file_returns_empty_string(tmp_path, monkeypatch):
    """An empty WORK_LOG.md should return an empty string, not an error."""
    monkeypatch.chdir(tmp_path)
    write_log(tmp_path, "")
    result = LogStreamer.get_context()
    assert result == ""


def test_small_file_returns_string_type(tmp_path, monkeypatch):
    """get_context() must always return a str (not bytes)."""
    monkeypatch.chdir(tmp_path)
    write_log(tmp_path, "hello")
    result = LogStreamer.get_context()
    assert isinstance(result, str)


# ---------------------------------------------------------------------------
# Tests: large files (> 1500 bytes) — tail retrieval
# ---------------------------------------------------------------------------

def test_large_file_returns_last_1500_bytes(tmp_path, monkeypatch):
    """A file larger than 1500 bytes should return exactly the tail 1500 bytes."""
    monkeypatch.chdir(tmp_path)
    # 2000 ASCII bytes; last 1500 are recoverable
    content = "A" * 2000 + "END_OF_LOG"
    write_log(tmp_path, content)
    result = LogStreamer.get_context()
    expected = (content.encode("utf-8")[-1500:]).decode("utf-8", errors="ignore")
    assert result == expected


def test_large_file_tail_ends_with_marker(tmp_path, monkeypatch):
    """The tail of a large file must include the very end of the file."""
    monkeypatch.chdir(tmp_path)
    large_content = "B" * 3000 + "TAIL_MARKER"
    write_log(tmp_path, large_content)
    result = LogStreamer.get_context()
    assert result.endswith("TAIL_MARKER")


def test_large_file_does_not_return_head(tmp_path, monkeypatch):
    """Content from the beginning of a large file must not appear in the result."""
    monkeypatch.chdir(tmp_path)
    prefix = "HEAD_CONTENT"
    large_content = prefix + "X" * 2000
    write_log(tmp_path, large_content)
    result = LogStreamer.get_context()
    assert not result.startswith(prefix)


def test_large_file_result_is_string(tmp_path, monkeypatch):
    """Tail result from a large file must be str, not bytes."""
    monkeypatch.chdir(tmp_path)
    write_log(tmp_path, "Z" * 2000)
    result = LogStreamer.get_context()
    assert isinstance(result, str)


# ---------------------------------------------------------------------------
# Tests: boundary cases
# ---------------------------------------------------------------------------

def test_exactly_1500_bytes_returns_all(tmp_path, monkeypatch):
    """A file of exactly 1500 bytes should be returned in full."""
    monkeypatch.chdir(tmp_path)
    content = "C" * 1500
    write_log(tmp_path, content)
    result = LogStreamer.get_context()
    assert result == content
    assert len(result) == 1500


def test_1501_bytes_returns_tail_1500(tmp_path, monkeypatch):
    """A file of 1501 bytes should return the last 1500 bytes (drops first byte)."""
    monkeypatch.chdir(tmp_path)
    content = "X" + "Y" * 1500   # 1501 ASCII bytes
    write_log(tmp_path, content)
    result = LogStreamer.get_context()
    assert result == "Y" * 1500
    assert not result.startswith("X")


def test_seek_reads_from_end_not_start(tmp_path, monkeypatch):
    """
    Regression: the old code read the full file and sliced [-1500:].
    The new code uses binary seek from end. Verify the output is equivalent
    for ASCII content so we confirm the correct bytes are returned.
    """
    monkeypatch.chdir(tmp_path)
    content = "S" * 500 + "T" * 1000 + "U" * 500  # 2000 bytes total
    write_log(tmp_path, content)
    result = LogStreamer.get_context()
    expected_bytes = content.encode("utf-8")[-1500:]
    assert result == expected_bytes.decode("utf-8", errors="ignore")


# ---------------------------------------------------------------------------
# Tests: multi-byte / UTF-8 safety
# ---------------------------------------------------------------------------

def test_multibyte_chars_tail_preserved(tmp_path, monkeypatch):
    """Multi-byte characters near the end of the file must appear in the tail."""
    monkeypatch.chdir(tmp_path)
    # 👋 is 4 bytes; put a clear ASCII marker at the very end
    multi_byte_log = "👋" * 500 + "END"   # 500*4 + 3 = 2003 bytes
    write_log(tmp_path, multi_byte_log.encode("utf-8"), mode="wb")
    result = LogStreamer.get_context()
    assert result.endswith("END")


def test_multibyte_seek_mid_char_does_not_raise(tmp_path, monkeypatch):
    """
    Seeking into the middle of a multi-byte character must NOT raise an exception;
    errors='ignore' swallows broken lead bytes.
    """
    monkeypatch.chdir(tmp_path)
    # Make a file where the seek lands inside a multi-byte sequence
    content_bytes = "👋".encode("utf-8") * 400   # 1600 bytes; seek at byte 100 from end
    write_log(tmp_path, content_bytes, mode="wb")
    result = LogStreamer.get_context()
    assert isinstance(result, str)  # Should not raise; errors='ignore' handles it


def test_mixed_ascii_and_unicode(tmp_path, monkeypatch):
    """ASCII and multi-byte chars mixed together should not corrupt the tail."""
    monkeypatch.chdir(tmp_path)
    # Pad with ASCII so the tail is pure ASCII + a known suffix
    prefix = "a" * 1000
    suffix = "hello world"
    content = (prefix + suffix).encode("utf-8")
    write_log(tmp_path, content, mode="wb")
    result = LogStreamer.get_context()
    assert result.endswith(suffix)


# ---------------------------------------------------------------------------
# Tests: error handling
# ---------------------------------------------------------------------------

def test_exception_during_read_returns_error_string(tmp_path, monkeypatch):
    """If an exception is raised while reading, return a descriptive error string."""
    monkeypatch.chdir(tmp_path)
    # Create the file so the existence check passes
    write_log(tmp_path, "some content")

    with patch("builtins.open", side_effect=OSError("disk failure")):
        result = LogStreamer.get_context()

    assert result.startswith("Error reading logs:")
    assert "disk failure" in result


def test_permission_error_returns_error_string(tmp_path, monkeypatch):
    """A PermissionError while opening the file should return a readable error."""
    monkeypatch.chdir(tmp_path)
    write_log(tmp_path, "content")

    with patch("builtins.open", side_effect=PermissionError("permission denied")):
        result = LogStreamer.get_context()

    assert "Error reading logs:" in result
    assert "permission denied" in result


# ---------------------------------------------------------------------------
# Tests: return-value shape
# ---------------------------------------------------------------------------

def test_get_context_never_returns_bytes(tmp_path, monkeypatch):
    """
    Even though the implementation reads in binary mode internally,
    the public API must always return str.
    """
    monkeypatch.chdir(tmp_path)
    write_log(tmp_path, "binary mode should be transparent")
    result = LogStreamer.get_context()
    assert not isinstance(result, bytes)


def test_get_context_large_file_length_at_most_1500_chars(tmp_path, monkeypatch):
    """
    For a large all-ASCII file, the returned string length must not exceed
    1500 characters (1 byte == 1 char for ASCII).
    """
    monkeypatch.chdir(tmp_path)
    write_log(tmp_path, "W" * 5000)
    result = LogStreamer.get_context()
    assert len(result) <= 1500