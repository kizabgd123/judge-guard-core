import time
from typing import Dict

# Old implementation
def old_get_title(page: Dict) -> str:
    try:
        props = page["properties"]
        title_prop = next((v for k,v in props.items() if v["id"] == "title"), None)
        if title_prop and title_prop["title"]:
            return title_prop["title"][0]["text"]["content"]

        entry = props.get("Entry", {}).get("rich_text", [])
        if entry:
            return entry[0]["text"]["content"]

        return "Untitled"
    except Exception:
        return "Error extracting title"

# New implementation
def new_get_title(page: Dict) -> str:
    try:
        props = page.get("properties", {})
        if not props:
            return "Untitled"

        # 1. First priority: look for the property with id == "title"
        title_prop = None

        # Fast-path O(1) check for common keys with id == "title"
        for key in ("Name", "Title"):
            prop = props.get(key)
            if isinstance(prop, dict) and prop.get("id") == "title":
                title_prop = prop
                break

        # Fallback to linear search for id == "title" if fast-path keys didn't match
        if title_prop is None:
            for prop in props.values():
                if isinstance(prop, dict) and prop.get("id") == "title":
                    title_prop = prop
                    break

        # Extract content if title property exists and has entries
        if title_prop is not None:
            title_list = title_prop.get("title")
            if title_list:
                return title_list[0]["text"]["content"]

        # 2. Second priority: fallback for 'Entry' property if it's a Rich Text, not Title
        entry_prop = props.get("Entry")
        if isinstance(entry_prop, dict):
            entry = entry_prop.get("rich_text", [])
            if entry:
                return entry[0]["text"]["content"]

        return "Untitled"
    except Exception:
        return "Error extracting title"

# Run comparison
log_page = {"id": "log1", "properties": {"Entry": {"title": [{"text": {"content": "This is a log entry description."}}]}}}
goal_page = {"id": "goal1", "properties": {"Name": {"title": [{"text": {"content": "This is a goal name description."}}]}}}

print("--- Microbenchmarking Title Extraction (100,000 iterations) ---")

start = time.time()
for _ in range(100000):
    old_get_title(log_page)
    old_get_title(goal_page)
duration_old = time.time() - start
print(f"Old _get_title duration: {duration_old:.4f}s")

start = time.time()
for _ in range(100000):
    new_get_title(log_page)
    new_get_title(goal_page)
duration_new = time.time() - start
print(f"New _get_title duration: {duration_new:.4f}s")

speedup = duration_old / duration_new
reduction = (1 - (duration_new / duration_old)) * 100
print(f"Speedup: {speedup:.2f}x (~{reduction:.1f}% reduction in latency)")
