import os

class LogStreamer:
    """
    Utility to fetch and format project logs for agent discussion.
    """
    # ⚡ Bolt: Stat-based cache (st_dev, st_ino, st_mtime_ns, st_size, content)
    _cache = None

    @classmethod
    def get_context(cls):
        log_path = "WORK_LOG.md"
        if not os.path.exists(log_path):
            cls._cache = None
            return "No project logs found."

        try:
            # ⚡ Bolt: Fast-path stat check to avoid redundant disk seeks, reads, and decodes.
            stat = os.stat(log_path)
            st_dev = stat.st_dev
            st_ino = stat.st_ino
            st_mtime_ns = stat.st_mtime_ns
            st_size = stat.st_size

            if cls._cache is not None:
                c_dev, c_ino, c_mtime, c_size, c_content = cls._cache
                if c_dev == st_dev and c_ino == st_ino and c_mtime == st_mtime_ns and c_size == st_size:
                    return c_content

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

                # Update cache
                cls._cache = (st_dev, st_ino, st_mtime_ns, st_size, content)
                return content
        except Exception as e:
            return f"Error reading logs: {e}"
