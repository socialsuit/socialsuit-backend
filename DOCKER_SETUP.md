# Docker Setup for Social Suit Projects

This document provides instructions for setting up and running the Social Suit and Sparkr projects using Docker.

## Prerequisites

- Docker and Docker Compose installed on your system
- Git repository cloned locally

## Project Structure

Both projects have been configured with Docker for easy development and deployment:

- Each project has its own `Dockerfile` and `docker-compose.yml`
- Services include FastAPI app, Celery worker/beat, PostgreSQL, and Redis
- Health check endpoints are available at `/healthz`
- Makefiles are provided for common Docker operations

## Social Suit Project

### Services

- **API**: FastAPI application running on port 8000
- **Worker**: Celery worker for background tasks
- **Beat**: Celery beat for scheduled tasks
- **PostgreSQL**: Database running on port 5432
- **Redis**: Cache and message broker running on port 6379
- **MongoDB**: Document database running on port 27017

### Commands

From the `social-suit` directory:

```bash
# Start all services
make up

# Stop all services
make down

# Build or rebuild services
make build

# View logs
make logs

# List running containers
make ps

# Remove all containers, networks, and volumes
make clean
```

## Sparkr Project

### Services

- **API**: FastAPI application running on port 8001
- **Worker**: Celery worker for background tasks
- **Beat**: Celery beat for scheduled tasks
- **PostgreSQL**: Database running on port 5433
- **Redis**: Cache and message broker running on port 6380

### Commands

From the `sparkr` directory:

```bash
# Start all services
make up

# Stop all services
make down

# Build or rebuild services
make build

# View logs
make logs

# List running containers
make ps

# Remove all containers, networks, and volumes
make clean
```

## Health Checks

Both projects include health check endpoints that verify the status of the API and its dependencies:

- Social Suit: http://localhost:8000/healthz
- Sparkr: http://localhost:8001/healthz

The health check returns a JSON response with the status of each service:

```json
{
  "status": "healthy",
  "services": {
    "api": "up",
    "database": "up",
    "redis": "up"
  }
}
```

## Development Workflow

1. Start the services with `make up`
2. Make changes to your code - the changes will be reflected immediately due to volume mounts
3. Check the logs with `make logs` if needed
4. Stop the services with `make down` when finished

## Shared Library

The shared library is mounted as a volume in both projects, allowing changes to be reflected immediately without rebuilding containers.

## Notes

- Each project uses distinct service names and ports to avoid conflicts
- Environment variables are set in the docker-compose.yml files
- For production deployment, you should modify the configurations to use proper secrets management