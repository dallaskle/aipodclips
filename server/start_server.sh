#!/bin/bash

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Set environment variables for memory management
export PYTHONUNBUFFERED=1
export PYTHONMALLOC=malloc
export MALLOC_TRIM_THRESHOLD_=65536

# Start Gunicorn with the config file
exec gunicorn main:app \
    --config gunicorn_config.py \
    --preload \
    --max-requests 1000 \
    --max-requests-jitter 50 \
    --worker-tmp-dir /dev/shm \
    --log-level info 