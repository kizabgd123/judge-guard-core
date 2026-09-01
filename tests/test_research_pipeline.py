import pytest
from unittest.mock import patch
import sqlite3
import os
from pathlib import Path
from research_pipeline import ResearchPipeline

@pytest.fixture
def temp_db(tmp_path):
    db_path = tmp_path / "test_research.db"
    # Overwrite the constant in research_pipeline
    with patch('research_pipeline.DB_PATH', db_path):
        yield db_path

def test_init_db(temp_db):
    pipeline = ResearchPipeline()
    pipeline.init_db()

    assert temp_db.exists()
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='documents'")
    assert cursor.fetchone() is not None

def test_parse_markdown_files(temp_db, tmp_path):
    # Setup test files
    research_dir = tmp_path / "research"
    phase_dir = research_dir / "phase0_scoping"
    phase_dir.mkdir(parents=True)
    md_file = phase_dir / "test.md"
    md_file.write_text("# Test Title\nTest content")

    pipeline = ResearchPipeline()
    pipeline.init_db()

    with patch('research_pipeline.RESEARCH_DIR', research_dir):
        pipeline.parse_markdown_files()

    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()
    cursor.execute("SELECT title, content FROM documents")
    row = cursor.fetchone()
    assert row[0] == "Test Title"
    assert "Test content" in row[1]

def test_extract_patterns(temp_db, tmp_path):
    # Insert a document manually
    pipeline = ResearchPipeline()
    pipeline.init_db()

    # We MUST use the connection from the pipeline to ensure Row factory and visibility
    pipeline.conn.execute("INSERT INTO documents (phase, filename, title, content) VALUES (?, ?, ?, ?)",
                 ("phase0", "test.md", "Test", "### Pattern 1 🔥\nDetails"))
    pipeline.conn.commit()

    pipeline.extract_patterns()

    row = pipeline.conn.execute("SELECT name, priority FROM patterns").fetchone()
    assert row["name"] == "Pattern 1"
    assert row["priority"] == "HIGH"

def test_verdict_caching(temp_db):
    pipeline = ResearchPipeline()
    pipeline.init_db()

    pipeline.cache_verdict("Action 1", "PASSED")
    verdict = pipeline.get_cached_verdict("Action 1")
    assert verdict == "PASSED"


# ── Tests for get_cached_verdict (PR: removed log_audit on cache hit) ──────────

def test_get_cached_verdict_miss_returns_none(temp_db):
    """Cache miss must return None without raising."""
    pipeline = ResearchPipeline()
    pipeline.init_db()

    result = pipeline.get_cached_verdict("action that was never cached")
    assert result is None


def test_get_cached_verdict_failed_verdict(temp_db):
    """Cache hit returns the stored verdict value, including FAILED."""
    pipeline = ResearchPipeline()
    pipeline.init_db()

    pipeline.cache_verdict("risky action", "FAILED")
    assert pipeline.get_cached_verdict("risky action") == "FAILED"


def test_get_cached_verdict_no_log_audit_on_hit(temp_db):
    """PR removed log_audit on cache hit; audit_log should NOT grow on get_cached_verdict."""
    pipeline = ResearchPipeline()
    pipeline.init_db()

    pipeline.cache_verdict("some action", "PASSED")
    # Drain the audit entries created so far
    before = pipeline.conn.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0]

    pipeline.get_cached_verdict("some action")
    after = pipeline.conn.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0]

    assert after == before, "get_cached_verdict must not write to audit_log on a cache hit"


def test_get_cached_verdict_hash_collision_same_action(temp_db):
    """The same action string must always resolve to the same verdict."""
    pipeline = ResearchPipeline()
    pipeline.init_db()

    action = "deterministic action"
    pipeline.cache_verdict(action, "PASSED")

    # Call multiple times – result must be stable
    assert pipeline.get_cached_verdict(action) == "PASSED"
    assert pipeline.get_cached_verdict(action) == "PASSED"


