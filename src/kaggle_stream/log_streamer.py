import os

class LogStreamer:
    """
    Utility to fetch and format project logs for agent discussion.
    """
    _cache = None  # Cache structure: (key_tuple, cached_content)

    @classmethod
    def get_context(cls, log_path: str = "WORK_LOG.md") -> str:
        try:
            stat = os.stat(log_path)
            # ⚡ Bolt: Fast stat key checking (device, inode, mtime_ns, size)
            key = (stat.st_dev, stat.st_ino, stat.st_mtime_ns, stat.st_size)
        except OSError:
            cls._cache = None
            return "No project logs found."

        # ⚡ Bolt: Return cached log tail if stat attributes match to bypass file opens, reads, and decodes
        if cls._cache is not None and cls._cache[0] == key:
            return cls._cache[1]

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
                cls._cache = (key, content)
                return content
        except Exception as e:
            return f"Error reading logs: {e}"
