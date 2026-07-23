import pytest
import json
import os

CONFIG_FILE = os.path.join("src", "mobile_app_pwa", "public", "app_config.json")

@pytest.fixture(scope="session", autouse=True)
def clean_pwa_config():
    # Save original content
    original_content = None
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                original_content = f.read()
        except Exception:
            pass

    yield

    # Restore original content or baseline
    if original_content is not None:
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                f.write(original_content)
        except Exception:
            pass
    else:
        # If config file didn't exist, remove it, or restore to baseline
        baseline = {
          "title": "Antigravity Mobile",
          "theme": "light",
          "content": "Welcome to the Agent-Controlled PWA!",
          "components": []
        }
        try:
            os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(baseline, f, indent=2)
                f.write("\n")
        except Exception:
            pass
