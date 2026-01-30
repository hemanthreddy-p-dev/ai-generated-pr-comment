FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /action

# Copy application files
COPY requirements.txt .
COPY entrypoint.sh .
COPY analyze_pr.py .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Make entrypoint executable
RUN chmod +x /action/entrypoint.sh

# Set entrypoint
ENTRYPOINT ["/action/entrypoint.sh"]
