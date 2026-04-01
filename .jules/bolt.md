## 2026-03-29 - [PWA Polling Overhead]
**Learning:** Aggressive polling (500ms) with cache-busting and unconditional state updates leads to high CPU and battery drain on mobile devices, even when the UI state is static.
**Action:** Implement 'Smart Polling' by respecting 'document.visibilityState' and only updating state if the payload has changed.

## 2026-03-30 - [Log File Tail Retrieval]
**Learning:** Reading a large file (like `WORK_LOG.md`) into memory only to slice the tail is an O(N) memory and I/O bottleneck.
**Action:** Use binary mode `rb` with `f.seek(max(0, file_size - N))` to achieve O(1) performance, and use `decode(errors='ignore')` to handle multi-byte characters safely.
