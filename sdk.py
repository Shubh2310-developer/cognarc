"""
COGNARC — Langfuse SDK Connection Test
Run: python sdk.py
Verifies LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, LANGFUSE_HOST are reachable.
"""

import os
from dotenv import load_dotenv

# Load from root .env
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

# ── Langfuse keys check ───────────────────────────────────────
public_key  = os.getenv("LANGFUSE_PUBLIC_KEY")
secret_key  = os.getenv("LANGFUSE_SECRET_KEY")
host        = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")

if not public_key or not secret_key:
    print("⚠️  LANGFUSE_PUBLIC_KEY / LANGFUSE_SECRET_KEY not set in .env")
    print("   These are Phase 10 keys — fill them when you create a Langfuse project.")
    print("   Skipping connection test.")
    raise SystemExit(0)

# ── Connect ───────────────────────────────────────────────────
from langfuse import Langfuse

langfuse = Langfuse(
    public_key=public_key,
    secret_key=secret_key,
    host=host,
)

# ── Send a test trace ─────────────────────────────────────────
trace = langfuse.trace(
    name="cognarc-sdk-test",
    metadata={"env": "development", "test": True},
)

span = trace.span(name="test-span")
span.end(output={"status": "ok"})

langfuse.flush()

print(f"✅  Langfuse connected → {host}")
print(f"   Trace ID: {trace.id}")
print("   Check your Langfuse dashboard → Traces to confirm.")