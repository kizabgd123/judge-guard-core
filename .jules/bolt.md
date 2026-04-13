## 2026-04-05 - [Synchronous Disk I/O in MobileBridge]
**Learning:** Even small JSON writes (~1KB) to `app_config.json` can introduce spikes in latency during the critical path of `JudgeGuard.verify_action`. On some systems, synchronous disk I/O can take 10-50ms, which is significant when the target is sub-10ms for cached hits.
**Action:** Offload `MobileBridge.sync_state` to a single-worker `ThreadPoolExecutor`. Use a state snapshot (`copy()`) before serialization to prevent race conditions.

## 2026-04-07 - [Process Overhead in Notion Synchronization]
**Learning:** Using `subprocess.run` to call an external script (`research_pipeline.py`) for Notion synchronization introduces ~300ms of overhead per call. This is particularly wasteful when the parent process already has an initialized instance of the required class (`ResearchPipeline`) and the synchronization task is I/O-bound.
**Action:** Refactor `JudgeGuard` to reuse the existing `ResearchPipeline` instance for synchronization. Offload the `sync_to_notion` call to a background `ThreadPoolExecutor` to remove synchronization latency from the main verification path, reducing total turn-around time by >90% for cached actions.

## 2026-04-10 - [Parallel Notion Sync with Connection Pooling]
**Learning:** Sequential HTTP requests to the Notion API for batch synchronization introduce significant linear latency (~100ms+ per entry). This becomes a major bottleneck when syncing multiple audit logs. Using `requests.Session` for connection pooling and `ThreadPoolExecutor` for parallelized requests reduces total latency from $O(N)$ to approximately $O(N/workers)$.
**Action:** Implement `requests.Session` and `ThreadPoolExecutor` in classes handling batch API calls (e.g., `ResearchPipeline`). Use `list(executor.map(...))` for parallel execution and ensure an explicit `close()` method is called for resource cleanup.
