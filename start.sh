#!/bin/bash

# Start script for combined deployment on Render
# This runs both the FastAPI backend and Next.js frontend

echo "🚀 Starting Legal AI System..."

# Install frontend dependencies and build
echo "📦 Building frontend..."
cd frontend
npm install
npm run build

# Start backend in background
echo "🔧 Starting backend..."
cd ..
uvicorn app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Wait for backend to be ready
sleep 5

# Start frontend
echo "🌐 Starting frontend..."
cd frontend
PORT=3000 npm run start &
FRONTEND_PID=$!

echo "✅ Legal AI System is running!"
echo "   Frontend: http://localhost:3000"
echo "   Backend:  http://localhost:8000"

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID
