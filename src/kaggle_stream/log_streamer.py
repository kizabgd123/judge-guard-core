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
            # ⚡ Bolt: Use seek-to-tail for O(1) performance regardless of log file size
            with open(log_path, "rb") as f:
                f.seek(0, 2)
                file_size = f.tell()
                f.seek(max(0, file_size - 1500))
                # Decode with ignore to safely handle split multi-byte characters at the start
                return f.read().decode("utf-8", errors="ignore")
        except Exception as e:
            return f"Error reading logs: {e}"
