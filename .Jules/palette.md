## 2025-05-15 - [Accessible Status Indicators]
**Learning:** When using `animate-ping` for a status indicator, always use `motion-safe:animate-ping` to respect user preferences for reduced motion. Additionally, adding `role="status"` and an `aria-label` with descriptive text (e.g., "Connection Status: Live") provides much better context for screen readers than the raw text label alone.
**Action:** Always apply `motion-safe:` to decorative/status animations and provide explicit ARIA context for status indicators in future tasks.
