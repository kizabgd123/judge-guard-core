import os

class LogStreamer:
    """
    Utility to fetch and format project logs for agent discussion.
    """
    _cache = None
    _cache_stat = None

    @classmethod
    def get_context(cls):
        log_path = "WORK_LOG.md"
        if not os.path.exists(log_path):
            cls._cache = None
            cls._cache_stat = None
            return "No project logs found."

        try:
            # ⚡ Bolt: Stat-based caching to bypass file open/seek/read/decode
            # on cache hits when WORK_LOG.md has not been modified.
            st = os.stat(log_path)
            current_stat = (st.st_dev, st.st_ino, st.st_mtime_ns, st.st_size)

            if cls._cache_stat == current_stat and cls._cache is not None:
                return cls._cache

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

            cls._cache = content
            cls._cache_stat = current_stat
            return content
        except Exception as e:
            cls._cache = None
            cls._cache_stat = None
            return f"Error reading logs: {e}"
