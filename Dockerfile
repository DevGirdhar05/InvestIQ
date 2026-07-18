FROM python:3.13-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies first
# Docker caches this layer — only re-runs if requirements.txt changes
# This makes rebuilds much faster
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# ── Stage 2: Runtime ──────────────────────────────────────────────
FROM python:3.13-slim

WORKDIR /app

# Copy installed packages from builder stage
COPY --from=builder /root/.local /root/.local

# Copy application source code
COPY src/       ./src/
COPY models/    ./models/
COPY scripts/ ./scripts/

# Make sure scripts in .local are usable
ENV PATH=/root/.local/bin:$PATH

# PORT 8000 is what uvicorn listens on
EXPOSE 8000

# Health check — Docker restarts the container if this fails
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

# Start command
CMD ["sh", "-c", "python scripts/init_db.py && uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --workers 2"]