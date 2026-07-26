import os
import pytest

CONFIG_PATH = "src/mobile_app_pwa/public/app_config.json"

@pytest.fixture(scope="session", autouse=True)
def preserve_app_config():
    """
    Session-scoped autouse fixture to capture and restore the pristine content of
    src/mobile_app_pwa/public/app_config.json, ensuring any background writes or side-effects
    from tests do not persist or break the frontend Vitest suite.
    """
    original_content = None
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                original_content = f.read()
        except Exception:
            pass

    yield

    if original_content is not None:
        try:
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                f.write(original_content)
        except Exception:
            pass
