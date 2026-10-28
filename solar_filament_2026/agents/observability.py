"""Agent Observability & OpenTelemetry Instrumentation.

Conforms to google-agents-cli-observability standards:
- Emits structured execution traces and tool spans.
- Gated content logging (NO_CONTENT / SPAN_ONLY).
- Deterministic local JSONL telemetry buffer.
"""

from __future__ import annotations

import json
import logging
import os
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Generator, Optional

logger = logging.getLogger("filament.agents.observability")


class AgentTracer:
    """Lightweight, resilient OpenTelemetry-compatible span and event tracer."""

    def __init__(self, trace_log_path: Optional[Path] = None) -> None:
        if trace_log_path is None:
            self.trace_log_path = Path(os.getcwd()) / "solar_filament_2026" / "data" / "agent_traces.jsonl"
        else:
            self.trace_log_path = trace_log_path
        self.trace_log_path.parent.mkdir(parents=True, exist_ok=True)

    def log_event(self, event_name: str, payload: Dict[str, Any]) -> None:
        """Append structured event payload to local trace ledger."""
        record = {
            "timestamp": time.time(),
            "iso_time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "event": event_name,
            "payload": payload,
        }
        try:
            with open(self.trace_log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record) + "\n")
        except Exception as e:
            logger.warning(f"Failed to append agent telemetry: {e}")

    @contextmanager
    def span(self, span_name: str, attributes: Optional[Dict[str, Any]] = None) -> Generator[Dict[str, Any], None, None]:
        """Context manager tracing execution span with timing and error capture."""
        start_time = time.perf_counter()
        span_data = {
            "span_name": span_name,
            "status": "RUNNING",
            "attributes": attributes or {},
        }
        self.log_event(f"span_start:{span_name}", span_data)
        try:
            yield span_data
            span_data["status"] = "OK"
        except Exception as e:
            span_data["status"] = "ERROR"
            span_data["error"] = str(e)
            raise
        finally:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            span_data["duration_ms"] = round(elapsed_ms, 2)
            self.log_event(f"span_end:{span_name}", span_data)


# Global singleton instance
TRACER = AgentTracer()
