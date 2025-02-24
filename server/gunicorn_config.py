import multiprocessing

# Worker Settings
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = 'uvicorn.workers.UvicornWorker'  # Using Uvicorn's worker class for better async support
worker_connections = 1000
timeout = 300  # Increase timeout to 5 minutes
keepalive = 2

# Memory Management
max_requests = 1000  # Restart workers after handling this many requests
max_requests_jitter = 50  # Add randomness to the max_requests
worker_tmp_dir = '/dev/shm'  # Use shared memory for temporary files

# Logging
accesslog = '-'
errorlog = '-'
loglevel = 'info'

# Process Naming
proc_name = 'aipodclips_server'

# SSL Configuration (if needed)
# keyfile = 'path/to/keyfile'
# certfile = 'path/to/certfile'

# Server Mechanics
preload_app = True  # Load application code before worker processes are forked 