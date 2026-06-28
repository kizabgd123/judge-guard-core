import time
import sys

start = time.perf_counter()
import research_pipeline
end = time.perf_counter()
print(f"Import research_pipeline took: {end - start:.4f}s")

start = time.perf_counter()
from src.kaggle_stream import multimedia
end = time.perf_counter()
print(f"Import src.kaggle_stream.multimedia took: {end - start:.4f}s")
