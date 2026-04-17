
import os
import time
import shutil
from pathlib import Path
from research_pipeline import ResearchPipeline

def setup_mock_research(num_files=500):
    research_dir = Path("./research")
    if research_dir.exists():
        shutil.rmtree(research_dir)
    research_dir.mkdir()

    (research_dir / "phase0_scoping").mkdir()

    for i in range(num_files):
        with open(research_dir / "phase0_scoping" / f"doc_{i}.md", "w") as f:
            f.write(f"# Document {i}\n\n")
            f.write(f"### Pattern {i} - HIGH\n")
            f.write(f"Some details about pattern {i}\n")

def benchmark():
    num_files = 500
    setup_mock_research(num_files)

    pipeline = ResearchPipeline()
    pipeline.init_db()

    # Cold start: Parse and Extract all
    print(f"--- Cold Start ({num_files} files) ---")
    start = time.time()
    affected_ids = pipeline.parse_markdown_files()
    parsed_time = time.time() - start

    start = time.time()
    patterns = pipeline.extract_patterns(doc_ids=affected_ids)
    extracted_time = time.time() - start
    print(f"Parse: {parsed_time:.4f}s, Extract: {extracted_time:.4f}s, Total: {parsed_time + extracted_time:.4f}s")

    # Warm start: No changes
    print(f"\n--- Warm Start (No changes, {num_files} files) ---")
    start = time.time()
    affected_ids = pipeline.parse_markdown_files()
    parsed_time = time.time() - start

    start = time.time()
    if affected_ids:
        patterns = pipeline.extract_patterns(doc_ids=affected_ids)
    else:
        patterns = 0
    extracted_time = time.time() - start
    print(f"Parse: {parsed_time:.4f}s, Extract: {extracted_time:.4f}s, Total: {parsed_time + extracted_time:.4f}s")

    # Warm start: 1 file change
    print(f"\n--- Warm Start (1 file changed) ---")
    with open(Path("./research/phase0_scoping/doc_0.md"), "a") as f:
        f.write("\nUpdated content\n")

    start = time.time()
    affected_ids = pipeline.parse_markdown_files()
    parsed_time = time.time() - start

    start = time.time()
    if affected_ids:
        patterns = pipeline.extract_patterns(doc_ids=affected_ids)
    else:
        patterns = 0
    extracted_time = time.time() - start
    print(f"Parse: {parsed_time:.4f}s, Extract: {extracted_time:.4f}s, Total: {parsed_time + extracted_time:.4f}s")

    # Compare with Full Scan (Simulated)
    print(f"\n--- Full Scan (Simulated for 1 change) ---")
    start = time.time()
    # Mocking the old behavior (always scanning everything)
    docs = pipeline.conn.execute("SELECT id, content FROM documents").fetchall()
    for doc in docs:
        pass # Simulate re-extraction loop overhead
    full_scan_time = time.time() - start
    print(f"Full Extract would take roughly: {full_scan_time:.4f}s")

    pipeline.close()
    if os.path.exists("research.db"):
        os.remove("research.db")
    shutil.rmtree("./research")

if __name__ == "__main__":
    benchmark()
