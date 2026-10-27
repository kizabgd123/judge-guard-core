"""
tests/test_rules_frontmatter.py
================================
Stvarni testovi za validaciju YAML frontmatter-a u .agents/rules/verification.md.

NEMA MOCK-OVA — čita stvarni fajl sa diska i parsira stvarni YAML.
"""

import os
import pytest

RULES_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    ".agents",
    "rules",
    "verification.md",
)

HOOKS_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    ".agents",
    "hooks.json",
)


def parse_frontmatter(filepath: str) -> dict:
    """
    Parsira YAML frontmatter iz markdown fajla.

    Args:
        filepath: Putanja do markdown fajla sa frontmatter-om.

    Returns:
        Dict sa parsiranim frontmatter podacima.

    Raises:
        ValueError: Ako frontmatter nije pronađen ili je neispravan.
    """
    import yaml

    with open(filepath, encoding="utf-8") as f:
        content = f.read()

    if not content.startswith("---"):
        raise ValueError(f"Frontmatter nije pronađen u {filepath}")

    parts = content.split("---", 2)
    if len(parts) < 3:
        raise ValueError(f"Neispravan frontmatter format u {filepath}")

    return yaml.safe_load(parts[1])


class TestRulesFileExists:
    """Verifikuje da rules fajl postoji."""

    def test_rules_file_exists(self):
        """verification.md mora postojati."""
        assert os.path.isfile(RULES_FILE), f"Rules fajl nije pronađen: {RULES_FILE}"

    def test_rules_file_not_empty(self):
        """verification.md ne sme biti prazan."""
        size = os.path.getsize(RULES_FILE)
        assert size > 0, "Rules fajl je prazan"

    def test_rules_file_under_24kb_limit(self):
        """Antigravity limit: max 24,000 bajtova po rules fajlu."""
        size = os.path.getsize(RULES_FILE)
        assert size < 24000, f"Rules fajl ({size} bajtova) premašuje Antigravity limit od 24KB"


class TestFrontmatterValid:
    """Verifikuje da je YAML frontmatter validan i ima ispravna polja."""

    def test_frontmatter_parseable(self):
        """Frontmatter mora biti validan YAML."""
        try:
            data = parse_frontmatter(RULES_FILE)
            assert isinstance(data, dict), "Frontmatter nije dict"
        except Exception as e:
            pytest.fail(f"Frontmatter parse greška: {e}")

    def test_trigger_field_exists(self):
        """Polje 'trigger' je obavezno u Antigravity rules."""
        data = parse_frontmatter(RULES_FILE)
        assert "trigger" in data, f"Nedostaje 'trigger' polje. Dostupna polja: {list(data.keys())}"

    def test_trigger_value_valid(self):
        """'trigger' mora biti jedan od dozvoljenih vrednosti."""
        valid_triggers = {"always_on", "model_decision", "glob", "manual"}
        data = parse_frontmatter(RULES_FILE)
        trigger = data["trigger"]
        assert trigger in valid_triggers, (
            f"Neispravan trigger '{trigger}'. Dozvoljeni: {valid_triggers}"
        )

    def test_trigger_is_always_on(self):
        """Za verifikaciona pravila, trigger MORA biti always_on."""
        data = parse_frontmatter(RULES_FILE)
        assert data["trigger"] == "always_on", (
            f"Verifikaciono pravilo mora imati trigger=always_on, ali ima: {data['trigger']}"
        )

    def test_description_field_exists(self):
        """Polje 'description' je preporučeno za sva pravila."""
        data = parse_frontmatter(RULES_FILE)
        assert "description" in data, "Nedostaje 'description' polje u frontmatter-u"
        assert len(data["description"]) > 10, "Description je prekratak"


class TestHooksFileValid:
    """Verifikuje da je .agents/hooks.json validan JSON."""

    def test_hooks_file_exists(self):
        """hooks.json mora postojati."""
        assert os.path.isfile(HOOKS_FILE), f"Hooks fajl nije pronađen: {HOOKS_FILE}"

    def test_hooks_file_valid_json(self):
        """hooks.json mora biti validan JSON."""
        import json
        try:
            with open(HOOKS_FILE, encoding="utf-8") as f:
                data = json.load(f)
            assert isinstance(data, dict), "hooks.json mora biti JSON objekat"
        except json.JSONDecodeError as e:
            pytest.fail(f"hooks.json nije validan JSON: {e}")

    def test_hooks_has_enabled_guard(self):
        """hooks.json mora imati bar jedan enabled guard."""
        import json
        with open(HOOKS_FILE, encoding="utf-8") as f:
            data = json.load(f)

        enabled_guards = [k for k, v in data.items() if v.get("enabled") is True]
        assert len(enabled_guards) > 0, "Nema ni jednog enabled guard-a u hooks.json"

    def test_hooks_has_pre_tool_use(self):
        """Mora postojati bar jedan PreToolUse hook."""
        import json
        with open(HOOKS_FILE, encoding="utf-8") as f:
            data = json.load(f)

        has_pre = any("PreToolUse" in v for v in data.values() if isinstance(v, dict))
        assert has_pre, "Nema PreToolUse hook-a u hooks.json"

    def test_hooks_run_command_matcher(self):
        """PreToolUse mora imati matcher za 'run_command'."""
        import json
        with open(HOOKS_FILE, encoding="utf-8") as f:
            data = json.load(f)

        matchers = []
        for guard in data.values():
            if isinstance(guard, dict) and "PreToolUse" in guard:
                for entry in guard["PreToolUse"]:
                    matchers.append(entry.get("matcher", ""))

        assert "run_command" in matchers, (
            f"Nema 'run_command' matcher-a u PreToolUse. Dostupni: {matchers}"
        )
