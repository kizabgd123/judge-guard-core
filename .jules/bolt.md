## 2026-03-29 - [PWA Polling Overhead]
**Learning:** Aggressive polling (500ms) with cache-busting and unconditional state updates leads to high CPU and battery drain on mobile devices, even when the UI state is static.
**Action:** Implement 'Smart Polling' by respecting 'document.visibilityState' and only updating state if the payload has changed.

## 2026-03-31 - [Destructive Testing in Performance Benchmarks]
**Learning:** Writing benchmarks or tests that overwrite real project files (like `WORK_LOG.md`) to test large-file performance is a critical risk. It leads to data loss and rejected PRs.
**Action:** Always use `tempfile` or mock file system paths via `pytest` monkeypatching when testing I/O operations on project-critical files.
