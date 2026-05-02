import time
import os
import sys

# Add current dir to path to import local modules
sys.path.append(os.getcwd())

def benchmark_init():
    start = time.perf_counter()
    from judge_guard import JudgeGuard
    import_time = time.perf_counter() - start

    start_init = time.perf_counter()
    # Mocking paths to avoid actual disk discovery if possible,
    # but the current code does discovery anyway.
    guard = JudgeGuard()
    init_time = time.perf_counter() - start_init

    print(f"Import time: {import_time*1000:.4f}ms")
    print(f"Init time: {init_time*1000:.4f}ms")
    print(f"Total startup: {(import_time + init_time)*1000:.4f}ms")

if __name__ == "__main__":
    benchmark_init()
