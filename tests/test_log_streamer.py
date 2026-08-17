import os
import pytest
from src.kaggle_stream.log_streamer import LogStreamer

def test_get_context_no_file(tmp_path, monkeypatch):
    # Ensure WORK_LOG.md doesn't exist
    monkeypatch.chdir(tmp_path)
    if os.path.exists("WORK_LOG.md"):
        os.remove("WORK_LOG.md")

    assert LogStreamer.get_context() == "No project logs found."

def test_get_context_small_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    content = "Hello log"
    with open("WORK_LOG.md", "w") as f:
        f.write(content)

    assert LogStreamer.get_context() == content

def test_get_context_large_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    large_content = "A" * 5000 + "END_OF_LOG"
    with open("WORK_LOG.md", "w") as f:
        f.write(large_content)

    context = LogStreamer.get_context()
    assert len(context) == 1500
    assert context.endswith("END_OF_LOG")

def test_get_context_unicode_split(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    # A 3-byte character: 🚀 (U+1F680, UTF-8: F0 9F 9A 80)
    # We want to place it such that it might be split if we just did a raw byte seek.
    # But since we use decode(errors='ignore'), it should just skip the partial character.
    unicode_char = "🚀"
    content = "A" * 1499 + unicode_char
    with open("WORK_LOG.md", "wb") as f:
        f.write(content.encode('utf-8'))

    context = LogStreamer.get_context()
    # If 1500 bytes are read, it might split the emoji if it was at the boundary.
    # Here, 1499 'A's + emoji. The emoji is 4 bytes.
    # Total size: 1503 bytes.
    # to_read = 1500. seek(-1500, 2) starts at the 4th byte.
    # The file is: [A, A, A, A... (1499 times), F0, 9F, 9A, 80]
    # Indices: 0 to 1498 are 'A', 1499, 1500, 1501, 1502 are the emoji bytes.
    # seek(-1500, 2) means we start at 1503 - 1500 = 3.
    # We read from index 3 to 1502. That's 1500 bytes.
    # It contains 'A's and the full emoji.
    assert unicode_char in context
