import os

class LogStreamer:
    """
    Utility to fetch and format project logs for agent discussion.
    """
    _cache_key = None
    _cached_content = None

    @classmethod
    def get_context(cls):
        log_path = "WORK_LOG.md"
        try:
            stat = os.stat(log_path)
            cache_key = (stat.st_dev, stat.st_ino, stat.st_mtime_ns, stat.st_size, log_path)
            if cls._cache_key == cache_key and cls._cached_content is not None:
                return cls._cached_content
        except OSError:
            cls._cache_key = None
            cls._cached_content = None
            return "No project logs found."

        try:
            # ⚡ Bolt: Stat-based caching avoids duplicate disk open/seek/read/decodes on repeated calls.
            # Use efficient seek-from-end for O(1) tail retrieval instead of reading the whole file into memory.
            max_chars = 1500
            with open(log_path, "rb") as f:
                f.seek(0, 2)  # Seek to end of file
                file_size = f.tell()

                # Determine how much to read
                to_read = min(file_size, max_chars)
                f.seek(-to_read, 2)

                # Decode bytes to string, ignoring partial multi-byte characters if they occur
                content = f.read().decode('utf-8', errors='ignore')
                cls._cache_key = cache_key
                cls._cached_content = content
                return content
        except Exception as e:
            return f"Error reading logs: {e}"
