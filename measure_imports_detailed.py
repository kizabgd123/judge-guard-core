import time
import subprocess
import sys

def measure_module(module_name):
    code = f"import time; start = time.perf_counter(); import {module_name}; print(time.perf_counter() - start)"
    res = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    try:
        return float(res.stdout.strip())
    except:
        return 0.0

modules = ["requests", "sqlite3", "json", "re", "logging", "dotenv", "concurrent.futures", "pathlib"]
for m in modules:
    print(f"{m}: {measure_module(m):.4f}s")

# Measure actual files
print(f"research_pipeline: {measure_module('research_pipeline'):.4f}s")
print(f"src.kaggle_stream.multimedia: {measure_module('src.kaggle_stream.multimedia'):.4f}s")
print(f"judge_guard: {measure_module('judge_guard'):.4f}s")
