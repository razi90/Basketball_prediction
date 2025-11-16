# Multi-stage Dockerfile for NBA Prediction System
# Optimized for both production and development

# Stage 1: Base image with dependencies
FROM python:3.12-slim AS base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    gnupg \
    unzip \
    curl \
    netcat-openbsd \
    ca-certificates \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libc6 \
    libcairo2 \
    libcups2 \
    libdbus-1-3 \
    libexpat1 \
    libfontconfig1 \
    libgbm1 \
    libgcc1 \
    libglib2.0-0 \
    libgomp1 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libstdc++6 \
    libx11-6 \
    libx11-xcb1 \
    libxcb1 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxi6 \
    libxrandr2 \
    libxrender1 \
    libxss1 \
    libxtst6 \
    lsb-release \
    xdg-utils \
    && rm -rf /var/lib/apt/lists/*

# Install Chromium for Selenium (multi-architecture support)
# Chromium supports both amd64 and arm64, unlike Chrome which is amd64-only
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    chromium \
    chromium-driver && \
    rm -rf /var/lib/apt/lists/*

# Create symbolic links for compatibility with scripts expecting 'google-chrome' and 'chromedriver'
RUN ln -s /usr/bin/chromium /usr/bin/google-chrome && \
    ln -s /usr/bin/chromedriver /usr/local/bin/chromedriver

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Stage 2: Development image
FROM base AS development

# Copy entire project
COPY . .

# Install CLI in editable mode
RUN pip install -e .

# Create necessary directories
RUN mkdir -p 2026/data 2026/output logs

# Set working directory to source
WORKDIR /app/2026/src

# Default command for development
CMD ["bash"]

# Stage 3: Dashboard image
FROM base AS dashboard

# Copy entire project
COPY . .

# Install CLI in editable mode
RUN pip install -e .

# Expose Streamlit port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Run dashboard
CMD ["streamlit", "run", "dashboard/app.py", "--server.address", "0.0.0.0", "--server.port", "8501"]

# Stage 4: Production runner
FROM base AS production

# Copy entire project
COPY . .

# Install CLI in editable mode
RUN pip install -e .

# Create necessary directories
RUN mkdir -p 2026/data 2026/output logs

# Copy entrypoint script
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

WORKDIR /app

ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["nba-predict", "pipeline"]
