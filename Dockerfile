# Multi-stage Dockerfile for Content Creator
# Optimized for production deployment

# Build stage - install dependencies
FROM python:3.11-slim as builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --user -r requirements.txt

# Runtime stage - minimal image
FROM python:3.11-slim

WORKDIR /app

# Install only runtime dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY . .

# Make sure scripts are executable
RUN chmod +x init_db.py main.py verify_system.py

# Add local bin to PATH
ENV PATH=/root/.local/bin:$PATH

# Create non-root user for security
RUN useradd -m -u 1000 contentcreator && \
    chown -R contentcreator:contentcreator /app

USER contentcreator

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "from src.database.connection import engine; engine.connect()" || exit 1

# Default command
CMD ["python", "main.py", "--scheduled"]
# Use an official Python runtime as a parent image
FROM python:3.9-slim-buster

# Set the working directory in the container
WORKDIR /app

# Install system dependencies required by psycopg2
# (PostgreSQL client library used by the application)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 5000 available to the world outside this container
# (If main.py runs a web server, though currently it's a CLI/scheduler)
EXPOSE 5000

# Run init_db.py to ensure database schema is created
# This will be handled by docker-compose's entrypoint or explicit command
# ENTRYPOINT ["/bin/bash", "-c"]
# CMD ["python", "main.py"]
