import pytest
import os

CONFIG_PATH = "src/mobile_app_pwa/public/app_config.json"

@pytest.fixture(scope="session", autouse=True)
def preserve_app_config():
    # Read and save the original content
    original_content = None
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                original_content = f.read()
        except Exception:
            pass

    yield

    # Restore the original content after all tests finish
    if original_content is not None:
        try:
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                f.write(original_content)
        except Exception:
            pass
