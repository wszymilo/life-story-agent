FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy project files (paths relative to context: ./aws)
COPY ../app/pyproject.toml /app/
COPY ../app/uv.lock /app/
COPY ../app/ /app/

# Install Python dependencies using uv
RUN pip install uv && \
    uv sync --frozen --no-dev

# Copy application code (after deps installed for better caching)
COPY ../app/ /app/

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV ENVIRONMENT=production

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run with uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
