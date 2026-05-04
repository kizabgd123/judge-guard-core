import time
import sys
import os

def measure_startup():
    start = time.perf_counter()
    import judge_guard
    imported_at = time.perf_counter()

    guard = judge_guard.JudgeGuard()
    initialized_at = time.perf_counter()

    print(f"Import time: {(imported_at - start) * 1000:.2f}ms")
    print(f"Initialization time: {(initialized_at - imported_at) * 1000:.2f}ms")
    print(f"Total startup: {(initialized_at - start) * 1000:.2f}ms")

if __name__ == "__main__":
    measure_startup()
