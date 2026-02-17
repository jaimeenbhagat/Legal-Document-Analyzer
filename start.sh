#!/bin/bash

# Start script for Render deployment
# Runs FastAPI backend on Render's assigned port

echo "🚀 Starting Legal AI Backend..."

# Get the port from Render (default 10000)
PORT=${PORT:-10000}

# Start backend on Render's assigned port
echo "🔧 Starting backend on port $PORT..."
uvicorn app.main:app --host 0.0.0.0 --port $PORT

echo "✅ Backend is running on port $PORT"
