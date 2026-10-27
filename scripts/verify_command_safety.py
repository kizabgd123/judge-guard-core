#!/usr/bin/env python3
"""
verify_command_safety.py — JudgeGuard Pre-Tool Hook
======================================================
Čita Antigravity IDE hook payload sa stdin i blokira opasne komande.

Antigravity IDE šalje JSON payload na stdin u formatu:
{
  "tool_name": "run_command",
  "tool_input": {
    "CommandLine": "rm -rf /"
  }
}

Exit Code 0 → komanda je dozvoljena
Exit Code 1 → komanda je BLOKIRANA
"""

import sys
import json


# Obrasci koji su UVEK zabranjeni — bez izuzetaka
BLOCKED_PATTERNS = [
    "rm -rf /",
    "rm -rf ~",
    "mkfs",
    "> /dev/sd",
    "dd if=/dev/zero",
    ":(){ :|:& };:",  # fork bomb
    "chmod -R 777 /",
    "sudo rm -rf",
    ">/dev/null 2>&1 &",  # background nuke
    "DROP TABLE",
    "DROP DATABASE",
    "TRUNCATE TABLE",
    "shred /dev/sd",
]

# Obrazci koji zahtevaju JudgeGuard verifikaciju pre izvršenja
REQUIRES_JUDGEGUARD = [
    "git push",
    "git commit",
    "npm publish",
    "pip install",
    "apt install",
    "curl | sh",
    "wget | sh",
    "bash <(",
]


def main() -> int:
    """
    Validira komandu iz hook payload-a.

    Returns:
        int: 0 ako je komanda dozvoljena, 1 ako je blokirana.
    """
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            # Nema payload-a — propusti (Antigravity može pozvati bez payload-a)
            return 0

        payload = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        # Neispravan JSON payload — propusti da ne blokiramo legitimne alate
        return 0

    # Izvuci komandu iz različitih mogućih struktura payload-a
    tool_input = payload.get("tool_input", payload.get("toolCall", {}).get("args", {}))
    cmd = tool_input.get("CommandLine", tool_input.get("command", ""))

    if not cmd:
        return 0

    cmd_upper = cmd.upper()

    # Provera apsolutno zabranjenih obrazaca
    for pattern in BLOCKED_PATTERNS:
        if pattern.upper() in cmd_upper:
            sys.stderr.write(
                f"[HOOK BLOCKED] ❌ Opasna komanda detektovana: '{pattern}' u '{cmd[:100]}'\n"
            )
            sys.stderr.write(
                "[HOOK BLOCKED] ❌ Pokrenite JudgeGuard manuelno ako ste sigurni da je ovo sigurno.\n"
            )
            return 1

    # Propusti komandu
    return 0


if __name__ == "__main__":
    sys.exit(main())
