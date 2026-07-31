import pytest
import json
import os

CONFIG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "src", "mobile_app_pwa", "public", "app_config.json"
)

@pytest.fixture(scope="session", autouse=True)
def maintain_app_config_baseline():
    # Read and backup original content
    original_content = None
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                original_content = f.read()
        except Exception:
            pass

    yield

    # Restore original content after the session
    if original_content is not None:
        try:
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                f.write(original_content)
        except Exception:
            pass
