# Use CUDA development image instead of runtime
FROM nvidia/cuda:12.8.0-cudnn-devel-ubuntu22.04

# Set environment variables in one layer
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

# Install minimal dependencies and clean up in single layer
RUN apt-get update && \
    apt-get install -y --no-install-recommends python3-pip espeak-ng && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Create non-root user
RUN useradd -m -u 1000 appuser

# Set working directory
WORKDIR /app

# Copy and install requirements as root (for system-wide install)
COPY requirements.txt .
RUN pip3 install -r requirements.txt

# Install PyTorch with CUDA support
RUN pip3 install torch torchvision

# Install spaCy model
RUN pip3 install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.7.1/en_core_web_sm-3.7.1-py3-none-any.whl

# Copy application code and change ownership
COPY . .
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 7576

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=2 \
    CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:7576/health', timeout=5)" || exit 1

# Run application
CMD ["python3", "./src/main.py"]