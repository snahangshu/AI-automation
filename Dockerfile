# Use an official Python image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=.

# Install system dependencies for Playwright/Chromium
# These are the essential libraries Render (and other Linux systems) need to run headless Chrome
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    gnupg \
    libnss3 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpangocairo-1.0-0 \
    libx11-xcb1 \
    libxshmfence1 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers (pre-baked into image for faster spin-up)
RUN playwright install chromium

# Copy application code
COPY . .

# Expose the API port
EXPOSE 8000

# The start command is handled by render.yaml blueprints or the dashboard.
# We will use 'api/server.py' for the Web Service and 'workflow.py' for the Worker.
CMD ["python", "api/server.py"]
