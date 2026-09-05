import pytest
import os

CONFIG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "src", "mobile_app_pwa", "public", "app_config.json"
)

CLEAN_CONFIG = '{\n  "title": "Antigravity Mobile",\n  "theme": "light",\n  "content": "Welcome to the Agent-Controlled PWA!",\n  "components": []\n}\n'

@pytest.fixture(scope="session", autouse=True)
def restore_app_config():
    yield

    # Ensure all background thread writes are complete
    try:
        from src.antigravity_core.mobile_bridge import bridge
        if hasattr(bridge, "_executor") and bridge._executor is not None:
            bridge._executor.shutdown(wait=True)
            bridge._executor = None
        bridge.app_state = {
            "title": "Antigravity Mobile",
            "theme": "light",
            "content": "Welcome to the Agent-Controlled PWA!",
            "components": []
        }
    except ImportError:
        # Expected when bridge is not available
        pass

    # Always restore clean 4-key baseline content
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        f.write(CLEAN_CONFIG)
