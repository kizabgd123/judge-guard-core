## 2026-03-29 - [PWA Polling Overhead]
**Learning:** Aggressive polling (500ms) with cache-busting and unconditional state updates leads to high CPU and battery drain on mobile devices, even when the UI state is static.
**Action:** Implement 'Smart Polling' by respecting 'document.visibilityState' and only updating state if the payload has changed.

## 2026-03-30 - [Redundant Multimedia Generation]
**Learning:** In a live multi-agent stream, agents often use similar or identical phrases and exhibit recurring moods. Generating fresh audio and images for every turn results in significant network overhead and latency (HF API calls can take seconds).
**Action:** Implement content-based caching in the MultimediaManager. Always check if the exact text or mood has been recently generated before hitting external APIs.

## 2026-03-31 - [Synchronous Notion API Bottleneck]
**Learning:** Synchronous network I/O (like Notion API calls) in the main agent loop creates a serial execution bottleneck. Even when other parts of the turn (like multimedia) are parallelized, the agent still waits for the database log to finish before proceeding to the next logical step.
**Action:** Offload side-effect logging to background threads using a `ThreadPoolExecutor`. This allows the agent to return immediately while the I/O happens asynchronously.

## 2026-04-03 - [O(N) Log Retrieval Anti-pattern]
**Learning:** Multiple components (LogStreamer, JudgeGuard) were reading entire growth-unbounded log files (WORK_LOG.md) into memory just to extract the tail. This causes linear performance degradation as the project progresses.
**Action:** Always use binary seek-from-end ('rb' with f.seek(0, 2)) for tail retrieval. Use 'errors=ignore' during decoding to safely handle potential UTF-8 character splits at the seek boundary.
