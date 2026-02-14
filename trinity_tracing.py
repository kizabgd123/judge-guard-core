"""
Revenue-Driven Tracing Helper for Trinity V3.14
Focuses on capturing High-Value Signals (Prompts, Decisions, Consensus).
"""
import os
import sys
import logging
from dotenv import load_dotenv

# CRITICAL: load_dotenv() MUST run before any env reads
load_dotenv()

try:
    from arize.otel import register
    from opentelemetry import trace
    from opentelemetry.trace import Status, StatusCode
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor
except ImportError:
    print("⚠️ Trace libs missing. Run: pip install arize-otel opentelemetry-api opentelemetry-sdk")
    trace = None

def get_tracer(service_name="trinity_debate"):
    """
    Initializes Arize OTEL Tracer.
    Returns a valid tracer, or a DummyTracer if dependencies/keys are missing.
    """
    # 1. Circuit Breaker: Check for Libs
    if trace is None:
        return DummyTracer()

    # 2. Circuit Breaker: Check for Keys
    space_id = os.getenv("ARIZE_SPACE_ID")
    api_key = os.getenv("ARIZE_API_KEY")
    
    if not space_id or not api_key:
        print("⚠️ ARIZE_SPACE_ID or ARIZE_API_KEY missing. Tracing Disabled.")
        return DummyTracer()

    try:
        # 3. Register Arize Tracer
        tracer_provider = register(
            space_id=space_id,
            api_key=api_key,
            project_name=service_name,
        )
        
        tracer = tracer_provider.get_tracer(service_name)
        print(f"✅ Arize Tracing Active: {service_name}")
        return tracer
    except Exception as e:
        err_msg = str(e)
        # Log full error for debugging but fall back gracefully
        if "PERMISSION_DENIED" in err_msg or "403" in err_msg:
            print(f"❌ Arize PERMISSION_DENIED: API key may be invalid or revoked. Full error: {err_msg}")
        else:
            print(f"❌ Arize Setup Failed: {err_msg}")
        print("⚠️ Falling back to DummyTracer (no-op).")
        return DummyTracer()

class DummySpan:
    def __enter__(self): return self
    def __exit__(self, exc_type, exc_val, exc_tb): pass
    def set_attribute(self, key, value): pass
    def set_status(self, status, description=None): pass
    def record_exception(self, exception): pass

class DummyTracer:
    """No-Op Tracer to prevent code breakage when tracing is off."""
    def start_as_current_span(self, name, **kwargs):
        return DummySpan()
