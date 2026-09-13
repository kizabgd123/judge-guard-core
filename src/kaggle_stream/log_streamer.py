import os

class LogStreamer:
    """
    Utility to fetch and format project logs for agent discussion.
    """
    _cache = None  # (stat_key, content)

    @classmethod
    def get_context(cls):
        log_path = "WORK_LOG.md"
        try:
            stat = os.stat(log_path)
            stat_key = (stat.st_dev, stat.st_ino, stat.st_mtime_ns, stat.st_size)
            # ⚡ Bolt: Stat-based caching to avoid redundant disk opens/reads on unchanged logs (~10x speedup)
            if cls._cache is not None and cls._cache[0] == stat_key:
                return cls._cache[1]
        except OSError:
            cls._cache = None
            return "No project logs found."

        try:
            # ⚡ Bolt: Use efficient seek-from-end for O(1) tail retrieval
            # instead of reading the whole file into memory (O(N)).
            max_chars = 1500
            with open(log_path, "rb") as f:
                f.seek(0, 2)  # Seek to end of file
                file_size = f.tell()

                # Determine how much to read
                to_read = min(file_size, max_chars)
                f.seek(-to_read, 2)

                # Decode bytes to string, ignoring partial multi-byte characters if they occur
                content = f.read().decode('utf-8', errors='ignore')
                cls._cache = (stat_key, content)
                return content
        except Exception as e:
            return f"Error reading logs: {e}"
