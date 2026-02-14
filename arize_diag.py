# arize_diag.py — V3.14 Secure Diagnostic (NO SECRETS PRINTED)
import os
from dotenv import load_dotenv
load_dotenv()

from opentelemetry import trace
import time

space_id = os.getenv('ARIZE_SPACE_ID')
api_key = os.getenv('ARIZE_API_KEY')

# Security: Only confirm presence, NEVER print values
print(f"ARIZE_SPACE_ID present: {bool(space_id)}")
print(f"ARIZE_API_KEY present: {bool(api_key)}")

if not space_id or not api_key:
    print("Init fail: Missing ARIZE credentials in .env")
    exit(1)

try:
    from arize.otel import register
    tracer_provider = register(
        space_id=space_id,
        api_key=api_key,
        project_name='Auth_Test_Diagnostic_V3.14'
    )
    tracer = tracer_provider.get_tracer(__name__)
    with tracer.start_as_current_span('diag_span'):
        pass  # Span created successfully
    time.sleep(2)
    print("Init success")
except Exception as e:
    err_msg = str(e)
    if "PERMISSION_DENIED" in err_msg or "403" in err_msg:
        print(f"Init fail: PERMISSION_DENIED — check that ARIZE_API_KEY is valid and not revoked.")
    else:
        print(f"Init fail: {e}")
