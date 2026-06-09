#!/usr/bin/env bash
set -e

# Kill any stale processes on our ports
fuser -k 8000/tcp 2>/dev/null || true

# Start the Django backend on port 8000 (internal, proxied by Vite)
cd /home/runner/workspace/pos_project/backend
python3 manage.py runserver 0.0.0.0:8000 --noreload &
DJANGO_PID=$!

# Give Django a couple of seconds to boot before Vite starts proxying
sleep 2

echo "Django started (PID $DJANGO_PID) on port 8000"
echo "Starting Vite dev server on port $PORT ..."

# Start the POS Vite dev server; it reads PORT from the environment
cd /home/runner/workspace/pos_project/frontend
exec node_modules/.bin/vite --host 0.0.0.0
