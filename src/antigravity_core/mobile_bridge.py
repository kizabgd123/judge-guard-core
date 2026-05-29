"""
Mobile Bridge - The connection between Antigravity Agents and the Mobile PWA.
Writes state to a shared JSON file that the PWA watches/fetches.
"""

import json
import os
import threading
from typing import Dict, Any
from concurrent.futures import ThreadPoolExecutor

# Path to the PWA public directory
PWA_PUBLIC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "mobile_app_pwa", "public")
CONFIG_FILE = os.path.join(PWA_PUBLIC_DIR, "app_config.json")

class MobileBridge:
    def __init__(self):
        self._lock = threading.RLock()
        with self._lock:
            self.app_state = {
                "title": "Antigravity Mobile",
                "theme": "light",
                "content": "Welcome to the Agent-Controlled PWA!",
                "components": []
            }
        # ⚡ Bolt: Executor for offloading blocking disk I/O
        self._executor = ThreadPoolExecutor(max_workers=1)
        self._ensure_public_dir()

        # ⚡ Bolt: Offload initial sync to background thread to avoid blocking imports
        self._executor.submit(self.sync_state)

    def __del__(self):
        """⚡ Bolt: Ensure ThreadPoolExecutor is shut down."""
        if hasattr(self, "_executor"):
            self._executor.shutdown(wait=False)

    def _ensure_public_dir(self):
        """Ensure the PWA public directory exists."""
        if not os.path.exists(PWA_PUBLIC_DIR):
            os.makedirs(PWA_PUBLIC_DIR, exist_ok=True)

    def update_state(self, new_state: Dict[str, Any]) -> Dict[str, Any]:
        """Update the mobile app state and sync to file."""
        with self._lock:
            self.app_state.update(new_state)
        # ⚡ Bolt: Offload blocking disk I/O to background thread
        self._executor.submit(self.sync_state)
        return self.app_state

    def sync_state(self):
        """Write current state to app_config.json."""
        try:
            # ⚡ Bolt: Thread-safe snapshot for serialization
            with self._lock:
                state_snapshot = self.app_state.copy()
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(state_snapshot, f, indent=2)
            # Use logger or print with caution in threads
            # print(f"✅ Bridge: Synced state to {CONFIG_FILE}")
        except Exception as e:
            print(f"❌ Bridge Error: Failed to sync state: {e}")

    def get_state(self) -> Dict[str, Any]:
        """Get current state."""
        with self._lock:
            return self.app_state.copy()

    def push_verdict(self, action: str, status: str, reason: str):
        """
        Push a Judge Verdict to the PWA.
        status: "PASSED" | "BLOCKED"
        """
        verdict_data = {
            "action": action,
            "status": status,
            "reason": reason,
            "timestamp": "Now" # In real app use time.time()
        }
        print(f"📡 Bridge: Pushing Verdict -> {status}")
        self.update_state({"last_verdict": verdict_data})

# Singleton instance
bridge = MobileBridge()

if __name__ == "__main__":
    # Test run
    print("Testing Bridge...")
    bridge.update_state({"content": "This content was injected by the Antigravity Bridge!"})
