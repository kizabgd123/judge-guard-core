#!/usr/bin/env python3
"""Fail-closed command safety hook for Antigravity's run_command tool."""

import json
import os
import shlex
import sys
from pathlib import Path


def _extract_command(payload: object) -> str | None:
    if not isinstance(payload, dict):
        return None
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        tool_call = payload.get("toolCall")
        args = tool_call.get("args") if isinstance(tool_call, dict) else None
        tool_input = args if isinstance(args, dict) else payload
    for key in ("CommandLine", "command", "cmd"):
        value = tool_input.get(key)
        if value is not None:
            return value if isinstance(value, str) else None
    return ""


def _is_root_delete(tokens: list[str]) -> bool:
    for index, token in enumerate(tokens):
        if os.path.basename(token) != "rm":
            continue
        cursor = index + 1
        recursive = force = False
        while cursor < len(tokens) and tokens[cursor].startswith("-") and tokens[cursor] != "--":
            flags = tokens[cursor][1:]
            recursive |= "r" in flags or "R" in flags or "recursive" in flags
            force |= "f" in flags or "force" in flags
            cursor += 1
        if cursor < len(tokens) and tokens[cursor] == "--":
            cursor += 1
        if not (recursive and force):
            continue
        targets = tokens[cursor:]
        expanded = [os.path.expandvars(target).replace("${HOME}", os.path.expanduser("~")) for target in targets]
        for target in expanded:
            normalized = os.path.normpath(os.path.expanduser(target))
            home_glob = normalized.startswith(os.path.expanduser("~") + os.sep) and normalized.endswith(os.sep + "*")
            if normalized in {"/", "/root", os.path.expanduser("~"), "."} or target == "/*" or home_glob:
                return True
    return False


def _required_scope(tokens: list[str]) -> str | None:
    lowered = [token.lower() for token in tokens]
    if any(lowered[i:i + 2] in (["git", "commit"], ["git", "push"]) for i in range(max(0, len(lowered) - 1))):
        return "git_commit"
    if any(lowered[i:i + 2] == ["npm", "publish"] for i in range(max(0, len(lowered) - 1))):
        return "npm_publish"
    if any(lowered[i:i + 2] in (["pip", "install"], ["apt", "install"], ["apt-get", "install"]) for i in range(max(0, len(lowered) - 1))):
        return "package_install"
    has_remote_fetch = any(token in {"curl", "wget"} for token in lowered)
    has_pipe_to_shell = any(
        token in {"sh", "bash", "zsh"} and "|" in lowered[:index]
        for index, token in enumerate(lowered)
    )
    if has_remote_fetch and has_pipe_to_shell or "<(" in tokens:
        return "remote_script"
    return None


def _block(reason: str) -> int:
    sys.stderr.write(f"[HOOK BLOCKED] {reason}\n")
    return 1


def main() -> int:
    raw = sys.stdin.read()
    if not raw.strip():
        return _block("hook payload is empty")
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return _block("hook payload is not valid JSON")

    command = _extract_command(payload)
    if command is None:
        return _block("command could not be extracted from this payload")
    if not command:
        return _block("command is missing or empty")

    try:
        tokens = shlex.split(command, punctuation_chars=";&|<>()")
    except ValueError:
        return _block("command could not be parsed safely")
    normalized = " ".join(tokens).lower()
    chmod_root = any(
        tokens[index].lower() == "chmod"
        and any("r" in flag.lower() for flag in tokens[index + 1:index + 3] if flag.startswith("-"))
        and "777" in tokens[index + 1:index + 4]
        and "/" in tokens[index + 1:index + 5]
        for index in range(len(tokens))
    )
    destructive = (
        _is_root_delete(tokens)
        or chmod_root
        or any(pattern in normalized for pattern in (
            "mkfs", "dd if=/dev/zero", ": ( : | : & ) ; :",
            "drop table", "drop database", "truncate table", "shred /dev/sd",
        ))
    )
    if destructive:
        return _block("command matches a destructive operation")

    scope = _required_scope(tokens)
    if scope:
        try:
            project_root = Path(__file__).resolve().parents[1]
            sys.path.insert(0, str(project_root))
            from src.antigravity_core.ticket_vault import require_ticket
            require_ticket(scope, os.getenv("JUDGE_EXECUTION_TICKET"))
        except Exception:
            return _block("JudgeGuard approval ticket is missing, invalid, expired, or already consumed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
