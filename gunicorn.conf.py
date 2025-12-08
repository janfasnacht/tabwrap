"""
Gunicorn configuration for TabWrap API production deployment.

Optimized for resource-constrained environments running LaTeX compilations.
"""

import multiprocessing
import os
import platform
from pathlib import Path

# Server socket
bind = "0.0.0.0:8000"

# Worker processes
# For LaTeX compilation workloads, limit workers to conserve memory
# Formula: (2 x CPU cores) + 1, but capped at 2 to prevent resource exhaustion
workers = min(2, (2 * multiprocessing.cpu_count()) + 1)

# Worker class - use Uvicorn for async support
worker_class = "uvicorn.workers.UvicornWorker"

# Timeout for LaTeX compilation (can be slow for complex tables)
timeout = 60  # seconds

# Logging
# Create logs directory if it doesn't exist
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

accesslog = str(log_dir / "access.log")
errorlog = str(log_dir / "error.log")
loglevel = os.getenv("TABWRAP_LOG_LEVEL", "info").lower()

# Process naming
proc_name = "tabwrap-api"

# Server mechanics
daemon = False  # systemd will handle daemonization
pidfile = None  # systemd manages process lifecycle
user = None  # Run as current user (systemd sets this)
group = None

# Graceful restarts
max_requests = 1000  # Restart workers after 1000 requests (prevent memory leaks)
max_requests_jitter = 50  # Add randomness to prevent all workers restarting simultaneously

# Resource limits
# Use tmpfs on Linux (/dev/shm) or fall back to /tmp on macOS
worker_tmp_dir = "/dev/shm" if platform.system() == "Linux" and os.path.exists("/dev/shm") else None
