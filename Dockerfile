# Use a lightweight Python base image with proper package management
FROM python:3.13.7-slim

# Set the working directory
WORKDIR /usr/src/app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Configure git for container environment
RUN git config --global --add safe.directory /usr/src/app

# Make start.sh executable
RUN chmod +x start.sh

# Run the application
CMD ["bash", "start.sh"]