# Gunicorn configuration for Portal Cautivo
# Usage: gunicorn -c deploy/gunicorn.conf.py wsgi:app

import multiprocessing

# Bind to localhost only (Nginx will proxy from outside)
bind = "127.0.0.1:8003"

# Worker configuration
workers = multiprocessing.cpu_count() + 1
worker_class = "sync"  # Use "gevent" if you install gevent and need async
worker_connections = 1000
threads = 2

# Timeout and keepalive
timeout = 30
keepalive = 2

# Request limits (restart worker after X requests to prevent memory leaks)
max_requests = 1000
max_requests_jitter = 50

# Logging
accesslog = "/var/www/wifi-portal-teste/logs/access.log"
errorlog = "/var/www/wifi-portal-teste/logs/error.log"
loglevel = "info"

# Process naming
proc_name = "portal-cautivo"

# Server mechanics
daemon = False
pidfile = "/var/run/wifi-portal-teste.pid"
umask = 0o022

# SSL (optional - use only if not behind Nginx with SSL)
# keyfile = "/etc/letsencrypt/live/seu-dominio.com/privkey.pem"
# certfile = "/etc/letsencrypt/live/seu-dominio.com/fullchain.pem"
# ssl_version = "TLSv1_2"
