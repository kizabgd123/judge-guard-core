import time
import os
import sys
import subprocess

def measure_startup():
    # Measure import time
    start = time.time()
    # We use a subprocess to get a clean state
    cmd = [sys.executable, "-c", "import time; s=time.time(); import judge_guard; print(time.time()-s)"]
    import_time = float(subprocess.check_output(cmd).decode().strip())

    # Measure init time
    cmd = [sys.executable, "-c", "import time; from judge_guard import JudgeGuard; s=time.time(); j=JudgeGuard(); print(time.time()-s)"]
    init_time = float(subprocess.check_output(cmd).decode().strip())

    print(f"Cold Import Time: {import_time:.4f}s")
    print(f"Initialization Time: {init_time:.4f}s")

if __name__ == "__main__":
    measure_startup()
