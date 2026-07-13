#!/bin/bash

# EYE Project - Start both frontend and backend servers

echo "🚀 Starting EYE Project..."
echo ""

# Start backend
echo "📡 Starting Backend (FastAPI)..."
cd backend
export DYLD_LIBRARY_PATH=/opt/homebrew/lib:$DYLD_LIBRARY_PATH
bash start.sh &
BACKEND_PID=$!
cd ..

# Wait a moment for backend to initialize
sleep 3

# Start frontend
echo "🎨 Starting Frontend (React/Vite)..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "✅ Both servers started!"
echo "   Backend:  http://127.0.0.1:8000"
echo "   Frontend: http://localhost:5173"
echo ""
echo "Press Ctrl+C to stop both servers"
echo ""

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID
