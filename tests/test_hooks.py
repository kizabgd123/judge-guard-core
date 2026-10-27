"""
tests/test_hooks.py
===================
Stvarni testovi za verify_command_safety.py hook skriptu.

NEMA MOCK-OVA za bezbednosne kapije ili sistemske komande.
Testira stvarnu logiku skripte direktnim pozivom subprocess-a sa stdin payload-om.
"""

import json
import subprocess
import sys
import os
import pytest

# Putanja do hook skripte
HOOK_SCRIPT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "scripts",
    "verify_command_safety.py",
)


def run_hook(payload: dict) -> subprocess.CompletedProcess:
    """
    Pokreće verify_command_safety.py sa datim payload-om na stdin.

    Args:
        payload: Dict koji se serijalizuje kao JSON i šalje na stdin.

    Returns:
        CompletedProcess sa returncode, stdout i stderr.
    """
    return subprocess.run(
        [sys.executable, HOOK_SCRIPT],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        timeout=10,
    )


class TestHookScriptExists:
    """Verifikuje da hook skripta postoji i može se pokrenuti."""

    def test_script_file_exists(self):
        """Hook skripta mora postojati na očekivanoj putanji."""
        assert os.path.isfile(HOOK_SCRIPT), f"Hook skripta nije pronađena: {HOOK_SCRIPT}"

    def test_script_is_executable_python(self):
        """Skripta mora biti validan Python modul (može se importovati)."""
        result = subprocess.run(
            [sys.executable, "-m", "py_compile", HOOK_SCRIPT],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Sintaksna greška u skripti: {result.stderr}"


class TestSafeCommands:
    """Bezbedne komande moraju proći (Exit Code 0)."""

    def test_git_status_passes(self):
        payload = {"tool_name": "run_command", "tool_input": {"CommandLine": "git status"}}
        result = run_hook(payload)
        assert result.returncode == 0, f"git status blokiran: {result.stderr}"

    def test_pytest_passes(self):
        payload = {"tool_name": "run_command", "tool_input": {"CommandLine": "pytest tests/ -v"}}
        result = run_hook(payload)
        assert result.returncode == 0, f"pytest blokiran: {result.stderr}"

    def test_ls_passes(self):
        payload = {"tool_name": "run_command", "tool_input": {"CommandLine": "ls -la"}}
        result = run_hook(payload)
        assert result.returncode == 0, f"ls blokiran: {result.stderr}"

    def test_cat_file_passes(self):
        payload = {"tool_name": "run_command", "tool_input": {"CommandLine": "cat WORK_LOG.md"}}
        result = run_hook(payload)
        assert result.returncode == 0, f"cat blokiran: {result.stderr}"

    def test_npm_test_passes(self):
        payload = {"tool_name": "run_command", "tool_input": {"CommandLine": "npm test"}}
        result = run_hook(payload)
        assert result.returncode == 0, f"npm test blokiran: {result.stderr}"

    def test_empty_stdin_is_blocked(self):
        """Prazan stdin ne sme zaobići sigurnosni hook."""
        result = subprocess.run(
            [sys.executable, HOOK_SCRIPT],
            input="",
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 1, "Prazan stdin je zaobišao sigurnosni hook"

    def test_invalid_json_is_blocked(self):
        """Neispravan JSON ne sme zaobići sigurnosni hook."""
        result = subprocess.run(
            [sys.executable, HOOK_SCRIPT],
            input="not json at all",
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 1, "Neispravan JSON je zaobišao sigurnosni hook"

    def test_unrecognized_payload_is_blocked(self):
        result = run_hook({"tool_name": "run_command", "tool_input": {"other": "value"}})
        assert result.returncode == 1, "Nepoznat format payload-a je zaobišao sigurnosni hook"


class TestDangerousCommands:
    """Opasne komande moraju biti blokirane (Exit Code 1)."""

    def test_rm_rf_root_blocked(self):
        payload = {"tool_name": "run_command", "tool_input": {"CommandLine": "rm -rf /"}}
        result = run_hook(payload)
        assert result.returncode == 1, "rm -rf / NIJE blokiran — kritična bezbednosna greška!"
        assert "BLOCKED" in result.stderr, "Hook nije ispisao poruku o blokiranju"

    def test_rm_rf_home_blocked(self):
        payload = {"tool_name": "run_command", "tool_input": {"CommandLine": "rm -rf ~"}}
        result = run_hook(payload)
        assert result.returncode == 1, "rm -rf ~ NIJE blokiran"

    def test_mkfs_blocked(self):
        payload = {"tool_name": "run_command", "tool_input": {"CommandLine": "mkfs.ext4 /dev/sda"}}
        result = run_hook(payload)
        assert result.returncode == 1, "mkfs NIJE blokiran"

    def test_dd_zero_blocked(self):
        payload = {
            "tool_name": "run_command",
            "tool_input": {"CommandLine": "dd if=/dev/zero of=/dev/sda"},
        }
        result = run_hook(payload)
        assert result.returncode == 1, "dd if=/dev/zero NIJE blokiran"

    def test_sudo_rm_rf_blocked(self):
        payload = {
            "tool_name": "run_command",
            "tool_input": {"CommandLine": "sudo rm -rf /etc"},
        }
        result = run_hook(payload)
        assert result.returncode == 1, "sudo rm -rf NIJE blokiran"

    def test_drop_table_blocked(self):
        payload = {
            "tool_name": "run_command",
            "tool_input": {"CommandLine": "psql -c 'DROP TABLE users'"},
        }
        result = run_hook(payload)
        assert result.returncode == 1, "DROP TABLE NIJE blokiran"

    @pytest.mark.parametrize("command", [
        "rm -rf /*",
        "rm -r -f -- /",
        "rm -rf ~/important/*",
        "chmod -R 777 /srv/app",
    ])
    def test_root_and_recursive_permission_changes_blocked(self, command):
        result = run_hook({"tool_name": "run_command", "tool_input": {"CommandLine": command}})
        assert result.returncode == 1, f"Destructive command was not blocked: {command}"

    @pytest.mark.parametrize("command", ["rm -rf ./build", "chmod -R 755 ./scripts"])
    def test_scoped_cleanup_and_permission_changes_are_allowed(self, command):
        result = run_hook({"tool_name": "run_command", "tool_input": {"CommandLine": command}})
        assert result.returncode == 0, f"Scoped command was unexpectedly blocked: {command}"


class TestAlternativePayloadFormats:
    """Testira različite formate payload-a koje Antigravity može slati."""

    def test_toolcall_format_safe(self):
        """Antigravity 'toolCall.args' format — bezbedna komanda."""
        payload = {
            "toolCall": {
                "args": {"CommandLine": "git diff HEAD"}
            }
        }
        result = run_hook(payload)
        assert result.returncode == 0, f"toolCall format blokiran za bezbednu komandu: {result.stderr}"

    def test_toolcall_format_dangerous(self):
        """Antigravity 'toolCall.args' format — opasna komanda."""
        payload = {
            "toolCall": {
                "args": {"CommandLine": "rm -rf /"}
            }
        }
        result = run_hook(payload)
        assert result.returncode == 1, "toolCall format nije blokiran za rm -rf /"
