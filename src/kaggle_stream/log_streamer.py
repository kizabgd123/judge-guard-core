import os
import threading

class LogStreamer:
    """
    Utility to fetch and format project logs for agent discussion.
    """
    # ⚡ Bolt: Stat-based cache variables and thread lock
    _cache_lock = threading.RLock()
    _cache_key = None
    _cache_content = None

    @classmethod
    def get_context(cls):
        log_path = "WORK_LOG.md"
        if not os.path.exists(log_path):
            with cls._cache_lock:
                cls._cache_key = None
                cls._cache_content = None
            return "No project logs found."

        try:
            # ⚡ Bolt: Check file stat to bypass duplicate disk reads and UTF-8 decodes on cache hits
            stat = os.stat(log_path)
            current_key = (os.path.abspath(log_path), stat.st_dev, stat.st_ino, stat.st_mtime_ns, stat.st_size)

            with cls._cache_lock:
                if cls._cache_key == current_key and cls._cache_content is not None:
                    return cls._cache_content

            # Cache miss - perform seek-from-end tail read
            max_chars = 1500
            with open(log_path, "rb") as f:
                f.seek(0, 2)  # Seek to end of file
                file_size = f.tell()

                # Determine how much to read
                to_read = min(file_size, max_chars)
                f.seek(-to_read, 2)

                # Decode bytes to string, ignoring partial multi-byte characters if they occur
                content = f.read().decode('utf-8', errors='ignore')

            with cls._cache_lock:
                cls._cache_key = current_key
                cls._cache_content = content

            return content
        except Exception as e:
            return f"Error reading logs: {e}"
