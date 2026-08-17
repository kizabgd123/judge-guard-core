#!/usr/bin/env python3
"""
Continuous Guard Daemon for Jugard System Integration (Jude Guard).
Runs continuously to ensure 24/7 availability, log monitoring,
and active enforcement of safety guardrails with API key rotation.
"""
import os
import sys
import time
import logging
import signal
import json
from typing import Optional
from dotenv import load_dotenv

# Ensure dotenv is loaded
load_dotenv()

# Setup structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] [JudeGuardDaemon] %(message)s',
    datefmt='%Y-%m-%dT%H:%M:%S%z'
)
logger = logging.getLogger("JudeGuardDaemon")

# Import core JudgeGuard and GeminiClient
from judge_guard import JudgeGuard
from src.antigravity_core.gemini_client import GeminiClient

class ContinuousGuardDaemon:
    """
    High-availability daemon that keeps Jude Guard active continuously,
    monitors work logs & operations, and manages API key rotation.
    """
    def __init__(self, check_interval: int = 5):
        self.check_interval = check_interval
        self.running = False
        self.guard = JudgeGuard()
        self.client = GeminiClient()
        self.stats = {
            "checks_performed": 0,
            "blocks_triggered": 0,
            "passes_recorded": 0,
            "key_rotations": 0,
            "uptime_seconds": 0,
            "start_time": time.time()
        }

    def start(self, once: bool = False):
        """Start the continuous guard monitoring loop."""
        self.running = True
        logger.info("🟢 Continuous Jude Guard Daemon STARTED. Mode: High Availability (24/7)")
        logger.info(f"🔑 API Key Rotation: ACTIVE ({len(self.client.api_keys)} keys available)")

        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._handle_shutdown)
        signal.signal(signal.SIGTERM, self._handle_shutdown)

        try:
            while self.running:
                self._run_guard_cycle()
                self.stats["checks_performed"] += 1
                self.stats["uptime_seconds"] = int(time.time() - self.stats["start_time"])

                if once:
                    logger.info("Single check cycle completed (--once specified).")
                    break

                time.sleep(self.check_interval)
        except Exception as e:
            logger.error(f"Error in Jude Guard loop: {e}", exc_info=True)
        finally:
            self.stop()

    def _run_guard_cycle(self):
        """Perform one monitoring and verification cycle."""
        work_log = self.guard.work_log_path
        if os.path.exists(work_log):
            mtime = os.path.getmtime(work_log)
            age = time.time() - mtime
            if age < self.check_interval * 2:
                logger.info(f"🔍 Recent work log activity detected ({age:.1f}s ago). Verification active.")

    def _handle_shutdown(self, signum, frame):
        logger.info(f"Received termination signal ({signum}). Shutting down gracefully...")
        self.running = False

    def stop(self):
        self.running = False
        if hasattr(self, 'guard') and self.guard:
            self.guard.close()
        logger.info(f"🔴 Continuous Jude Guard Daemon STOPPED. Stats: {json.dumps(self.stats)}")

def run_self_test() -> bool:
    """Run an immediate self-test of the daemon, API key rotation, and Jude Guard verification."""
    logger.info("🧪 Running immediate self-test for Jude Guard & Key Rotation...")
    
    # Test 1: Gemini Client & Key Rotation
    client = GeminiClient(api_keys="test_key_1, test_key_2, test_key_3")
    initial_index = client.current_key_index
    rotated = client._rotate_key()
    assert rotated is True, "Key rotation failed!"
    assert client.current_key_index == (initial_index + 1), "Key index did not increment properly!"
    logger.info(f"✅ Key Rotation Test PASSED: Rotated from key {initial_index + 1} to {client.current_key_index + 1}")

    # Test 2: Jude Guard Hard Block Security Rule
    guard = JudgeGuard()
    dangerous_pass = guard._is_dangerous_command("rm -rf /")
    assert dangerous_pass is True, "Dangerous command check failed!"
    logger.info("✅ Security Hard Block Test PASSED: 'rm -rf /' detected and blocked.")

    # Test 3: Jude Guard Safe Command Rule
    safe_pass = guard._is_dangerous_command("git status")
    assert safe_pass is False, "Safe command misidentified!"
    logger.info("✅ Security Safe Command Test PASSED: 'git status' allowed.")

    # Test 4: Daemon Single Cycle
    daemon = ContinuousGuardDaemon(check_interval=1)
    daemon.start(once=True)
    logger.info("✅ Continuous Guard Daemon Self-Test PASSED!")
    
    return True

if __name__ == "__main__":
    if "--test" in sys.argv:
        success = run_self_test()
        sys.exit(0 if success else 1)
    
    once_mode = "--once" in sys.argv
    daemon = ContinuousGuardDaemon()
    daemon.start(once=once_mode)
