# ══════════════════════════════════════════════════════════════
# COGNARC — API Dockerfile (Production)
# infrastructure/docker/api/ — referenced by docker-compose.yml
# Base: python:3.12-slim | Runtime: uvicorn | Port: 8000
# §01: NEVER install conda/jupyter/notebooks in production image
# ══════════════════════════════════════════════════════════════

FROM python:3.12-slim AS base

# Security: run as non-root
RUN groupadd --gid 1001 cognarc \
    && useradd --uid 1001 --gid cognarc --shell /bin/bash --create-home cognarc

# Install system deps needed for Motor/pydantic/cryptography
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ── Dependency Layer (cached separately) ──────────────────────
FROM base AS deps

COPY apps/api/requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# ── Application Layer ─────────────────────────────────────────
FROM deps AS app

COPY apps/api/app ./app

# Copy env example for documentation (never .env itself)
COPY apps/api/.env.example ./.env.example

# Switch to non-root user
USER cognarc

# ── Runtime ───────────────────────────────────────────────────
EXPOSE 8000

# Healthcheck — aligns with GET /health
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "1", \
     "--no-access-log"]
