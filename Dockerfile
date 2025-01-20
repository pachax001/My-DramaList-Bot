# Use a minimal Python base image
FROM python:3.11-slim

# Set environment variables to minimize the image size and avoid .pyc files
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set working directory inside the container
WORKDIR /app

# Install dependencies required for building Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    libffi-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy and install dependencies
COPY requirements.txt /app/

# Create virtual environment and install dependencies
RUN python3 -m venv /app/venv && \
    /app/venv/bin/pip install --upgrade pip && \
    /app/venv/bin/pip install -r requirements.txt

# Copy the application code
COPY . /app/

# Ensure __pycache__ and other unnecessary files are ignored
RUN find . -type d -name "__pycache__" -exec rm -rf {} + && \
    find . -type f -name "*.pyc" -delete

# Activate venv and set the entrypoint
ENV PATH="/app/venv/bin:$PATH"

# Start the bot
CMD ["python", "main.py"]
