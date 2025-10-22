#!/bin/bash
# Render start script for AURION Backend

echo "🌟 Starting AURION Backend..."

# Start the server
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
