import pytest
import json
import os

@pytest.fixture(scope="session", autouse=True)
def restore_app_config():
    config_path = "src/mobile_app_pwa/public/app_config.json"

    # Store original contents
    original_content = None
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            original_content = f.read()

    yield

    # Restore original contents
    if original_content is not None:
        with open(config_path, "w") as f:
            f.write(original_content)
