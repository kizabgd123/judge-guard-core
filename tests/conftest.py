import pytest
import os
import json

CONFIG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "src", "mobile_app_pwa", "public", "app_config.json"
)

BASELINE_CONFIG = {
    "title": "Antigravity Mobile",
    "theme": "light",
    "content": "Welcome to the Agent-Controlled PWA!",
    "components": []
}

@pytest.fixture(scope="session", autouse=True)
def restore_app_config():
    yield

    # Ensure all background thread writes are complete
    try:
        from src.antigravity_core.mobile_bridge import bridge
        if hasattr(bridge, "_executor") and bridge._executor is not None:
            bridge._executor.shutdown(wait=True)
            bridge._executor = None
    except ImportError:
        # Expected when bridge is not available
        pass

    # Always restore baseline config
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(BASELINE_CONFIG, f, indent=2)
