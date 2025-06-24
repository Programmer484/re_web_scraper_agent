FROM python:3.11-slim as builder

# Install system dependencies for building
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install dependencies in a virtualenv
COPY requirements.txt .

# Create virtual environment at /venv
RUN python -m venv /venv \
    && /venv/bin/pip install --no-cache-dir --upgrade pip \
    && /venv/bin/pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim

# Create non-root user for security
RUN adduser --disabled-password --gecos '' --uid 1000 appuser

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy virtualenv from builder
COPY --from=builder /venv /venv

# Copy application code
COPY --chown=appuser:appuser . .

# Set environment variables
ENV VIRTUAL_ENV=/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Create logs directory with proper permissions
RUN mkdir -p /app/logs && chown -R appuser:appuser /app/logs

# Switch to non-root user
USER appuser

# Health check with longer timeout for wake-up scenarios
HEALTHCHECK --interval=60s --timeout=60s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose the port
EXPOSE 8000

# Run the FastAPI server with debug logging
CMD ["uvicorn", "api_server:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "debug", "--access-log"]
