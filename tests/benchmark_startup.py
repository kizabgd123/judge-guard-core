import time
import os
import sys

# Add current directory to path so we can import judge_guard
sys.path.append(os.getcwd())

def benchmark_init():
    start = time.perf_counter()
    from judge_guard import JudgeGuard
    end_import = time.perf_counter()

    guard = JudgeGuard()
    end_init = time.perf_counter()

    print(f"Import time: {(end_import - start) * 1000:.2f}ms")
    print(f"Init time: {(end_init - end_import) * 1000:.2f}ms")
    print(f"Total startup: {(end_init - start) * 1000:.2f}ms")

if __name__ == "__main__":
    benchmark_init()
