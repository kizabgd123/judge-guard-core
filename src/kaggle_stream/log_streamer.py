import os

class LogStreamer:
    """
    Utility to fetch and format project logs for agent discussion.
    """
    _cache = None

    @staticmethod
    def get_context():
        log_path = "WORK_LOG.md"
        try:
            stat = os.stat(log_path)
        except OSError:
            LogStreamer._cache = None
            return "No project logs found."

        try:
            # ⚡ Bolt: Check stat-based cache (path, dev, ino, mtime_ns, size)
            # to bypass file opens, seeks, reads, and UTF-8 decodes on unchanged logs.
            cache = LogStreamer._cache
            if cache is not None and cache[:5] == (log_path, stat.st_dev, stat.st_ino, stat.st_mtime_ns, stat.st_size):
                return cache[5]

            # ⚡ Bolt: Use efficient seek-from-end for O(1) tail retrieval
            # instead of reading the whole file into memory (O(N)).
            max_chars = 1500
            file_size = stat.st_size
            with open(log_path, "rb") as f:
                f.seek(0, 2)  # Seek to end of file

                # Determine how much to read
                to_read = min(file_size, max_chars)
                if to_read > 0:
                    f.seek(-to_read, 2)

                # Decode bytes to string, ignoring partial multi-byte characters if they occur
                content = f.read().decode('utf-8', errors='ignore')
                LogStreamer._cache = (log_path, stat.st_dev, stat.st_ino, stat.st_mtime_ns, stat.st_size, content)
                return content
        except Exception as e:
            return f"Error reading logs: {e}"
