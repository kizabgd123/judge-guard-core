import time
import sqlite3
import os
from pathlib import Path
from research_pipeline import ResearchPipeline

DB_PATH = Path("./research_benchmark.db")

def setup_benchmark_db(num_docs=1000, patterns_per_doc=10):
    if DB_PATH.exists():
        os.remove(DB_PATH)

    pipeline = ResearchPipeline()
    # Mock DB_PATH for the pipeline instance
    import research_pipeline
    research_pipeline.DB_PATH = DB_PATH

    pipeline.init_db()

    conn = sqlite3.connect(DB_PATH)
    doc_ids = []
    for i in range(num_docs):
        content = f"# Document {i}\n\n"
        for j in range(patterns_per_doc):
            content += f"### Pattern {i}_{j} - High priority\nThis is pattern {j} in doc {i}.\n\n"

        cursor = conn.execute(
            "INSERT INTO documents (phase, filename, title, content, hash) VALUES (?, ?, ?, ?, ?) RETURNING id",
            (f"phase{i%3}", f"file_{i}.md", f"Title {i}", content, f"hash_{i}")
        )
        doc_ids.append(cursor.fetchone()[0])
    conn.commit()
    conn.close()
    return pipeline, doc_ids

def benchmark_extraction(pipeline, doc_ids=None):
    start = time.time()
    found = pipeline.extract_patterns(doc_ids=doc_ids)
    end = time.time()
    return end - start, found

if __name__ == "__main__":
    print("Setting up benchmark with 1000 documents...")
    pipeline, doc_ids = setup_benchmark_db(num_docs=1000, patterns_per_doc=10)

    print("Running initial extraction (full scan)...")
    duration, found = benchmark_extraction(pipeline)
    print(f"Full extraction: {duration:.4f}s, found {found} patterns")

    print("Running second extraction (incremental, NO changes)...")
    duration, found = benchmark_extraction(pipeline, doc_ids=[])
    print(f"Incremental (no changes): {duration:.4f}s, found {found} patterns")

    print("Running third extraction (incremental, 1 change)...")
    duration, found = benchmark_extraction(pipeline, doc_ids=[doc_ids[0]])
    print(f"Incremental (1 change): {duration:.4f}s, found {found} patterns")

    # Cleanup
    if DB_PATH.exists():
        os.remove(DB_PATH)
