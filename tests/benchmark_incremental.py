import time
import os
import sqlite3
from pathlib import Path
from research_pipeline import ResearchPipeline

def benchmark_extraction():
    # Setup test environment
    db_path = Path("benchmark_test.db")
    if db_path.exists():
        os.remove(db_path)

    # Patch DB_PATH in research_pipeline
    import research_pipeline
    research_pipeline.DB_PATH = db_path

    pipeline = ResearchPipeline()
    pipeline.init_db()

    # Create many documents
    num_docs = 2000
    print(f"Creating {num_docs} documents...")
    for i in range(num_docs):
        pipeline.conn.execute(
            "INSERT INTO documents (phase, filename, title, content) VALUES (?, ?, ?, ?)",
            (f"phase{i%4}", f"doc_{i}.md", f"Doc {i}", f"### Pattern {i} 🔥\nDetails")
        )
    pipeline.conn.commit()

    # Full extraction (baseline)
    print(f"Full extraction (baseline) for {num_docs} docs...")
    start = time.time()
    pipeline.extract_patterns()
    end = time.time()
    full_time = end - start
    print(f"Full: {full_time:.4f}s")

    # Simulate adding one more document
    new_doc_id = num_docs + 1
    cursor = pipeline.conn.execute(
        "INSERT INTO documents (phase, filename, title, content) VALUES (?, ?, ?, ?)",
        ("phase0", f"doc_{new_doc_id}.md", "New Doc", "### New Pattern 🟢\nDetails")
    )
    pipeline.conn.commit()

    # Re-extract ALL
    print("Full extraction again (re-extracting all)...")
    start = time.time()
    pipeline.extract_patterns()
    end = time.time()
    full_again_time = end - start
    print(f"Full Again: {full_again_time:.4f}s")

    # Incremental extraction for just the new doc
    # We need the ID of the new doc
    doc_id = pipeline.conn.execute("SELECT id FROM documents WHERE filename = ?", (f"doc_{new_doc_id}.md",)).fetchone()[0]

    print(f"Incremental extraction for 1 doc (ID: {doc_id})...")
    start = time.time()
    pipeline.extract_patterns(doc_ids=[doc_id])
    end = time.time()
    inc_time = end - start
    print(f"Incremental: {inc_time:.4f}s")

    if inc_time < full_again_time:
        speedup = (full_again_time / inc_time) if inc_time > 0 else float('inf')
        print(f"✅ Success! Incremental is {speedup:.1f}x faster.")
    else:
        print("❌ Failure: Incremental is not faster.")

    # Verification: Check if patterns are correct
    count = pipeline.conn.execute("SELECT COUNT(*) FROM patterns").fetchone()[0]
    print(f"Total patterns in DB: {count}")
    expected = num_docs + 1
    if count == expected:
        print("✅ Correctness verified: Pattern count matches.")
    else:
        print(f"❌ Correctness failed: Expected {expected}, got {count}")

    # Cleanup
    pipeline.close()
    if db_path.exists():
        os.remove(db_path)

if __name__ == "__main__":
    benchmark_extraction()
