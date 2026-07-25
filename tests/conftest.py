import pytest
import os

@pytest.fixture(scope="session", autouse=True)
def restore_app_config():
    config_path = "src/mobile_app_pwa/public/app_config.json"
    original_content = None
    if os.path.exists(config_path):
        try:
            with open(config_path, "r") as f:
                original_content = f.read()
        except Exception:
            pass

    yield

    if original_content is not None:
        try:
            with open(config_path, "w") as f:
                f.write(original_content)
        except Exception:
            pass
