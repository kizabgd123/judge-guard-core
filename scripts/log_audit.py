#!/usr/bin/env python3
"""
log_audit.py — Tamper-Evident Post-Tool Audit Logger
=====================================================
Reads Antigravity IDE post-tool hook payloads from stdin and records structured,
sanitized, tamper-evident audit records into audit.log.

Features:
1. CRLF Injection Defense: All fields are strictly sanitized to prevent forged log entries.
2. Secret Redaction: Automatically masks API keys, bearer tokens, passwords, and private tokens.
3. Tamper-Evident Integrity: Appends HMAC-SHA256 hash using machine-local secret.
4. Comprehensive Event Extraction: Captures tool name, target file/command, status, and output.
5. Exit code is always 0 (non-blocking audit observability).
"""

import sys
import json
import os
import re
import hmac
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, Tuple


AUDIT_LOG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "audit.log"
)
SECRET_KEY_PATH = os.path.expanduser("~/.gemini/.judge_secret")

# Patterns for sensitive credential detection and redaction
SECRET_PATTERNS = [
    (re.compile(r"Bearer\s+[A-Za-z0-9\-._~+/]+=*", re.IGNORECASE), "Bearer [REDACTED]"),
    (re.compile(r"AIza[0-9A-Za-z\-_]{35}"), "AIza[REDACTED]"),
    (re.compile(r"(ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{36}"), r"\1_[REDACTED]"),
    (re.compile(r"ntn_[0-9A-Za-z]{40,}"), "ntn_[REDACTED]"),
    (re.compile(r"(password|secret|token|api_key|apiKey)\s*[:=]\s*['\"]?([^'\"\s&,]+)['\"]?", re.IGNORECASE), r"\1=[REDACTED]"),
]


def redact_secrets(text: str) -> str:
    """Mask credentials and sensitive tokens from text."""
    if not text:
        return ""
    result = text
    for pattern, replacement in SECRET_PATTERNS:
        result = pattern.sub(replacement, result)
    return result


def sanitize_field(val: Any, max_len: int = 200) -> str:
    """Sanitize string to prevent newline injection (CRLF) and truncate to max_len."""
    if val is None:
        return ""
    s = str(val)
    # Strip carriage returns and replace newlines with escaped \\n
    s = s.replace("\r", "").replace("\n", "\\n").replace("|", "¦")
    s = redact_secrets(s)
    if len(s) > max_len:
        s = s[:max_len] + "..."
    return s.strip()


def get_audit_secret() -> bytes:
    """Retrieve machine-local secret key for tamper-evident HMAC signing."""
    if os.path.exists(SECRET_KEY_PATH):
        try:
            with open(SECRET_KEY_PATH, "rb") as f:
                key = f.read().strip()
                if key:
                    return key
        except Exception:
            pass
    # Fallback to deterministic host salt
    salt = f"{os.uname().nodename}-{os.getuid()}".encode("utf-8")
    return hashlib.sha256(salt).digest()


def extract_payload_info(payload: Any) -> Tuple[str, str, str, str]:
    """
    Extract (tool_name, target, details, status) from diverse hook payload formats.
    """
    if not isinstance(payload, dict):
        return ("unknown", "", "", "unparseable_payload")

    tool_name = payload.get("tool_name") or payload.get("tool") or payload.get("name") or "unknown"
    
    # Extract input arguments
    if "tool_input" in payload:
        tool_input = payload.get("tool_input")
        if not isinstance(tool_input, dict):
            return (str(tool_name), "", "", "unparseable_payload")
    elif "toolCall" in payload:
        tool_call = payload.get("toolCall")
        if not isinstance(tool_call, dict) or not isinstance(tool_call.get("args"), dict):
            return (str(tool_name), "", "", "unparseable_payload")
        tool_input = tool_call["args"]
    else:
        tool_input = {}

    command = tool_input.get("CommandLine", tool_input.get("command"))
    if command is not None and not isinstance(command, str):
        return (str(tool_name), "", "", "unparseable_payload")
    if isinstance(command, str):
        digest = hashlib.sha256(command.encode("utf-8")).hexdigest()[:16]
        target = f"command[length={len(command)} sha256={digest}]"
    else:
        path_value = tool_input.get("TargetFile") or tool_input.get("path") or tool_input.get("AbsolutePath") or ""
        if path_value and not isinstance(path_value, str):
            return (str(tool_name), "", "", "unparseable_payload")
        target = repr(path_value) if path_value else ""

    # Details (parameters preview)
    details_items = []
    if "error" in payload:
        details_items.append(f"error={payload['error']}")
    if "Instruction" in tool_input:
        details_items.append(f"inst={tool_input['Instruction']}")
    elif "Description" in tool_input:
        details_items.append(f"desc={tool_input['Description']}")
    details = " ".join(details_items)

    # Output status
    if "error" in payload:
        status = "error"
    else:
        tool_output = payload.get("tool_output", payload.get("result", {}))
        if isinstance(tool_output, dict):
            status = str(tool_output.get("status") or tool_output.get("returncode") or "ok")
        elif isinstance(tool_output, str):
            status = "ok" if "error" not in tool_output.lower() else "error"
        else:
            status = "executed"

    return (str(tool_name), str(target), details, status)


def format_audit_entry(tool_name: str, target: str, details: str, status: str, secret: bytes) -> str:
    """Format and HMAC-sign a single audit log entry."""
    iso_time = datetime.now(timezone.utc).isoformat()
    clean_tool = sanitize_field(tool_name, 50)
    clean_target = sanitize_field(target, 250)
    clean_details = sanitize_field(details, 250)
    clean_status = sanitize_field(status, 40)

    record_core = f"{iso_time} | tool={clean_tool} | target={clean_target} | details={clean_details} | status={clean_status}"
    sig = hmac.new(secret, record_core.encode("utf-8"), hashlib.sha256).hexdigest()[:16]
    return f"{record_core} | hmac={sig}\n"


def main() -> int:
    """Main entrypoint for post-tool hook invocation."""
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            return 0
        try:
            payload = json.loads(raw)
        except (json.JSONDecodeError, ValueError):
            payload = {"error": "unparseable_payload"}

        secret = get_audit_secret()
        tool_name, target, details, status = extract_payload_info(payload)
        if status == "unparseable_payload":
            sys.stderr.write("[AUDIT] unparseable_payload\n")
        line = format_audit_entry(tool_name, target, details, status, secret)

        try:
            with open(AUDIT_LOG_PATH, "a", encoding="utf-8") as f:
                f.write(line)
        except OSError as e:
            sys.stderr.write(f"[AUDIT LOG ERROR] Cannot write to {AUDIT_LOG_PATH}: {e}\n")

    except Exception as e:
        # Never crash the IDE tool execution on hook failure
        sys.stderr.write(f"[AUDIT LOG UNEXPECTED] {e}\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
