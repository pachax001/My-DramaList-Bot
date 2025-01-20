# Use a minimal Python base image
FROM python:3.11-slim

# Set environment variables to avoid .pyc files and buffering
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory inside the container
WORKDIR /app

# Install necessary dependencies to build Pyrogram and other packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    libffi-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements first to leverage Docker caching
COPY requirements.txt /app/

# Create a virtual environment and install dependencies
RUN python3 -m venv /app/venv && \
    /app/venv/bin/pip install --no-cache-dir --upgrade pip && \
    /app/venv/bin/pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code after dependencies are installed
COPY . /app/

# Ensure __pycache__ and other unnecessary files are ignored
RUN find . -type d -name "__pycache__" -exec rm -rf {} + && \
    find . -type f -name "*.pyc" -delete

# Activate venv and set the entrypoint
ENV PATH="/app/venv/bin:$PATH"

# Start the bot using venv Python explicitly
CMD ["/app/venv/bin/python", "main.py"]
