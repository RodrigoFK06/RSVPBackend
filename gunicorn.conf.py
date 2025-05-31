# gunicorn.conf.py
import os
import multiprocessing

# Basic configuration based on the issue description
workers = int(os.environ.get('GUNICORN_WORKERS', '4'))
worker_class = os.environ.get('GUNICORN_WORKER_CLASS', 'uvicorn.workers.UvicornWorker')
bind = os.environ.get('GUNICORN_BIND', '0.0.0.0:8000')

# Logging - Gunicorn's own logging. Can be configured further.
# accesslog = '-' # Log to stdout
# errorlog = '-'  # Log to stderr
loglevel = os.environ.get('GUNICORN_LOGLEVEL', 'info')

# For more advanced settings, you can add:
# threads = int(os.environ.get('GUNICORN_THREADS', '1')) # If using gthread worker class
# timeout = int(os.environ.get('GUNICORN_TIMEOUT', '30'))
# keepalive = int(os.environ.get('GUNICORN_KEEPALIVE', '2'))

# Example of dynamic workers based on CPU cores:
# default_workers = (multiprocessing.cpu_count() * 2) + 1
# workers = int(os.environ.get('GUNICORN_WORKERS', str(default_workers)))
