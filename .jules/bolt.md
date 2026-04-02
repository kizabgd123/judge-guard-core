## 2026-03-29 - [PWA Polling Overhead]
**Learning:** Aggressive polling (500ms) with cache-busting and unconditional state updates leads to high CPU and battery drain on mobile devices, even when the UI state is static.
**Action:** Implement 'Smart Polling' by respecting 'document.visibilityState' and only updating state if the payload has changed.

## 2026-03-30 - [Redundant Multimedia Generation]
**Learning:** In a live multi-agent stream, agents often use similar or identical phrases and exhibit recurring moods. Generating fresh audio and images for every turn results in significant network overhead and latency (HF API calls can take seconds).
**Action:** Implement content-based caching in the MultimediaManager. Always check if the exact text or mood has been recently generated before hitting external APIs.

## 2026-04-02 - [Blocking I/O in Agent Loop]
**Learning:** Performing synchronous network I/O (like Notion API calls) within the core agent step logic creates a significant bottleneck that blocks subsequent parallelized tasks (like multimedia generation). Offloading these independent I/O tasks to background threads can reduce turn latency by ~50% without architectural changes.
**Action:** Use a `ThreadPoolExecutor` with `max_workers=1` for independent logging tasks to ensure they don't block the main execution flow while maintaining sequential integrity.
