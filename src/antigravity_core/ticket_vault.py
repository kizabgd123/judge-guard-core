"""
Execution Ticket Vault — Anti-Circumvention & Gated Execution Engine
=====================================================================
Issues and validates cryptographically signed, single-use, time-limited
execution tickets. Guarantees that mutating or production operations
(e.g., publishing to LinkedIn, destructive migrations, cloud deployments)
cannot execute unless JudgeGuard has genuinely evaluated and approved
that exact operation within a strict TTL window (60 seconds).

Guarantees:
1. Zero-Simulation / Zero-Mock compliance.
2. Single-use: once consumed, ticket status becomes CONSUMED (no replay attacks).
3. Non-forgeable: HMAC-SHA256 signature using a secure local secret key.
4. Auto-expiring: strictly valid for TTL seconds (default 60s).
"""

import os
import sys
import time
import json
import hmac
import hashlib
import uuid
import tempfile
import fcntl
from typing import Optional, Dict, Any

TICKETS_DIR = os.path.expanduser("~/.gemini/tickets")
SECRET_KEY_PATH = os.path.expanduser("~/.gemini/.judge_secret")
DEFAULT_TTL_SECONDS = 60


def _get_or_create_master_secret(secret_key_path: str = SECRET_KEY_PATH) -> bytes:
    """Ensure a persistent, machine-local HMAC signing key exists."""
    os.makedirs(os.path.dirname(secret_key_path), mode=0o700, exist_ok=True)
    if os.path.exists(secret_key_path):
        try:
            with open(secret_key_path, "rb") as key_file:
                raw_key = key_file.read().strip()
                if raw_key:
                    return raw_key
        except Exception:
            pass

    # Generate fresh 256-bit random key material for HMAC verification
    key_material = os.urandom(32).hex().encode("utf-8")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(secret_key_path, flags, 0o600)
    except FileExistsError:
        return _get_or_create_master_secret(secret_key_path)
    with os.fdopen(fd, "wb") as key_out:
        key_out.write(key_material)
        key_out.flush()
        os.fsync(key_out.fileno())
    return key_material


def _sign_payload(secret: bytes, payload_str: str) -> str:
    """Compute HMAC-SHA256 signature for a string payload."""
    return hmac.new(secret, payload_str.encode("utf-8"), hashlib.sha256).hexdigest()


import re


def _matches_scope(ticket_action: str, requested_scope: str) -> bool:
    """Check if ticket action authorized the requested execution scope."""
    t_words = set(re.findall(r"\w+", ticket_action.lower()))
    s_lower = requested_scope.lower().strip()
    tokens_map = {
        "social_push": ({"social"}, {"push", "post", "publish"}, {"linkedin", "instagram"}),
        "linkedin_publish": ({"linkedin"}, {"publish", "post"}),
        "git_commit": ({"git"}, {"commit"}),
        "deploy": ({"deploy"}, {"release", "ship"}, {"production", "prod"}),
        "npm_publish": ({"npm"}, {"publish"}),
        "package_install": ({"install"}, {"package", "dependency", "pip", "apt"}),
        "remote_script": ({"curl", "wget", "download"}, {"script", "shell", "bash", "sh"}),
    }
    if s_lower in tokens_map:
        return all(group & t_words for group in tokens_map[s_lower])
    return bool(s_lower) and " ".join(ticket_action.lower().split()) == " ".join(s_lower.split())