def test_get_cached_verdict_distinct_actions_independent(temp_db):
    """Two different actions must not share a cached verdict."""
    pipeline = ResearchPipeline()
    pipeline.init_db()

    pipeline.cache_verdict("action A", "PASSED")
    pipeline.cache_verdict("action B", "FAILED")

    assert pipeline.get_cached_verdict("action A") == "PASSED"
    assert pipeline.get_cached_verdict("action B") == "FAILED"
    assert pipeline.get_cached_verdict("action C") is None


def test_get_cached_verdict_overwrite(temp_db):
    """cache_verdict with a new verdict for the same action must update the stored value."""
    pipeline = ResearchPipeline()
    pipeline.init_db()

    pipeline.cache_verdict("action X", "PASSED")
    pipeline.cache_verdict("action X", "FAILED")

    assert pipeline.get_cached_verdict("action X") == "FAILED"


# ── Tests for sync_to_notion (PR: early return + comment cleanup) ───────────────

def test_sync_to_notion_empty_queue_is_noop(temp_db):
    """Early-return path: an empty notion_queue must not trigger any I/O or logging."""
    pipeline = ResearchPipeline()
    pipeline.init_db()
    pipeline.notion_queue = []

    with patch("dotenv.load_dotenv") as mock_dotenv:
        pipeline.sync_to_notion()

    mock_dotenv.assert_not_called()


def test_sync_to_notion_saves_to_local_cache_when_no_creds(temp_db, tmp_path):
    """Without Notion credentials the queue must be written to the local JSON cache."""
    pipeline = ResearchPipeline()
    pipeline.init_db()
    pipeline.notion_queue = [{"action": "TEST", "details": "d", "timestamp": "2024-01-01T00:00:00"}]

    cache_file = tmp_path / ".cache" / "notion_queue.json"
    with patch("research_pipeline.NOTION_LOG", cache_file), \
         patch("dotenv.load_dotenv"), \
         patch.dict(os.environ, {}, clear=True):
        # Ensure no token/db_id in env
        os.environ.pop("NOTION_TOKEN", None)
        os.environ.pop("NOTION_DATABASE_ID", None)
        pipeline.sync_to_notion()

    assert cache_file.exists()
    import json
    saved = json.loads(cache_file.read_text())
    assert len(saved) == 1
    assert saved[0]["action"] == "TEST"


def test_sync_to_notion_merges_with_existing_cache(temp_db, tmp_path):
    """New queue entries must be appended to the existing local cache file."""
    import json

    cache_file = tmp_path / ".cache" / "notion_queue.json"
    cache_file.parent.mkdir(parents=True)
    existing_entry = {"action": "EXISTING", "details": "", "timestamp": "2024-01-01T00:00:00"}
    cache_file.write_text(json.dumps([existing_entry]))

    pipeline = ResearchPipeline()
    pipeline.init_db()
    pipeline.notion_queue = [{"action": "NEW", "details": "", "timestamp": "2024-01-02T00:00:00"}]

    with patch("research_pipeline.NOTION_LOG", cache_file), \
         patch("dotenv.load_dotenv"), \
         patch.dict(os.environ, {}, clear=True):
        os.environ.pop("NOTION_TOKEN", None)
        os.environ.pop("NOTION_DATABASE_ID", None)
        pipeline.sync_to_notion()

    saved = json.loads(cache_file.read_text())
    actions = [e["action"] for e in saved]
    assert "EXISTING" in actions
    assert "NEW" in actions


def test_sync_to_notion_handles_corrupt_cache_file(temp_db, tmp_path):
    """If the existing cache file is not valid JSON, it must be overwritten gracefully."""
    import json

    cache_file = tmp_path / ".cache" / "notion_queue.json"
    cache_file.parent.mkdir(parents=True)
    cache_file.write_text("NOT VALID JSON{{{{")

    pipeline = ResearchPipeline()
    pipeline.init_db()
    pipeline.notion_queue = [{"action": "RECOVER", "details": "", "timestamp": "2024-01-01T00:00:00"}]

    with patch("research_pipeline.NOTION_LOG", cache_file), \
         patch("dotenv.load_dotenv"), \
         patch.dict(os.environ, {}, clear=True):
        os.environ.pop("NOTION_TOKEN", None)
        os.environ.pop("NOTION_DATABASE_ID", None)
        pipeline.sync_to_notion()

    saved = json.loads(cache_file.read_text())
    assert any(e["action"] == "RECOVER" for e in saved)


