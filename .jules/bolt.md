## 2026-04-05 - [Synchronous Disk I/O in MobileBridge]
**Learning:** Even small JSON writes (~1KB) to `app_config.json` can introduce spikes in latency during the critical path of `JudgeGuard.verify_action`. On some systems, synchronous disk I/O can take 10-50ms, which is significant when the target is sub-10ms for cached hits.
**Action:** Offload `MobileBridge.sync_state` to a single-worker `ThreadPoolExecutor`. Use a state snapshot (`copy()`) before serialization to prevent race conditions.

## 2026-04-06 - [Background Subprocess for SQLite Thread Safety]
**Learning:** Attempting to call `ResearchPipeline.sync_to_notion()` directly from a background thread in `JudgeGuard` caused `sqlite3.ProgrammingError` because the SQLite connection was created in the main thread. While `check_same_thread=False` is a workaround, it's brittle when using classes that don't expose their connection logic.
**Action:** Use a background `ThreadPoolExecutor` to run `subprocess.run(["python3", "research_pipeline.py", "--sync-notion"])`. This keeps database access isolated to the subprocess's own thread/process, ensuring safety while still providing ~95% latency reduction (127ms -> 5ms) for the main agent thread.
