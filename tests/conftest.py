import pytest
import os

CONFIG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "src", "mobile_app_pwa", "public", "app_config.json"
)

import json

CLEAN_BASELINE = {
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

    # Restore clean baseline content
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(CLEAN_BASELINE, f, indent=2)
        f.write("\n")
