# Multi-stage Dockerfile for StudyMummy Backend

# Stage 1: Build virtual environment
FROM python:3.11-slim AS builder

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy files needed for installation
COPY pyproject.toml uv.lock ./

# Install dependencies using uv caching
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

# Stage 2: Runtime image
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies (e.g., curl for healthchecks)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libcairo2 \
    tesseract-ocr \
    tesseract-ocr-deu \
    tesseract-ocr-eng \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Add virtual environment to PATH
ENV PATH="/app/.venv/bin:$PATH"

# Copy application source code and configuration
COPY app ./app
COPY pyproject.toml uv.lock ./

# Expose port
EXPOSE 8000

# Run the FastAPI app with Uvicorn in production mode behind Cloudflare Tunnel
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "*"]
