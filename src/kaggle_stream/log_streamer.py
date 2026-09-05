import os
from typing import Optional, Tuple

class LogStreamer:
    """
    Utility to fetch and format project logs for agent discussion.
    """
    _cache_key: Optional[Tuple[int, int, int, int]] = None
    _cache_val: Optional[str] = None

    @classmethod
    def get_context(cls) -> str:
        log_path = "WORK_LOG.md"
        try:
            stat = os.stat(log_path)
            key = (stat.st_dev, stat.st_ino, stat.st_mtime_ns, stat.st_size)
            # ⚡ Bolt: Return cached log context if file has not been modified
            if cls._cache_key == key and cls._cache_val is not None:
                return cls._cache_val

            # ⚡ Bolt: Use efficient seek-from-end for O(1) tail retrieval
            # instead of reading the whole file into memory (O(N)).
            max_chars = 1500
            file_size = stat.st_size
            to_read = min(file_size, max_chars)

            with open(log_path, "rb") as f:
                if to_read > 0:
                    f.seek(-to_read, 2)
                # Decode bytes to string, ignoring partial multi-byte characters if they occur
                content = f.read().decode('utf-8', errors='ignore')

            cls._cache_key = key
            cls._cache_val = content
            return content

        except FileNotFoundError:
            cls._cache_key = None
            cls._cache_val = None
            return "No project logs found."
        except Exception as e:
            return f"Error reading logs: {e}"
