import time
import os
import sys
import subprocess

def measure_command(cmd):
    start = time.time()
    subprocess.run(cmd, shell=True, capture_output=True)
    return (time.time() - start) * 1000

def run_benchmarks():
    print("--- JudgeGuard Performance Benchmarks ---")

    # 1. Cold Import Time (measure how long it takes to just run 'python3 -c "import judge_guard"')
    import_time = measure_command('python3 -c "import judge_guard"')
    print(f"Cold Import Time: {import_time:.2f}ms")

    # 2. Initialization Time
    init_script = """
import time
import judge_guard
start = time.time()
guard = judge_guard.JudgeGuard()
print((time.time() - start) * 1000)
"""
    with open("_bench_init.py", "w") as f:
        f.write(init_script)

    init_output = subprocess.run(['python3', '_bench_init.py'], capture_output=True, text=True).stdout.strip()
    init_time = float(init_output.splitlines()[-1])
    print(f"Initialization Time: {init_time:.2f}ms")

    # 3. Cached Verification (Hot Path)
    # Ensure we have a cached verdict
    setup_cache = """
import os
import judge_guard
from research_pipeline import ResearchPipeline
rp = ResearchPipeline().init_db()
rp.cache_verdict("Benchmark Action", "PASSED")
with open("WORK_LOG.md", "w") as f:
    f.write("🟡 Starting Benchmark Action\\n")
"""
    subprocess.run(['python3', '-c', setup_cache])

    hot_path_script = """
import time
import judge_guard
guard = judge_guard.JudgeGuard()
# Warm up bridge import if necessary (but we want to measure first call overhead too)
start = time.time()
guard.verify_action("Benchmark Action")
print((time.time() - start) * 1000)
"""
    with open("_bench_hot_path.py", "w") as f:
        f.write(hot_path_script)

    hot_path_output = subprocess.run(['python3', '_bench_hot_path.py'], capture_output=True, text=True).stdout.strip()
    hot_path_time = float(hot_path_output.splitlines()[-1])
    print(f"Cached Verification (Hot Path): {hot_path_time:.2f}ms")

    # Cleanup
    for f in ["_bench_init.py", "_bench_hot_path.py", "research.db"]:
        if os.path.exists(f):
            os.remove(f)

if __name__ == "__main__":
    run_benchmarks()
