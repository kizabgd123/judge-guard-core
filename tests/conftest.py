import pytest
import shutil
import os

@pytest.fixture(scope="session", autouse=True)
def preserve_app_config():
    config_path = "src/mobile_app_pwa/public/app_config.json"
    backup_path = "src/mobile_app_pwa/public/app_config.json.bak"

    # Back up the original configuration before any tests run
    has_backup = False
    if os.path.exists(config_path):
        shutil.copy2(config_path, backup_path)
        has_backup = True

    yield

    # Restore the original configuration after the entire test session completes
    if has_backup and os.path.exists(backup_path):
        shutil.copy2(backup_path, config_path)
        os.remove(backup_path)
