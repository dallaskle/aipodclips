import multiprocessing

# Worker Settings
workers = 2  # Reduced from cpu_count() * 2 + 1 to stay within memory limits
worker_class = 'gevent'  # Using gevent for async support with Flask
worker_connections = 1000
timeout = 300  # 5 minutes
keepalive = 2

# Memory Management
max_requests = 100  # Restart workers after handling this many requests
max_requests_jitter = 10  # Add randomness to the max_requests
limit_request_line = 4096
limit_request_fields = 100
limit_request_field_size = 8190

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

# Memory Optimization
worker_tmp_dir = '/dev/shm'  # Use shared memory for temporary files
max_requests_jitter = 10  # Helps prevent memory leaks
graceful_timeout = 30  # Give workers time to finish 