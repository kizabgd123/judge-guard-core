import time
import os
import sys

# Ensure project root is in path
sys.path.append(os.getcwd())

def measure():
    # Setup work log
    with open("WORK_LOG.md", "w") as f:
        f.write("🟡 Starting Test Action\n")

    start_import = time.perf_counter()
    import judge_guard
    from judge_guard import JudgeGuard
    end_import = time.perf_counter()

    start_init = time.perf_counter()
    guard = JudgeGuard()
    end_init = time.perf_counter()

    action = "Test Action"
    # Ensure it's cached
    if guard.pipeline:
        guard.pipeline.cache_verdict(action, "PASSED")

    start_verify = time.perf_counter()
    res = guard.verify_action(action)
    end_verify = time.perf_counter()

    print(f"Import time: {(end_import - start_import) * 1000:.2f}ms")
    print(f"Init time: {(end_init - start_init) * 1000:.2f}ms")
    print(f"Verify (cached) time: {(end_verify - start_verify) * 1000:.2f}ms")
    print(f"Total time: {(end_verify - start_import) * 1000:.2f}ms")

    # Cleanup
    if os.path.exists("WORK_LOG.md"):
        os.remove("WORK_LOG.md")
    if os.path.exists("research.db"):
        os.remove("research.db")

if __name__ == "__main__":
    measure()
