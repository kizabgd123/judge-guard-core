import os

class LogStreamer:
    """
    Utility to fetch and format project logs for agent discussion.
    """
    _cache = None  # Tuple: ((st_dev, st_ino, st_mtime_ns, st_size), content)

    @staticmethod
    def get_context():
        log_path = "WORK_LOG.md"
        if not os.path.exists(log_path):
            return "No project logs found."

        try:
            # ⚡ Bolt: Use stat-based caching checking os.stat attributes (st_dev, st_ino, st_mtime_ns, st_size)
            # to return cached log tail content on cache hits, bypassing file opens, seeks, reads, and UTF-8 decodes.
            st = os.stat(log_path)
            stat_key = (st.st_dev, st.st_ino, st.st_mtime_ns, st.st_size)
            if LogStreamer._cache and LogStreamer._cache[0] == stat_key:
                return LogStreamer._cache[1]

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
                LogStreamer._cache = (stat_key, content)
                return content
        except Exception as e:
            return f"Error reading logs: {e}"
