# =============================================================================
# Multi-Stage Dockerfile for Legal Document Analyzer
# Single container serving both FastAPI backend + Next.js static frontend
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1: Build Next.js Frontend
# -----------------------------------------------------------------------------
FROM node:20-alpine AS frontend-builder

WORKDIR /app

# Copy package files first (better layer caching)
COPY frontend/package.json frontend/package-lock.json* ./

# Install dependencies
RUN npm install --legacy-peer-deps

# Copy all frontend source files
COPY frontend/ ./

# Remove any stale local build artifacts
RUN rm -f tsconfig.tsbuildinfo && rm -rf .next

# Set build-time env vars
ENV STATIC_EXPORT=true
ENV NEXT_TELEMETRY_DISABLED=1
# Increase Node.js memory limit for Docker build
ENV NODE_OPTIONS="--max-old-space-size=2048"

# Build static export using webpack (not turbopack)
RUN npm run build

# -----------------------------------------------------------------------------
# Stage 2: Python Backend + Serve Static Frontend
# -----------------------------------------------------------------------------
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=10000

WORKDIR /app

# Install system dependencies for faiss-cpu
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY app/ ./app/

# Copy data directory (FAISS indexes and PDFs)
COPY data/ ./data/

# Copy static frontend build from Stage 1 (WORKDIR was /app, output is /app/out)
COPY --from=frontend-builder /app/out ./static

# Create directories for runtime data
RUN mkdir -p ./data/pdfs ./data/faiss_index

# Expose port (Render uses 10000)
EXPOSE 10000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:10000/health')" || exit 1

# Run FastAPI with uvicorn
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "10000"]
