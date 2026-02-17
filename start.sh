#!/bin/bash

# Start script for combined deployment on Render
# This runs both the FastAPI backend and Next.js frontend

echo "🚀 Starting Legal AI System..."

# Start backend in background
echo "🔧 Starting backend on port 8000..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Wait for backend to be ready
sleep 3

# Start frontend (already built during build phase)
echo "🌐 Starting frontend on port 10000..."
cd frontend
PORT=10000 npm run start &
FRONTEND_PID=$!

echo "✅ Legal AI System is running!"
echo "   Frontend: http://localhost:10000"
echo "   Backend:  http://localhost:8000"

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID
