import pytest
import os
import json

CONFIG_PATH = "src/mobile_app_pwa/public/app_config.json"

@pytest.fixture(scope="session", autouse=True)
def restore_app_config():
    """Autouse fixture to backup and restore app_config.json to prevent test pollution."""
    backup = None
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                backup = f.read()
        except Exception:
            pass

    yield

    if backup is not None:
        try:
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                f.write(backup)
        except Exception:
            pass
