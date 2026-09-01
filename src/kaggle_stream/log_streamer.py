import os

class LogStreamer:
    """
    Utility to fetch and format project logs for agent discussion.
    """
    # ⚡ Bolt: Class-level cache storing (log_path, mtime, size, content)
    _cache = None

    @classmethod
    def get_context(cls, log_path: str = "WORK_LOG.md") -> str:
        if not os.path.exists(log_path):
            return "No project logs found."

        try:
            # ⚡ Bolt: Check file stat (mtime & size) before opening file
            # to reuse cached tail content on hits, bypassing seek/read/decode disk I/O.
            stat = os.stat(log_path)
            mtime = stat.st_mtime
            file_size = stat.st_size

            if cls._cache is not None:
                c_path, c_mtime, c_size, c_content = cls._cache
                if c_path == log_path and c_mtime == mtime and c_size == file_size:
                    return c_content

            # ⚡ Bolt: Use efficient seek-from-end for O(1) tail retrieval
            # instead of reading the whole file into memory (O(N)).
            max_chars = 1500
            # UTF-8 characters can be up to 4 bytes
            max_bytes = max_chars * 4

            with open(log_path, "rb") as f:
                to_read = min(file_size, max_bytes)
                if to_read > 0:
                    f.seek(-to_read, 2)  # Seek to end minus bytes to read

                # Decode bytes to string and slice exact max_chars tail
                content = f.read().decode('utf-8', errors='ignore')[-max_chars:]
                cls._cache = (log_path, mtime, file_size, content)
                return content
        except Exception as e:
            return f"Error reading logs: {e}"
