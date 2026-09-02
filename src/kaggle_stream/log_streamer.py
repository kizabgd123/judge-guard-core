import os

class LogStreamer:
    """
    Utility to fetch and format project logs for agent discussion.
    """
    _cache = None

    @classmethod
    def get_context(cls):
        log_path = "WORK_LOG.md"
        if not os.path.exists(log_path):
            cls._cache = None
            return "No project logs found."

        try:
            # ⚡ Bolt: Stat-based caching (checking st_mtime_ns and st_size)
            # avoids repeated file opens, seeks, reads, and UTF-8 decodes on cache hits.
            stat = os.stat(log_path)
            st_mtime = stat.st_mtime_ns
            st_size = stat.st_size

            if cls._cache is not None:
                cached_mtime, cached_size, cached_content = cls._cache
                if cached_mtime == st_mtime and cached_size == st_size:
                    return cached_content

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

            cls._cache = (st_mtime, st_size, content)
            return content
        except Exception as e:
            cls._cache = None
            return f"Error reading logs: {e}"
