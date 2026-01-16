---
name: mobile-vibe-coding
description: Skill for dynamically updating the Mobile PWA UI using "Vibe Coding" techniques.
version: 1.0.0
---

# 📱 Mobile Vibe Coding Skill

**Objective:** Allow agents to instantly update the Mobile PWA interface to prototype features, change content, or demonstrate flows.

## 🛠️ Tools & context

- **Configuration File:** `src/mobile_app_pwa/public/app_config.json`
- **Bridge Script:** `src/antigravity_core/mobile_bridge.py`
- **Frontend:** React PWA polling the config file.

## 📝 Workflow

### 1. Read Current State

Read the current configuration to understand what is displayed.

```python
from src.antigravity_core.mobile_bridge import bridge
print(bridge.get_state())
```

### 2. Update UI

Update the state dictionary. The bridge handles file synchronization.

```python
bridge.update_state({
    "title": "New Title",
    "content": "Updated content from Agent!",
    "theme": "dark" # (if supported)
})
```

### 3. Verify

Use the `browser_subagent` to check `http://localhost:5173` and confirm the changes are visible.

## 💡 Best Practices ("Vibe Coding")

- **Iterate Fast:** Make small changes and verify.
- **Use Components:** Inject dynamic components using the `components` list in the state.

  ```json
  "components": [
    {"type": "alert", "payload": "System Normal"},
    {"type": "button", "payload": "Click Me"}
  ]
  ```
