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
            with open(log_path, "r") as f:
                content = f.read()
                # Get the last 1500 characters to stay within context window and focus on recent work
                return content[-1500:]
        except Exception as e:
            return f"Error reading logs: {e}"
