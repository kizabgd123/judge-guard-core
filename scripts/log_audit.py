#!/usr/bin/env python3
"""
log_audit.py — JudgeGuard Post-Tool Audit Logger
=================================================
Čita Antigravity IDE post-tool hook payload sa stdin i upisuje audit log.

Antigravity IDE šalje JSON payload na stdin posle izvršenja alata u formatu:
{
  "tool_name": "write_file",
  "tool_input": { "path": "...", ... },
  "tool_output": { ... }
}

Svaki audit log unos ide u audit.log u root-u workspace-a.
Exit Code je uvek 0 (ne blokiramo, samo logujemo).
"""

import sys
import json
import os
from datetime import datetime


AUDIT_LOG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "audit.log"
)


def main() -> int:
    """
    Loguje post-tool akciju u audit.log.

    Returns:
        int: Uvek 0 (ne blokiramo, samo logujemo).
    """
    timestamp = datetime.now().isoformat()

    try:
        raw = sys.stdin.read()
        if not raw.strip():
            return 0

        payload = json.loads(raw)
        tool_name = payload.get("tool_name", "unknown")
        tool_input = payload.get("tool_input", {})

        # Izvuci ključne informacije o alatu
        summary_parts = [f"tool={tool_name}"]
        if "path" in tool_input:
            summary_parts.append(f"path={tool_input['path']}")
        if "CommandLine" in tool_input:
            cmd = tool_input["CommandLine"][:80]
            summary_parts.append(f"cmd={cmd}")

        summary = " | ".join(summary_parts)

    except (json.JSONDecodeError, ValueError):
        summary = "unparseable_payload"

    log_line = f"[{timestamp}] POST_TOOL: {summary}\n"

    try:
        with open(AUDIT_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(log_line)
    except OSError as e:
        sys.stderr.write(f"[AUDIT LOG ERROR] Ne mogu pisati u {AUDIT_LOG_PATH}: {e}\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
