import os

class LogStreamer:
    """
    Utility to fetch and format project logs for agent discussion.
    """
    # ⚡ Bolt: Class-level cache storing ((path, st_dev, st_ino, st_mtime_ns, st_size), content)
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
            # ⚡ Bolt: Stat-based cache validation checking path, device, inode, mtime, and size.
            # On cache hit, bypass file open, seek, read, and UTF-8 decode.
            cache_key = (log_path, stat.st_dev, stat.st_ino, stat.st_mtime_ns, stat.st_size)
            if LogStreamer._cache and LogStreamer._cache[0] == cache_key:
                return LogStreamer._cache[1]

            # ⚡ Bolt: Use stat.st_size directly and seek-from-end for O(1) tail retrieval
            # instead of reading the whole file into memory (O(N)).
            max_chars = 1500
            file_size = stat.st_size
            with open(log_path, "rb") as f:
                to_read = min(file_size, max_chars)
                if to_read < file_size:
                    f.seek(-to_read, 2)

                # Decode bytes to string, ignoring partial multi-byte characters if they occur
                content = f.read().decode('utf-8', errors='ignore')
                LogStreamer._cache = (cache_key, content)
                return content
        except Exception as e:
            LogStreamer._cache = None
            return f"Error reading logs: {e}"
