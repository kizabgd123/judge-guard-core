import time
import sys
import subprocess

def measure_import(module_name):
    code = f"import time; start=time.perf_counter(); import {module_name}; print((time.perf_counter()-start)*1000)"
    try:
        result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
        if result.returncode == 0:
            return float(result.stdout.strip())
        else:
            return -1
    except Exception:
        return -1

modules = [
    "os", "sys", "time", "glob", "logging", "typing",
    "concurrent.futures", "dotenv", "sqlite3", "hashlib", "json", "re",
    "requests", "google.generativeai"
]

print(f"{'Module':<25} | {'Import Time (ms)':<15}")
print("-" * 43)
for mod in modules:
    t = measure_import(mod)
    print(f"{mod:<25} | {t:>15.4f}")

# Measure total startup of judge_guard
start = time.perf_counter()
import judge_guard
total_import = (time.perf_counter() - start) * 1000
print(f"\nTotal judge_guard import time: {total_import:.4f}ms")
