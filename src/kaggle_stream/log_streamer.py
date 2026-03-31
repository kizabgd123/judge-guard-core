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
            # ⚡ Bolt: Use binary mode and seek from end to avoid reading full file into memory.
            # Using 'rb' and decode with 'ignore' handles potential multi-byte character issues
            # if we seek into the middle of one.
            with open(log_path, "rb") as f:
                f.seek(0, 2)  # Move to the end of the file
                file_size = f.tell()
                # Move back up to 1500 bytes from the end
                f.seek(max(0, file_size - 1500))
                binary_content = f.read()
                return binary_content.decode("utf-8", errors="ignore")
        except Exception as e:
            return f"Error reading logs: {e}"
