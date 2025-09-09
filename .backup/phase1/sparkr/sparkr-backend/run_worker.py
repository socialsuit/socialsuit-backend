#!/usr/bin/env python
import os
import sys
import subprocess
from app.core.config import settings

def main():
    """Run the Celery worker"""
    print("Starting Celery worker...")
    cmd = [
        "celery",
        "-A", "app.workers.tasks_worker.celery_app",
        "worker",
        "--loglevel=info"
    ]
    
    # Add optional arguments from command line
    if len(sys.argv) > 1:
        cmd.extend(sys.argv[1:])
    
    # Run the worker
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("Worker stopped")
    except subprocess.CalledProcessError as e:
        print(f"Error running worker: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()