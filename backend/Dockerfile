# ============================================================
# Healthcare Risk Platform — Backend Dockerfile
# Multi-stage build for minimal production image
# ============================================================

# ── Stage 1: Builder ─────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Use requirements-render.txt (requirements.txt was removed)
COPY requirements-render.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir --user -r requirements-render.txt

# ── Stage 2: Production ───────────────────────────────────────
FROM python:3.11-slim AS production

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd -r appuser && useradd -r -g appuser appuser

COPY --from=builder /root/.local /home/appuser/.local
COPY --chown=appuser:appuser . .

RUN mkdir -p /app/models && chown appuser:appuser /app/models

USER appuser

ENV PATH=/home/appuser/.local/bin:$PATH
ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