def test_sync_to_notion_pushes_to_notion_when_creds_present(temp_db, tmp_path):
    """When Notion credentials exist, entries must be POSTed via the session."""
    from unittest.mock import MagicMock

    pipeline = ResearchPipeline()
    pipeline.init_db()
    pipeline.notion_queue = [{"action": "SYNC", "details": "ok", "timestamp": "2024-01-01T00:00:00"}]

    mock_resp = MagicMock()
    mock_resp.status_code = 200

    with patch("dotenv.load_dotenv"), \
         patch.dict(os.environ, {"NOTION_TOKEN": "secret", "NOTION_DATABASE_ID": "db-123"}), \
         patch.object(pipeline.session, "post", return_value=mock_resp) as mock_post:
        pipeline.sync_to_notion()

    mock_post.assert_called_once()
    call_kwargs = mock_post.call_args
    assert "notion.com" in call_kwargs[0][0]
    # Queue cleared after successful sync
    assert pipeline.notion_queue == []


def test_sync_to_notion_clears_queue_after_notion_success(temp_db):
    """notion_queue must be empty after a successful Notion sync."""
    from unittest.mock import MagicMock

    pipeline = ResearchPipeline()
    pipeline.init_db()
    pipeline.notion_queue = [
        {"action": "A1", "details": "", "timestamp": "2024-01-01T00:00:00"},
        {"action": "A2", "details": "", "timestamp": "2024-01-01T00:00:01"},
    ]

    mock_resp = MagicMock()
    mock_resp.status_code = 200

    with patch("dotenv.load_dotenv"), \
         patch.dict(os.environ, {"NOTION_TOKEN": "t", "NOTION_DATABASE_ID": "d"}), \
         patch.object(pipeline.session, "post", return_value=mock_resp):
        pipeline.sync_to_notion()

    assert pipeline.notion_queue == []


def test_sync_to_notion_exception_falls_back_to_local_cache(temp_db, tmp_path):
    """If the Notion POST raises, the queue must be persisted to local cache."""
    import json

    cache_file = tmp_path / ".cache" / "notion_queue.json"
    pipeline = ResearchPipeline()
    pipeline.init_db()
    pipeline.notion_queue = [{"action": "FALLBACK", "details": "", "timestamp": "2024-01-01T00:00:00"}]

    with patch("research_pipeline.NOTION_LOG", cache_file), \
         patch("dotenv.load_dotenv"), \
         patch.dict(os.environ, {"NOTION_TOKEN": "t", "NOTION_DATABASE_ID": "d"}), \
         patch.object(pipeline.session, "post", side_effect=Exception("network error")):
        pipeline.sync_to_notion()

    assert cache_file.exists()
    saved = json.loads(cache_file.read_text())
    assert any(e["action"] == "FALLBACK" for e in saved)


def test_sync_to_notion_multiple_entries_all_posted(temp_db):
    """Every entry in notion_queue must be POSTed to Notion individually."""
    from unittest.mock import MagicMock

    pipeline = ResearchPipeline()
    pipeline.init_db()
    pipeline.notion_queue = [
        {"action": "E1", "details": "", "timestamp": "2024-01-01T00:00:00"},
        {"action": "E2", "details": "", "timestamp": "2024-01-01T00:00:01"},
        {"action": "E3", "details": "", "timestamp": "2024-01-01T00:00:02"},
    ]

    mock_resp = MagicMock()
    mock_resp.status_code = 200

    with patch("dotenv.load_dotenv"), \
         patch.dict(os.environ, {"NOTION_TOKEN": "t", "NOTION_DATABASE_ID": "d"}), \
         patch.object(pipeline.session, "post", return_value=mock_resp) as mock_post:
        pipeline.sync_to_notion()

    assert mock_post.call_count == 3