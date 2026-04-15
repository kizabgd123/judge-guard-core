## 2026-04-05 - [Synchronous Disk I/O in MobileBridge]
**Learning:** Even small JSON writes (~1KB) to `app_config.json` can introduce spikes in latency during the critical path of `JudgeGuard.verify_action`. On some systems, synchronous disk I/O can take 10-50ms, which is significant when the target is sub-10ms for cached hits.
**Action:** Offload `MobileBridge.sync_state` to a single-worker `ThreadPoolExecutor`. Use a state snapshot (`copy()`) before serialization to prevent race conditions.

## 2026-04-07 - [Process Overhead in Notion Synchronization]
**Learning:** Using `subprocess.run` to call an external script (`research_pipeline.py`) for Notion synchronization introduces ~300ms of overhead per call. This is particularly wasteful when the parent process already has an initialized instance of the required class (`ResearchPipeline`) and the synchronization task is I/O-bound.
**Action:** Refactor `JudgeGuard` to reuse the existing `ResearchPipeline` instance for synchronization. Offload the `sync_to_notion` call to a background `ThreadPoolExecutor` to remove synchronization latency from the main verification path, reducing total turn-around time by >90% for cached actions.

## 2026-04-10 - [Parallelization and Connection Pooling in ResearchPipeline]
**Learning:** Sequential HTTP POST requests in `ResearchPipeline.sync_to_notion` create a significant bottleneck, especially when batching multiple audit entries. Using `requests.Session` for connection pooling and `ThreadPoolExecutor.map` for parallelizing I/O-bound API calls reduces latency by ~70-80% (from ~1.12s to ~0.31s for 11 entries).
**Action:** Implement a persistent `self.session` and `self._executor` in classes performing batch API calls. Always include a `close()` method for clean resource teardown.

## 2026-04-12 - [Redundant Auditing in Cache Hot-Path]
**Learning:** Performing a synchronous database write (audit log) on every read-only cache hit in `ResearchPipeline.get_cached_verdict` introduces ~2.5ms of overhead, which is ~100x the latency of the actual SQLite lookup (~0.02ms). This negates much of the "fast path" benefit of caching and creates noise in Notion.
**Action:** Avoid synchronous I/O or state mutations in cache retrieval methods. If auditing is required for hits, offload it to a background thread or use a lower-frequency sampling method.

## 2026-04-15 - [Incremental Extraction with SQLite RETURNING]
**Learning:** In pipelines where data parsing is followed by secondary extraction (e.g., Markdown -> Docs -> Patterns), re-processing the entire database on every update is a significant $O(N)$ bottleneck. Using the SQLite `RETURNING id` clause during upserts allows for precise tracking of modified records in a single atomic step.
**Action:** Implement a "Targeted extraction" pattern where the parsing layer returns a list of affected IDs, and the extraction layer accepts an optional filter for those IDs. This reduces warm-run processing time from $O(N)$ to $O(\text{modified})$, which is often a 10-100x speedup for typical updates.
