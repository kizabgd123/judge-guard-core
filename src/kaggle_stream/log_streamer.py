import os

class LogStreamer:
    """
    Utility to fetch and format project logs for agent discussion.
    """
    @staticmethod
    def get_context():
        log_path = "WORK_LOG.md"
        if not os.path.exists(log_path):
            return "No project logs found."

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
                return content
        except Exception as e:
            return f"Error reading logs: {e}"
