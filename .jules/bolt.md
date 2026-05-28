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

## 2026-04-16 - [Process Overhead and Lazy Loading]
**Learning:** For high-frequency CLI tools like `JudgeGuard`, the cost of importing heavy libraries (e.g., `google-generativeai` at ~0.53s, `requests` at ~0.16s) can dominate the total execution time, especially on "hot paths" like cache hits that take <1ms. This process overhead creates a poor user experience.
**Action:** Use lazy loading for heavy dependencies. Move imports into method scopes or use @property-based lazy initialization. This reduced `JudgeGuard` CLI startup for cached verdicts by ~89% (from ~1.0s to ~0.11s).

## 2026-04-18 - [Redundant String Decoding in Hashing and Regex Passes]
**Learning:** For bulk file processing (e.g., 1000+ files), the overhead of decoding bytes to UTF-8 strings for hashing is significant (~30-40% of total time). Similarly, performing multiple regex passes ( then  in a loop) creates O(N_matches * N_doc) complexity.
**Action:** Use `read_bytes()` for hashing and defer `.decode()` until changes are confirmed. Use `re.finditer()` with pre-compiled regexes for single-pass extraction to achieve ~70% speedup in semantic processing.

## 2026-04-18 - [Redundant String Decoding in Hashing and Regex Passes]
**Learning:** For bulk file processing (e.g., 1000+ files), the overhead of decoding bytes to UTF-8 strings for hashing is significant (~30-40% of total time). Similarly, performing multiple regex passes (`re.findall` then `re.search` in a loop) creates O(N_matches * N_doc) complexity.
**Action:** Use `read_bytes()` for hashing and defer `.decode()` until changes are confirmed. Use `re.finditer()` with pre-compiled regexes for single-pass extraction to achieve ~70% speedup in semantic processing.

## 2026-05-20 - [Lazy-loading Module Setup for CLI Performance]
**Learning:** For Python CLI tools, even small top-level calls like `load_dotenv()` or `logging.basicConfig()` contribute measurably to startup latency (~40-60ms). Deferring these to a thread-safe "ensure setup" method called only when an action is actually being processed significantly improves responsiveness for the "hot path" (e.g., cache hits).
**Action:** Move environment and logging setup into a lazy `_ensure_setup()` method. Use `threading.RLock` to ensure it runs exactly once. Defer heavy imports (like `glob`) to the method scope where they are used.

## 2026-05-20 - [Lazy Property Pattern for Configuration Discovery]
**Learning:** Performing disk-intensive configuration discovery (like `glob.glob` for "brain" directories or file reads for "immutable laws") in `__init__` forces a performance penalty on every instantiation, even for simple status checks.
**Action:** Refactor all configuration discovery into lazy properties. Use a boolean sentinel (e.g., `_searched`) to handle cases where a search returns `None` and should not be repeated.
