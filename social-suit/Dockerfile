FROM python:3.11-slim

WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install shared library
COPY ../shared /shared
RUN pip install --no-cache-dir -e /shared

# Copy project files
COPY . .

# Create health check endpoint
RUN echo 'from fastapi import FastAPI, APIRouter\n\nrouter = APIRouter()\n\n@router.get("/health")\ndef health_check():\n    return {"status": "healthy"}\n\ndef add_health_routes(app: FastAPI):\n    app.include_router(router)' > app/api/health.py

# Expose port
EXPOSE 10000

# Command to run the application in production
CMD ["gunicorn", "app.main:app", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:10000"]