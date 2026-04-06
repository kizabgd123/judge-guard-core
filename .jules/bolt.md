## 2026-04-05 - [Synchronous Disk I/O in MobileBridge]
**Learning:** Even small JSON writes (~1KB) to `app_config.json` can introduce spikes in latency during the critical path of `JudgeGuard.verify_action`. On some systems, synchronous disk I/O can take 10-50ms, which is significant when the target is sub-10ms for cached hits.
**Action:** Offload `MobileBridge.sync_state` to a single-worker `ThreadPoolExecutor`. Use a state snapshot (`copy()`) before serialization to prevent race conditions.

## 2026-04-06 - [Sequential API Calls in GuardianAgent]
**Learning:** `GuardianAgent.process_logs` was performing sequential Gemini and Notion API calls (0.5s + 0.2s = 0.7s per log). This created a significant bottleneck as the number of logs grew, leading to $O(N)$ scaling.
**Action:** Parallelized `process_logs` using `ThreadPoolExecutor(max_workers=5)`, reducing total execution time for 5 logs by ~80% (from 3.5s to 0.7s) as verified by `tests/benchmark_guardian.py`.
