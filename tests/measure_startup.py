
import time
import sys
import os

def measure():
    start_import = time.time()
    # We want to measure the time it takes to import judge_guard and init JudgeGuard
    import judge_guard
    end_import = time.time()
    print(f"Import time: {(end_import - start_import) * 1000:.2f}ms")

    start_init = time.time()
    guard = judge_guard.JudgeGuard()
    end_init = time.time()
    print(f"Init time: {(end_init - start_init) * 1000:.2f}ms")

if __name__ == "__main__":
    measure()
