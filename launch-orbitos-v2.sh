#!/bin/zsh
# Script to launch backend (FastAPI) and frontend (npm) in production mode

cleanup() {
  echo "Stopping backend and frontend..."
  kill $BACKEND_PID 2>/dev/null
  kill $FRONTEND_PID 2>/dev/null
  exit
}

trap cleanup SIGINT SIGTERM

# Start backend
source .venv/bin/activate
cd backend
fastapi run src/main.py &
BACKEND_PID=$!
cd ..

# Start frontend
cd frontend && npm run start &
FRONTEND_PID=$!
cd ..

# Wait for both to finish
wait $BACKEND_PID $FRONTEND_PID