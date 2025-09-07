FROM python:3.11-slim

# Install system dependencies including curl for health checks
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    python3-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better Docker layer caching
COPY requirements*.txt* ./
COPY pyproject.toml* ./

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    if [ -f requirements.txt ]; then pip install --no-cache-dir -r requirements.txt; fi && \
    if [ -f pyproject.toml ]; then pip install --no-cache-dir -e .; fi

# Copy the rest of the application
COPY . .

# Create data directory for file-based storage
RUN mkdir -p data

# Set Python path to include current directory
ENV PYTHONPATH=/app

# Default command (will be overridden by docker-compose)
CMD ["python", "-m", "bff.main"]

# Health check endpoint (generic)
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
  CMD curl -f http://localhost:8000/api/health || curl -f http://localhost:8000/health || exit 1