# CareVoice AI Hospital Platform - Production Dockerfile
# Multi-stage/Slim build optimized for Python 3.11 with Astral uv

# Get Astral uv binary from official image
FROM ghcr.io/astral-sh/uv:latest AS uv_bin

FROM python:3.11-slim as builder

# Setup system environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Install system dependencies needed for compiling psycopg2/asyncpg or other native libraries
RUN apt-get update \
    && apt-get install --no-install-recommends -y \
       build-essential \
       libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy uv binaries
COPY --from=uv_bin /uv /uvx /bin/

# Copy project manifest and lockfile first to optimize Docker layer caching
COPY pyproject.toml uv.lock ./

# Create virtual environment and install dependencies from lockfile (deterministic, reproducible)
RUN uv venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
RUN uv sync --frozen --no-dev --no-install-project


# Production Final stage
FROM python:3.11-slim as final

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# Install runtime dependencies (like libpq for postgres connection)
RUN apt-get update \
    && apt-get install --no-install-recommends -y \
       libpq5 \
       curl \
    && rm -rf /var/lib/apt/lists/*

# Copy uv binaries to final stage for direct "uv run" commands in container orchestration
COPY --from=uv_bin /uv /uvx /bin/

# Copy virtual environment from builder stage
COPY --from=builder /app/.venv /app/.venv

# Copy backend codebase
COPY . .

# Expose port 8000 for local development/production orchestration
EXPOSE 8000

# Default health check to verify container liveness
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Launch the FastAPI application using high-performance Uvicorn server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
