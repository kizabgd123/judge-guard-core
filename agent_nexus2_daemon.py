#!/usr/bin/env python3
"""
agent_nexus2_daemon.py — Always-on Agent Nexus 2 daemon.

Starts the NexusOrchestrator (which includes GuardianAgent, RotatorAgent,
NotionAgent, MonitorAgent) and keeps it alive indefinitely.

Run as a persistent background process:
    python3 agent_nexus2_daemon.py &

Health check:
    curl http://localhost:7861/health
"""
from __future__ import annotations

import json
import os
import signal
import sys
import time

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from src.antigravity_core.agent_nexus2 import NexusOrchestrator, _make_logger

LOG = _make_logger("NexusDaemon")
HEARTBEAT_INTERVAL = int(os.getenv("GUARDIAN_CHECK_INTERVAL_SECONDS", "30"))


def _handle_signal(signum, _frame):
    LOG.info(f"Signal {signum} received — Agent Nexus 2 daemon shutting down cleanly.")
    sys.exit(0)


def main() -> None:
    signal.signal(signal.SIGTERM, _handle_signal)
    signal.signal(signal.SIGINT, _handle_signal)

    LOG.info("=" * 60)
    LOG.info("Agent Nexus 2 Daemon STARTING")
    LOG.info("=" * 60)

    nexus = NexusOrchestrator()
    nexus.start()

    LOG.info(json.dumps(nexus.status()))

    # Keep daemon alive — status log every interval
    while True:
        time.sleep(HEARTBEAT_INTERVAL)
        try:
            status = nexus.status()
            LOG.info(json.dumps(status))
        except Exception as exc:
            LOG.error(f"Daemon loop error: {exc}")


if __name__ == "__main__":
    main()
