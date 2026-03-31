import os
import sys

# Ensure project root is in path
sys.path.append(os.getcwd())

from src.kaggle_stream.log_streamer import LogStreamer

def run_test():
    test_log = "TEST_WORK_LOG.md"

    # Temporarily monkeypatch the log path in LogStreamer
    # Since LogStreamer hardcodes "WORK_LOG.md", we'll rename any existing one
    # or just use a dummy one for testing if we can modify the class.
    # Let's just create a dummy WORK_LOG.md and restore it.

    real_log = "WORK_LOG.md"
    temp_log = "WORK_LOG.md.bak"

    if os.path.exists(real_log):
        os.rename(real_log, temp_log)

    try:
        # Case 1: Small file (< 1500 chars)
        small_content = "This is a small log file."
        with open(real_log, "w") as f:
            f.write(small_content)

        result = LogStreamer.get_context()
        assert result == small_content, f"Expected {small_content}, got {result}"
        print("✅ Small file test passed.")

        # Case 2: Large file (> 1500 chars)
        large_content = "A" * 2000 + "END_OF_LOG"
        with open(real_log, "w") as f:
            f.write(large_content)

        result = LogStreamer.get_context()
        expected = large_content[-1500:]
        assert result == expected, f"Large file test failed. Length: {len(result)}"
        assert result.endswith("END_OF_LOG"), "Large file test failed to get the tail."
        print("✅ Large file test passed.")

        # Case 3: Handle multi-byte characters
        multi_byte_log = "👋" * 500 + "END" # 👋 is 4 bytes
        # Total bytes: 500 * 4 + 3 = 2003 bytes
        with open(real_log, "wb") as f:
            f.write(multi_byte_log.encode("utf-8"))

        result = LogStreamer.get_context()
        # The result might start with a broken emoji which 'ignore' handles
        assert result.endswith("END"), "Multi-byte test failed to get the tail."
        print("✅ Multi-byte robustness test passed.")

    finally:
        if os.path.exists(real_log):
            os.remove(real_log)
        if os.path.exists(temp_log):
            os.rename(temp_log, real_log)

if __name__ == "__main__":
    run_test()
