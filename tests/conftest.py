import pytest
import os

CONFIG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "src", "mobile_app_pwa", "public", "app_config.json"
)

@pytest.fixture(scope="session", autouse=True)
def restore_app_config():
    # Capture original content
    original_content = None
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            original_content = f.read()

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

    # Restore original content
    if original_content is not None:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            f.write(original_content)
