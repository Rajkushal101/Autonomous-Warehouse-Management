# ==============================================================================
# Hardened Minimal Multi-Stage Dockerfile
# Autonomous Warehouse Management System (Phase 13 / DC-02 / DC-03)
# ==============================================================================

# Stage 1: Build & Dependencies
FROM python:3.12-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Hardened Runtime Container
FROM python:3.12-slim AS runtime

# Security Practice 1: Non-root execution
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -s /sbin/nologin -M appuser

WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /root/.local /home/appuser/.local
ENV PATH=/home/appuser/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Copy application source code (excluding tests, docs, secrets via .dockerignore)
COPY app/ /app/app/
COPY worker/ /app/worker/
COPY scripts/ /app/scripts/

# Security Practice 2: Filesystem permissions & non-root ownership
RUN chown -R appuser:appgroup /app && \
    chmod -R 550 /app

USER appuser:appgroup

# Security Practice 3: Controlled port exposure
EXPOSE 8000

# Security Practice 4: Health check probe
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health/live')" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
