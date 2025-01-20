# Use a minimal Python base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements first for caching dependencies
COPY requirements.txt /app/

# Install dependencies
RUN python3 -m venv /app/venv && \
    /app/venv/bin/pip install --upgrade pip && \
    /app/venv/bin/pip install -r requirements.txt

# Copy the rest of the application files
COPY . /app/

# Ensure __pycache__ and other unnecessary files are ignored
RUN find . -type d -name "__pycache__" -exec rm -rf {} + && \
    find . -type f -name "*.pyc" -delete

# Activate venv and set the entrypoint
ENV PATH="/app/venv/bin:$PATH"
CMD ["python", "main.py"]
