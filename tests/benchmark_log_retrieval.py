import os
import time
import tempfile

def current_load_context(file_path, max_chars=15000):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            return content[-max_chars:]
    except Exception:
        return ""

def optimized_load_context(file_path, max_chars=15000):
    try:
        with open(file_path, "rb") as f:
            f.seek(0, 2)
            file_size = f.tell()
            to_read = min(file_size, max_chars)
            f.seek(-to_read, 2)
            return f.read().decode('utf-8', errors='ignore')
    except Exception:
        return ""

def current_check_work_log(file_path):
    try:
        with open(file_path, 'r', encoding="utf-8") as f:
            content = f.read()
            last_lines = content[-1000:].lower()
            return '🟡' in last_lines or 'starting' in last_lines
    except Exception:
        return False

def optimized_check_work_log(file_path):
    try:
        with open(file_path, "rb") as f:
            f.seek(0, 2)
            file_size = f.tell()
            to_read = min(file_size, 1000)
            f.seek(-to_read, 2)
            last_lines = f.read().decode('utf-8', errors='ignore').lower()
            return '🟡' in last_lines or 'starting' in last_lines
    except Exception:
        return False

def run_benchmark():
    file_size_mb = 10
    with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.md') as tmp:
        # Fill file with ~10MB of data
        content = "Line of log data with some text.\n" * (file_size_mb * 1024 * 1024 // 32)
        tmp.write(content)
        tmp.write("🟡 Starting [FINAL_ACTION]\n")
        tmp_path = tmp.name

    print(f"--- Log Retrieval Benchmark ({file_size_mb}MB file) ---")

    # Benchmark _load_context
    start = time.time()
    for _ in range(100):
        current_load_context(tmp_path)
    current_time = time.time() - start

    start = time.time()
    for _ in range(100):
        optimized_load_context(tmp_path)
    opt_time = time.time() - start

    print(f"_load_context (100 iterations):")
    print(f"  Current:   {current_time:.4f}s")
    print(f"  Optimized: {opt_time:.4f}s")
    print(f"  Speedup:   {current_time/opt_time:.1f}x")

    # Benchmark _check_work_log
    start = time.time()
    for _ in range(100):
        current_check_work_log(tmp_path)
    current_time = time.time() - start

    start = time.time()
    for _ in range(100):
        optimized_check_work_log(tmp_path)
    opt_time = time.time() - start

    print(f"\n_check_work_log (100 iterations):")
    print(f"  Current:   {current_time:.4f}s")
    print(f"  Optimized: {opt_time:.4f}s")
    print(f"  Speedup:   {current_time/opt_time:.1f}x")

    os.unlink(tmp_path)

if __name__ == "__main__":
    run_benchmark()
