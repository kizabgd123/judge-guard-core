"""
Agent Nexus 2 — Multi-Agent Coordinator with Jude Guard Integration.

Replaces standalone JudgeGuard with a full multi-agent network:
  - GuardianAgent  : enforces Jude Guard hard blocks and soft guards
  - RotatorAgent   : manages Gemini API key rotation (13 keys)
  - NotionAgent    : syncs results to Notion in background
  - MonitorAgent   : heartbeat + health endpoint
  - NexusOrchestrator: coordinates all agents, always-on daemon thread

Usage:
    from src.antigravity_core.agent_nexus2 import NexusOrchestrator
    nexus = NexusOrchestrator()
    nexus.start()
    result = nexus.verify_action("some action description")
"""
from __future__ import annotations

import json
import logging
import os
import queue
import threading
import time
from concurrent.futures import Future, ThreadPoolExecutor
from typing import Optional

# ---------------------------------------------------------------------------
# Structured JSON logger
# ---------------------------------------------------------------------------

def _make_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        fmt = json.dumps({
            "time": "%(asctime)s",
            "level": "%(levelname)s",
            "agent": name,
            "msg": "%(message)s",
        })
        handler.setFormatter(logging.Formatter(fmt))
        logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger


# ---------------------------------------------------------------------------
# RotatorAgent — cycles through 13 Gemini API keys
# ---------------------------------------------------------------------------

class RotatorAgent:
    """Manages a pool of Gemini API keys with round-robin rotation."""

    def __init__(self) -> None:
        self._log = _make_logger("RotatorAgent")
        raw = os.getenv("GEMINI_API_KEYS", "")
        self._keys: list[str] = [k.strip() for k in raw.split(",") if k.strip()]
        if not self._keys:
            fallback = os.getenv("GEMINI_API_KEY", "")
            if fallback:
                self._keys = [fallback]
        self._index = 0
        self._lock = threading.Lock()
        self._log.info(f"Loaded {len(self._keys)} Gemini API keys")

    def next_key(self) -> Optional[str]:
        """Return the next API key in the rotation pool."""
        with self._lock:
            if not self._keys:
                return None
            key = self._keys[self._index % len(self._keys)]
            self._index += 1
            return key

    def current_key(self) -> Optional[str]:
        """Return current key without advancing the index."""
        with self._lock:
            if not self._keys:
                return None
            return self._keys[self._index % len(self._keys)]

    def key_count(self) -> int:
        return len(self._keys)


# ---------------------------------------------------------------------------
# GuardianAgent — Jude Guard logic as an agent
# ---------------------------------------------------------------------------

HARD_BLOCK_PATTERNS = [
    "drop table", "truncate", "delete from", "schema reset",
    "git push --force", "rm -rf /", "rm -rf /*", "chmod -R 777",
    "sudo rm",
]

SOFT_GUARD_PATTERNS = [
    "integration/", "adapters/", "connectors/", "api/",
    "requirements.txt", "package-lock.json", "Pipfile.lock",
    "migrate_", "setup_", "init_", "install_",
]


