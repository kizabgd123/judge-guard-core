import os

class LogStreamer:
    """
    Utility to fetch and format project logs for agent discussion.
    """
    _cache = None  # (stat_key, content)

    @classmethod
    def get_context(cls):
        log_path = "WORK_LOG.md"
        if not os.path.exists(log_path):
            cls._cache = None
            return "No project logs found."

        try:
            st = os.stat(log_path)
            stat_key = (os.path.abspath(log_path), st.st_dev, st.st_ino, st.st_mtime_ns, st.st_size)

            # ⚡ Bolt: Stat-based cache check to bypass file opens, seeks, reads, and decodes on cache hits
            if cls._cache is not None and cls._cache[0] == stat_key:
                return cls._cache[1]

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
            cls._cache = None
            return f"Error reading logs: {e}"
