## 2026-04-05 - [Synchronous Disk I/O in MobileBridge]
**Learning:** Even small JSON writes (~1KB) to `app_config.json` can introduce spikes in latency during the critical path of `JudgeGuard.verify_action`. On some systems, synchronous disk I/O can take 10-50ms, which is significant when the target is sub-10ms for cached hits.
**Action:** Offload `MobileBridge.sync_state` to a single-worker `ThreadPoolExecutor`. Use a state snapshot (`copy()`) before serialization to prevent race conditions.

## 2026-04-07 - [Process Overhead in Notion Synchronization]
**Learning:** Using `subprocess.run` to call an external script (`research_pipeline.py`) for Notion synchronization introduces ~300ms of overhead per call. This is particularly wasteful when the parent process already has an initialized instance of the required class (`ResearchPipeline`) and the synchronization task is I/O-bound.
**Action:** Refactor `JudgeGuard` to reuse the existing `ResearchPipeline` instance for synchronization. Offload the `sync_to_notion` call to a background `ThreadPoolExecutor` to remove synchronization latency from the main verification path, reducing total turn-around time by >90% for cached actions.

## 2026-04-10 - [Aggressive Token Truncation in LLM Responses]
**Learning:** Setting `max_output_tokens` to an extremely low value (e.g., 10) for LLM calls that return structured data (like JSON or even simple classification verdicts) can lead to truncated responses and subsequent parsing errors. This is a "breaking" micro-optimization that negates the performance benefit by causing functional failure.
**Action:** When using `generation_config` to limit tokens, always set a safe upper bound based on the maximum expected length of the valid response (e.g., 50 for classification, 150-250 for short JSON) to ensure reliability while still limiting tail-end latency from model verbosity.
