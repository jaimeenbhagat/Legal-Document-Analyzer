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

# Remove any stale local build artifacts and Next.js auto-generated files
RUN rm -f tsconfig.tsbuildinfo && rm -rf .next && rm -f next-env.d.ts

# Overwrite tsconfig.json to remove Next.js auto-added incremental/.next paths
# (Next.js modifies tsconfig.json locally; these entries break fresh Docker builds)
RUN printf '{\n  "compilerOptions": {\n    "baseUrl": ".",\n    "target": "ES2017",\n    "lib": ["dom", "dom.iterable", "esnext"],\n    "allowJs": true,\n    "skipLibCheck": true,\n    "strict": true,\n    "noEmit": true,\n    "esModuleInterop": true,\n    "module": "esnext",\n    "moduleResolution": "bundler",\n    "resolveJsonModule": true,\n    "isolatedModules": true,\n    "jsx": "react-jsx",\n    "plugins": [{"name": "next"}],\n    "paths": {"@/*": ["./*"]}\n  },\n  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", "**/*.mts"],\n  "exclude": ["node_modules"]\n}\n' > tsconfig.json

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