class TicketVault:
    """
    Manages generation, storage, validation, and single-use consumption of
    JudgeGuard execution tickets.
    """

    def __init__(self, tickets_dir: str = TICKETS_DIR, secret_key_path: str = SECRET_KEY_PATH):
        self.tickets_dir = os.path.expanduser(tickets_dir)
        os.makedirs(self.tickets_dir, mode=0o700, exist_ok=True)
        os.chmod(self.tickets_dir, 0o700)
        self.active_ticket_file = os.path.join(self.tickets_dir, ".active_ticket.json")
        self.lock_file = os.path.join(self.tickets_dir, ".vault.lock")
        self.secret = _get_or_create_master_secret(os.path.expanduser(secret_key_path))

    def _write_json_atomic(self, file_path: str, data: Dict[str, Any]) -> None:
        fd, temp_path = tempfile.mkstemp(prefix=".ticket-", dir=self.tickets_dir)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as output:
                os.chmod(temp_path, 0o600)
                json.dump(data, output, indent=2)
                output.flush()
                os.fsync(output.fileno())
            os.replace(temp_path, file_path)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def issue_ticket(self, action: str, ttl_seconds: int = DEFAULT_TTL_SECONDS) -> Dict[str, Any]:
        """
        Issue a brand new, signed execution ticket for an approved action.
        """
        ticket_id = str(uuid.uuid4())
        now = time.time()
        action_hash = hashlib.sha256(action.strip().encode("utf-8")).hexdigest()
        nonce = os.urandom(16).hex()

        ticket_data = {
            "ticket_id": ticket_id,
            "action": action.strip(),
            "action_hash": action_hash,
            "created_at": now,
            "expires_at": now + ttl_seconds,
            "ttl": ttl_seconds,
            "nonce": nonce,
            "status": "ACTIVE"
        }

        # Build canonical signing payload
        sign_base = f"{ticket_id}|{action_hash}|{now}|{ticket_data['expires_at']}|{nonce}"
        ticket_data["signature"] = _sign_payload(self.secret, sign_base)

        file_path = os.path.join(self.tickets_dir, f"{ticket_id}.json")
        self._write_json_atomic(file_path, ticket_data)

        try:
            self._write_json_atomic(self.active_ticket_file, ticket_data)
        except Exception:
            pass

        return ticket_data

    def verify_and_consume(self, action_scope: str, ticket_id: Optional[str] = None) -> bool:
        """Serialize verification and consumption so tickets cannot be replayed concurrently."""
        with open(self.lock_file, "a", encoding="utf-8") as lock:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
            try:
                return self._verify_and_consume_unlocked(action_scope, ticket_id)
            finally:
                fcntl.flock(lock.fileno(), fcntl.LOCK_UN)

    def _verify_and_consume_unlocked(self, action_scope: str, ticket_id: Optional[str] = None) -> bool:
        """
        Verify that a valid, active ticket exists covering the requested action scope,
        and immediately consume it (mark as CONSUMED) to prevent replay.

        If ticket_id is not provided, scans for the newest active valid ticket
        matching action_scope within the TTL window.
        """
        now = time.time()
        candidates = []

        if ticket_id:
            try:
                ticket_file = os.path.join(self.tickets_dir, f"{uuid.UUID(ticket_id)}.json")
            except (ValueError, AttributeError):
                return False
            if os.path.exists(ticket_file):
                candidates.append(ticket_file)
        else:
            # Check environment variable first
            env_ticket = os.getenv("JUDGE_EXECUTION_TICKET")
            if env_ticket:
                ticket_file = os.path.join(self.tickets_dir, f"{env_ticket}.json")
                if os.path.exists(ticket_file):
                    candidates.append(ticket_file)

            # Check active ticket file in /tmp
            if os.path.exists(self.active_ticket_file):
                candidates.append(self.active_ticket_file)

            # Also check all recent ticket files
            try:
                files = [os.path.join(self.tickets_dir, f) for f in os.listdir(self.tickets_dir) if f.endswith(".json")]
                # Sort newest first
                files.sort(key=lambda p: os.path.getmtime(p), reverse=True)
                for f in files:
                    if f not in candidates:
                        candidates.append(f)
            except Exception:
                pass

        if not candidates:
            return False

        for file_path in candidates:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # 1. Check status
                if data.get("status") != "ACTIVE":
                    continue

                # 2. Check expiration
                expires_at = data.get("expires_at", 0)
                if now > expires_at:
                    data["status"] = "EXPIRED"
                    try:
                        with open(file_path, "w", encoding="utf-8") as f:
                            json.dump(data, f, indent=2)
                    except Exception:
                        pass
                    continue

                # 3. Check signature
                sign_base = f"{data['ticket_id']}|{data['action_hash']}|{data['created_at']}|{data['expires_at']}|{data['nonce']}"
                expected_sig = _sign_payload(self.secret, sign_base)
                if not hmac.compare_digest(data.get("signature", ""), expected_sig):
                    data["status"] = "INVALID_SIGNATURE"
                    try:
                        with open(file_path, "w", encoding="utf-8") as f:
                            json.dump(data, f, indent=2)
                    except Exception:
                        pass
                    continue

                # The visible action must be covered by the signed hash; otherwise
                # editing the JSON action could widen an otherwise valid ticket.
                expected_action_hash = hashlib.sha256(
                    data.get("action", "").strip().encode("utf-8")
                ).hexdigest()
                if not hmac.compare_digest(data.get("action_hash", ""), expected_action_hash):
                    continue

                # 4. Scope matching
                ticket_action = data.get("action", "")
                if not _matches_scope(ticket_action, action_scope):
                    continue

                # Valid ticket found! Consume it immediately.
                data["status"] = "CONSUMED"
                data["consumed_at"] = now
                try:
                    self._write_json_atomic(file_path, data)
                    # Also mark canonical ticket file if candidate was the active pointer
                    canonical = os.path.join(self.tickets_dir, f"{data['ticket_id']}.json")
                    if os.path.exists(canonical) and canonical != file_path:
                        self._write_json_atomic(canonical, data)
                    if file_path == self.active_ticket_file or os.path.exists(self.active_ticket_file):
                        os.remove(self.active_ticket_file)
                except OSError:
                    return False

                return True

            except Exception:
                continue

        return False


# Singleton convenience functions
_default_vault: Optional[TicketVault] = None


def get_ticket_vault() -> TicketVault:
    global _default_vault
    if _default_vault is None:
        _default_vault = TicketVault()
    return _default_vault


def require_ticket(
    action_scope: str,
    ticket_id: Optional[str] = None,
    vault: Optional[TicketVault] = None,
) -> bool:
    """
    Gatekeeper check: Call this at the start of any critical script or API call.
    Raises SecurityGateError if no valid ticket is found and consumed.
    """
    selected_vault = vault or get_ticket_vault()
    approved = selected_vault.verify_and_consume(action_scope, ticket_id)
    if not approved:
        raise PermissionError(
            f"🛑 JudgeGuard Security Gate: No valid, active execution ticket found for action '{action_scope}'. "
            "Execution blocked. You must obtain genuine approval from judge_guard.py before running."
        )
    return True
