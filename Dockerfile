# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy pyproject.toml
COPY pyproject.toml /app/

# Install application dependencies
RUN pip install --no-cache-dir . && pip install --no-cache-dir ".[dev,ml]"

# Copy the rest of the application code
COPY . /app/

# Expose port
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "services.core.main:app", "--host", "0.0.0.0", "--port", "8000"]
