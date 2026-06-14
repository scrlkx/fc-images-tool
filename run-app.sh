#!/bin/bash

set -e

APP_DIR="$(cd "$(dirname "$0")" && pwd)"
PORT=8501

# Kill any existing instance of this app
pkill -f "streamlit run $APP_DIR/app.py" 2>/dev/null || true

# Start Streamlit server in background
"$APP_DIR/.venv/bin/streamlit" run "$APP_DIR/app.py" \
    --server.port "$PORT" \
    --server.headless true \
    --browser.gatherUsageStats false &

# Wait for server to be ready (up to 15s)
for i in $(seq 1 30); do
    sleep 0.5
    nc -z localhost "$PORT" 2>/dev/null && break
done

# Open in default browser
xdg-open "http://localhost:$PORT"