class GuardianAgent:
    """Enforces Jude Guard hard blocks and soft guards with Safety Halt threshold."""

    def __init__(self) -> None:
        self._log = _make_logger("GuardianAgent")
        self._consecutive_blocks = 0
        self._safety_halt = False
        self._lock = threading.Lock()

    def is_safety_halted(self) -> bool:
        with self._lock:
            return self._safety_halt

    def reset_safety_halt(self) -> None:
        with self._lock:
            self._consecutive_blocks = 0
            self._safety_halt = False
            self._log.info("🟢 Safety Halt RESET by operator.")

    def check(self, action: str) -> dict:
        """
        Returns dict: {"status": "PASS"|"BLOCK"|"SOFT"|"HALT", "reason": str}
        """
        with self._lock:
            if self._safety_halt:
                reason = "🚨 SAFETY HALT ACTIVE: Multiple consecutive Hard Blocks detected. Service is locked until manual reset."
                self._log.error(reason)
                return {"status": "HALT", "reason": reason}

            action_lower = action.lower()

            # Hard blocks
            for pattern in HARD_BLOCK_PATTERNS:
                if pattern in action_lower:
                    self._consecutive_blocks += 1
                    reason = (
                        f"🔴 HARD BLOCK ({self._consecutive_blocks}/3): Action matches forbidden pattern '{pattern}'. "
                        "Explicit user confirmation required."
                    )
                    if self._consecutive_blocks >= 3:
                        self._safety_halt = True
                        reason = f"🚨 SAFETY HALT TRIGGERED: 3 consecutive Hard Blocks detected! (Last pattern: '{pattern}')"
                        self._log.critical(reason)
                        return {"status": "HALT", "reason": reason}

                    self._log.warning(reason)
                    return {"status": "BLOCK", "reason": reason}

            # On non-block, reset consecutive counter
            self._consecutive_blocks = 0

            # Soft guards
            for pattern in SOFT_GUARD_PATTERNS:
                if pattern in action_lower:
                    reason = (
                        f"🟡 SOFT GUARD: Action touches guarded path '{pattern}'. "
                        "Pause and verify intent before proceeding."
                    )
                    self._log.info(reason)
                    return {"status": "SOFT", "reason": reason}

            self._log.info(f"✅ Action PASSED guardian check: {action[:80]}")
            return {"status": "PASS", "reason": "No violations found."}



# ---------------------------------------------------------------------------
# NotionAgent — background sync
# ---------------------------------------------------------------------------

class NotionAgent:
    """Syncs verdicts to Notion asynchronously."""

    def __init__(self) -> None:
        self._log = _make_logger("NotionAgent")
        self._token = os.getenv("NOTION_API_KEY") or os.getenv("NOTION_TOKEN")
        self._queue: queue.Queue = queue.Queue()
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="notion")
        if self._token:
            self._log.info("Notion token loaded. Sync enabled.")
        else:
            self._log.warning("No Notion token found. Sync disabled.")

    def enqueue(self, action: str, verdict: str, reason: str) -> None:
        """Non-blocking: push a verdict record into Notion sync queue."""
        if not self._token:
            return
        self._queue.put_nowait({"action": action, "verdict": verdict, "reason": reason})
        self._executor.submit(self._flush)

    def _flush(self) -> None:
        """Drain queue and POST each item to Notion API."""
        import urllib.request
        while not self._queue.empty():
            try:
                item = self._queue.get_nowait()
            except queue.Empty:
                break
            payload = {
                "parent": {"type": "database_id", "database_id": "jugard-nexus-log"},
                "properties": {
                    "Action": {"title": [{"text": {"content": item["action"][:200]}}]},
                    "Verdict": {"rich_text": [{"text": {"content": item["verdict"]}}]},
                    "Reason": {"rich_text": [{"text": {"content": item["reason"][:500]}}]},
                    "Timestamp": {"rich_text": [{"text": {"content": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}}]},
                },
            }
            data = json.dumps(payload).encode()
            req = urllib.request.Request(
                "https://api.notion.com/v1/pages",
                data=data,
                headers={
                    "Authorization": f"Bearer {self._token}",
                    "Content-Type": "application/json",
                    "Notion-Version": "2022-06-28",
                },
                method="POST",
            )
            try:
                with urllib.request.urlopen(req, timeout=10) as resp:
                    self._log.info(f"Notion sync OK: HTTP {resp.status} for verdict={item['verdict']}")
            except Exception as exc:
                if "401" in str(exc):
                    self._log.info("Notion token invalid (401). Disabling background Notion sync.")
                    self._token = None
                else:
                    self._log.warning(f"Notion sync failed (non-fatal): {exc}")



# ---------------------------------------------------------------------------
# MonitorAgent — heartbeat + health
# ---------------------------------------------------------------------------

