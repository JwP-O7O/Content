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
