import pytest
from unittest.mock import patch
import os
import json
import shutil
import time
from src.antigravity_core.mobile_bridge import MobileBridge

@pytest.fixture
def temp_pwa_dir(tmp_path):
    pwa_dir = tmp_path / "mobile_app_pwa"
    public_dir = pwa_dir / "public"
    public_dir.mkdir(parents=True)
    return pwa_dir

def test_mobile_bridge_init(temp_pwa_dir):
    # Mock paths
    public_dir = str(temp_pwa_dir / "public")
    config_file = str(temp_pwa_dir / "public" / "app_config.json")

    with patch('src.antigravity_core.mobile_bridge.PWA_PUBLIC_DIR', public_dir), \
         patch('src.antigravity_core.mobile_bridge.CONFIG_FILE', config_file):

        bridge = MobileBridge()
        assert bridge.app_state["title"] == "Antigravity Mobile"

        # In lazy mode, __init__ doesn't sync. We trigger it manually for the test or wait for update.
        bridge.sync_state()
        assert os.path.exists(config_file)

def test_update_state(temp_pwa_dir):
    config_file = str(temp_pwa_dir / "public" / "app_config.json")
    with patch('src.antigravity_core.mobile_bridge.PWA_PUBLIC_DIR', str(temp_pwa_dir / "public")), \
         patch('src.antigravity_core.mobile_bridge.CONFIG_FILE', config_file):

        bridge = MobileBridge()
        bridge.update_state({"theme": "dark", "content": "Updated content"})

        # ⚡ Bolt: Wait for background sync to complete
        bridge.executor.shutdown(wait=True)

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

        # ⚡ Bolt: Wait for background sync to complete
        bridge.executor.shutdown(wait=True)

        assert "last_verdict" in bridge.app_state
        assert bridge.app_state["last_verdict"]["action"] == "TestAction"
        assert bridge.app_state["last_verdict"]["status"] == "PASSED"

        with open(config_file, "r") as f:
            data = json.load(f)
            assert data["last_verdict"]["status"] == "PASSED"
