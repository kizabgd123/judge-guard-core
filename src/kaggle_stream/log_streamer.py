import os

class LogStreamer:
    """
    Utility to fetch and format project logs for agent discussion.
    """
    _cache = None  # Tuple of (stat_tuple, content)

    @classmethod
    def get_context(cls):
        log_path = "WORK_LOG.md"
        try:
            st = os.stat(log_path)
            stat_key = (st.st_dev, st.st_ino, st.st_mtime_ns, st.st_size)

            # ⚡ Bolt: Cache hit - bypass file open, seek, read, and UTF-8 decode
            if cls._cache and cls._cache[0] == stat_key:
                return cls._cache[1]

            # ⚡ Bolt: Cache miss - use efficient seek-from-end for O(1) tail retrieval
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
        except FileNotFoundError:
            cls._cache = None
            return "No project logs found."
        except Exception as e:
            cls._cache = None
            return f"Error reading logs: {e}"
