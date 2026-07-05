import time
import os
from research_pipeline import ResearchPipeline

def benchmark_write():
    if os.path.exists("bench.db"):
        os.remove("bench.db")

    # Patch DB_PATH
    import research_pipeline
    research_pipeline.DB_PATH = research_pipeline.Path("bench.db")

    rp = ResearchPipeline().init_db()

    start = time.time()
    for i in range(10):
        rp.cache_verdict(f"Action {i}", "PASSED")
    end = time.time()

    avg_latency = (end - start) / 10 * 1000
    print(f"Average cache_verdict latency: {avg_latency:.2f}ms")

    rp.close()
    if os.path.exists("bench.db"):
        os.remove("bench.db")

if __name__ == "__main__":
    benchmark_write()
