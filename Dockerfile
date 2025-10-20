# Multi-stage build for minimal image size and fast bootup
FROM python:3.11-slim as base

# Set environment variables for optimization
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100

# Install system dependencies in a single layer
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# ============================================
# Stage 2: Dependencies installation
# ============================================
FROM base as dependencies

# Copy only requirements files first for better layer caching
COPY requirements.txt ./
COPY 2DMatGMM/requirements.txt ./2DMatGMM/
COPY cameraTesting/SDK/Python\ Toolkit/examples/Requirements.txt ./camera_requirements.txt

# Install Python dependencies in order of stability (least likely to change first)
# This optimizes Docker layer caching
RUN pip install --no-cache-dir \
    pillow>=5.4.1 \
    tifffile>=2019.3.8 \
    numpy==1.24.4 \
    opencv-python==4.8.0.74 \
    numba==0.57.1 \
    scikit-image==0.21.0 \
    scikit-learn==1.3.0 \
    matplotlib \
    flask \
    websockets \
    pyserial \
    python-dotenv \
    && python -m compileall -q /usr/local/lib/python3.11

# ============================================
# Stage 3: Application
# ============================================
FROM base as application

# Copy Python packages from dependencies stage
COPY --from=dependencies /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages

# Copy application code
COPY src/ ./src/
COPY 2DMatGMM/ ./2DMatGMM/
COPY shared/ ./shared/
COPY contrastDictDir/ ./contrastDictDir/

# Copy necessary camera SDK files (only what's needed)
COPY cameraTesting/SDK/Python\ Toolkit/ ./cameraTesting/SDK/Python\ Toolkit/

# Pre-compile Python files for faster startup
RUN python -m compileall -q ./src ./2DMatGMM

# Create non-root user for security
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

USER appuser

# Expose ports
EXPOSE 5000 8765

# Set working directory to src
WORKDIR /app/src

# Health check for faster container orchestration
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:5000/health', timeout=2)" || exit 1

# Use exec form for faster signal handling
CMD ["python", "-u", "main.py"]

