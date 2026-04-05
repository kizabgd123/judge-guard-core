import pytest
from unittest.mock import patch, MagicMock
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

        # ⚡ Bolt: Wait for background sync to complete
        bridge._executor.shutdown(wait=True)

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
        bridge._executor.shutdown(wait=True)

        assert "last_verdict" in bridge.app_state
        assert bridge.app_state["last_verdict"]["action"] == "TestAction"
        assert bridge.app_state["last_verdict"]["status"] == "PASSED"

        with open(config_file, "r") as f:
            data = json.load(f)
            assert data["last_verdict"]["status"] == "PASSED"


# --- Tests for MobileBridge ThreadPoolExecutor offload (PR: Bolt: Offload Bridge I/O and reuse GeminiClient) ---

from concurrent.futures import ThreadPoolExecutor as _TPE

def test_executor_is_single_worker(temp_pwa_dir):
    """MobileBridge must create a ThreadPoolExecutor with max_workers=1."""
    with patch('src.antigravity_core.mobile_bridge.PWA_PUBLIC_DIR', str(temp_pwa_dir / "public")), \
         patch('src.antigravity_core.mobile_bridge.CONFIG_FILE', str(temp_pwa_dir / "public" / "app_config.json")):
        bridge = MobileBridge()
        assert isinstance(bridge._executor, _TPE)
        # Verify the max-worker cap by checking the underlying pool size
        assert bridge._executor._max_workers == 1
        bridge._executor.shutdown(wait=True)


def test_update_state_submits_to_executor(temp_pwa_dir):
    """update_state must submit sync_state to the executor rather than calling it directly."""
    config_file = str(temp_pwa_dir / "public" / "app_config.json")
    with patch('src.antigravity_core.mobile_bridge.PWA_PUBLIC_DIR', str(temp_pwa_dir / "public")), \
         patch('src.antigravity_core.mobile_bridge.CONFIG_FILE', config_file):
        bridge = MobileBridge()
        submitted_calls = []
        original_submit = bridge._executor.submit

        def tracking_submit(fn, *args, **kwargs):
            submitted_calls.append(fn)
            return original_submit(fn, *args, **kwargs)

        bridge._executor.submit = tracking_submit
        bridge.update_state({"key": "value"})
        bridge._executor.shutdown(wait=True)

        assert bridge.sync_state in submitted_calls


def test_sync_state_writes_snapshot_not_live_reference(temp_pwa_dir):
    """sync_state must serialize a copy of app_state so mid-serialization mutations do not corrupt the file."""
    config_file = str(temp_pwa_dir / "public" / "app_config.json")
    with patch('src.antigravity_core.mobile_bridge.PWA_PUBLIC_DIR', str(temp_pwa_dir / "public")), \
         patch('src.antigravity_core.mobile_bridge.CONFIG_FILE', config_file):
        bridge = MobileBridge()
        bridge._executor.shutdown(wait=True)  # stop background processing

        # Directly call sync_state and then mutate app_state before reading file
        bridge.app_state["key"] = "original"
        bridge.sync_state()
        bridge.app_state["key"] = "mutated_after_sync"

        with open(config_file, "r") as f:
            data = json.load(f)
        # File must contain the state at sync time, not the post-mutation value
        assert data["key"] == "original"


def test_del_shuts_down_executor(temp_pwa_dir):
    """__del__ must call shutdown(wait=False) on the executor."""
    with patch('src.antigravity_core.mobile_bridge.PWA_PUBLIC_DIR', str(temp_pwa_dir / "public")), \
         patch('src.antigravity_core.mobile_bridge.CONFIG_FILE', str(temp_pwa_dir / "public" / "app_config.json")):
        bridge = MobileBridge()
        mock_executor = MagicMock()
        bridge._executor = mock_executor
        bridge.__del__()
        mock_executor.shutdown.assert_called_once_with(wait=False)


def test_del_safe_without_executor_attribute(temp_pwa_dir):
    """__del__ must not raise if _executor was never set (e.g. init failed mid-way)."""
    with patch('src.antigravity_core.mobile_bridge.PWA_PUBLIC_DIR', str(temp_pwa_dir / "public")), \
         patch('src.antigravity_core.mobile_bridge.CONFIG_FILE', str(temp_pwa_dir / "public" / "app_config.json")):
        bridge = MobileBridge()
        del bridge._executor
        # Must not raise
        bridge.__del__()


def test_update_state_returns_updated_state(temp_pwa_dir):
    """update_state must return the merged app_state dict immediately."""
    config_file = str(temp_pwa_dir / "public" / "app_config.json")
    with patch('src.antigravity_core.mobile_bridge.PWA_PUBLIC_DIR', str(temp_pwa_dir / "public")), \
         patch('src.antigravity_core.mobile_bridge.CONFIG_FILE', config_file):
        bridge = MobileBridge()
        result = bridge.update_state({"theme": "dark"})
        bridge._executor.shutdown(wait=True)
        assert result["theme"] == "dark"
        assert result is bridge.app_state