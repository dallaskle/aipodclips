#!/bin/bash

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Set environment variables for memory management
export PYTHONUNBUFFERED=1
export PYTHONMALLOC=malloc
export MALLOC_TRIM_THRESHOLD_=65536
export MPLBACKEND=Agg  # Prevent matplotlib from using too much memory
export OPENBLAS_NUM_THREADS=1  # Limit numpy threads
export MKL_NUM_THREADS=1  # Limit numpy threads
export NUMEXPR_NUM_THREADS=1  # Limit numpy threads

# Set memory limit to stay under Render's 512MB limit
ulimit -v 471859200  # 450MB in bytes

# Start Gunicorn with the config file
exec gunicorn main:app \
    --config gunicorn_config.py \
    --preload \
    --max-requests 100 \
    --max-requests-jitter 10 \
    --worker-tmp-dir /dev/shm \
    --log-level info 