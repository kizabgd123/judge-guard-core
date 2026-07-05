import time
import sys

def profile_import(module_name):
    start = time.time()
    __import__(module_name)
    end = time.time()
    print(f"{module_name}: {(end - start) * 1000:.2f}ms")

modules = [
    "os", "sqlite3", "hashlib", "json", "re", "logging",
    "datetime", "pathlib", "typing", "concurrent.futures", "dotenv"
]

for m in modules:
    if m in sys.modules:
        del sys.modules[m]
    profile_import(m)
