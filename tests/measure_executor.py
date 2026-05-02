import time
from concurrent.futures import ThreadPoolExecutor

start = time.perf_counter()
for _ in range(100):
    executor = ThreadPoolExecutor(max_workers=1)
    executor.shutdown(wait=False)
print(f"ThreadPoolExecutor creation time: {(time.perf_counter() - start)/100*1000:.4f}ms")
