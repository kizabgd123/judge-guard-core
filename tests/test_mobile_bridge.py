import pytest
from unittest.mock import patch
import os
import json
import shutil
from src.antigravity_core.mobile_bridge import MobileBridge

@pytest.fixture
def temp_pwa_dir(tmp_path):
    pwa_dir = tmp_path / "mobile_app_pwa"
    public_dir = pwa_dir / "public"
    public_dir.mkdir(parents=True)
    return pwa_dir

def test_mobile_bridge_init(temp_pwa_dir, monkeypatch):
    # Set the base directory for MobileBridge to find the public dir relative to its own path
    # MobileBridge uses os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # We'll mock the module level constant or just test the logic with a fresh instance

    with patch('src.antigravity_core.mobile_bridge.PWA_PUBLIC_DIR', str(temp_pwa_dir / "public")), \
         patch('src.antigravity_core.mobile_bridge.CONFIG_FILE', str(temp_pwa_dir / "public" / "app_config.json")):

        bridge = MobileBridge()
        assert bridge.app_state["title"] == "Antigravity Mobile"
        assert os.path.exists(str(temp_pwa_dir / "public" / "app_config.json"))

def test_update_state(temp_pwa_dir):
    config_file = str(temp_pwa_dir / "public" / "app_config.json")
    with patch('src.antigravity_core.mobile_bridge.PWA_PUBLIC_DIR', str(temp_pwa_dir / "public")), \
         patch('src.antigravity_core.mobile_bridge.CONFIG_FILE', config_file):

        bridge = MobileBridge()
        bridge.update_state({"theme": "dark", "content": "Updated content"})

        assert bridge.app_state["theme"] == "dark"
        assert bridge.app_state["content"] == "Updated content"

        with open(config_file, "r") as f:
            data = json.load(f)
            assert data["theme"] == "dark"
            assert data["content"] == "Updated content"

def test_push_verdict(temp_pwa_dir):
    config_file = str(temp_pwa_dir / "public" / "app_config.json")
    with patch('src.antigravity_core.mobile_bridge.PWA_PUBLIC_DIR', str(temp_pwa_dir / "public")), \
         patch('src.antigravity_core.mobile_bridge.CONFIG_FILE', config_file):

        bridge = MobileBridge()
        bridge.push_verdict("TestAction", "PASSED", "All good")

        assert "last_verdict" in bridge.app_state
        assert bridge.app_state["last_verdict"]["action"] == "TestAction"
        assert bridge.app_state["last_verdict"]["status"] == "PASSED"

        with open(config_file, "r") as f:
            data = json.load(f)
            assert data["last_verdict"]["status"] == "PASSED"
