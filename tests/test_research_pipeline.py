import pytest
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

from unittest.mock import patch