class MonitorAgent:
    """Runs a tiny HTTP health server and emits heartbeat logs."""

    def __init__(self, port: int = 7861) -> None:
        self._log = _make_logger("MonitorAgent")
        self._port = port
        self._running = False
        self._start_time = time.time()
        self._verdicts: dict[str, int] = {"PASS": 0, "BLOCK": 0, "SOFT": 0}
        self._lock = threading.Lock()

    def record(self, verdict: str) -> None:
        with self._lock:
            self._verdicts[verdict] = self._verdicts.get(verdict, 0) + 1

    def start(self) -> None:
        self._running = True
        threading.Thread(target=self._serve, daemon=True, name="monitor-http").start()
        threading.Thread(target=self._heartbeat, daemon=True, name="monitor-hb").start()

    def _serve(self) -> None:
        import http.server
        import socketserver

        agent = self

        class Handler(http.server.BaseHTTPRequestHandler):
            def do_GET(self) -> None:  # noqa: N802
                if self.path in ("/health", "/status"):
                    with agent._lock:
                        body = json.dumps({
                            "status": "ok",
                            "agent": "AgentNexus2",
                            "uptime_seconds": int(time.time() - agent._start_time),
                            "verdicts": agent._verdicts,
                        }).encode()
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(body)
                else:
                    self.send_response(404)
                    self.end_headers()

            def log_message(self, *args) -> None:  # noqa: N802
                pass  # silence default access log

        class ReusableTCPServer(socketserver.TCPServer):
            allow_reuse_address = True

        try:
            with ReusableTCPServer(("0.0.0.0", self._port), Handler) as srv:
                self._log.info(f"MonitorAgent health endpoint: http://localhost:{self._port}/health")
                srv.serve_forever()
        except OSError as exc:
            self._log.info(f"MonitorAgent port {self._port} unavailable ({exc}); health endpoint already active.")


    def _heartbeat(self) -> None:
        while self._running:
            with self._lock:
                self._log.info(
                    f"Heartbeat | uptime={int(time.time()-self._start_time)}s "
                    f"| verdicts={self._verdicts}"
                )
            time.sleep(30)


# ---------------------------------------------------------------------------
# NexusOrchestrator — the main coordinator (replaces JudgeGuard)
# ---------------------------------------------------------------------------

class NexusOrchestrator:
    """
    Agent Nexus 2 — always-on multi-agent orchestrator.

    Replaces the single-agent JudgeGuard with a coordinated team:
      GuardianAgent + RotatorAgent + NotionAgent + MonitorAgent.
    """

    _instance: Optional["NexusOrchestrator"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "NexusOrchestrator":
        """Singleton — only one Nexus per process."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._log = _make_logger("NexusOrchestrator")
        self._guardian = GuardianAgent()
        self._rotator = RotatorAgent()
        self._notion = NotionAgent()
        self._monitor = MonitorAgent(port=int(os.getenv("NEXUS_MONITOR_PORT", "7861")))
        self._started = False
        self._initialized = True

    def start(self) -> None:
        """Start all background agents. Safe to call multiple times."""
        if self._started:
            return
        self._monitor.start()
        self._started = True
        self._log.info(
            f"🚀 Agent Nexus 2 STARTED — "
            f"{self._rotator.key_count()} Gemini keys, "
            f"Notion={'ON' if self._notion._token else 'OFF'}"
        )

    def verify_action(self, action: str) -> dict:
        """
        Run the full Agent Nexus 2 verification pipeline on an action.

        Returns:
            dict with keys: status (PASS|BLOCK|SOFT), reason, key_used
        """
        if not self._started:
            self.start()

        key = self._rotator.next_key()
        result = self._guardian.check(action)
        self._monitor.record(result["status"])
        self._notion.enqueue(action, result["status"], result["reason"])

        result["key_used"] = (key[:8] + "...") if key else "none"
        result["agent"] = "AgentNexus2"
        return result

    def reset_safety_halt(self) -> None:
        self._guardian.reset_safety_halt()

    def status(self) -> dict:
        """Return current system status snapshot."""
        return {
            "agent": "AgentNexus2",
            "started": self._started,
            "safety_halt": self._guardian.is_safety_halted(),
            "gemini_keys": self._rotator.key_count(),
            "notion_enabled": bool(self._notion._token),
            "monitor_port": self._monitor._port,
            "verdicts": dict(self._monitor._verdicts),
        }



# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    import sys
    nexus = NexusOrchestrator()
    nexus.start()

    if len(sys.argv) < 2:
        print(json.dumps(nexus.status(), indent=2))
        return

    action = " ".join(sys.argv[1:])
    result = nexus.verify_action(action)
    print(json.dumps(result, indent=2))
    if result["status"] == "BLOCK":
        sys.exit(1)


if __name__ == "__main__":
    main()
