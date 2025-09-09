# Sparkr Backend

[![Version](https://img.shields.io/badge/version-0.1.0-blue.svg)](https://github.com/yourusername/sparkr-backend/releases/tag/v0.1.0)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

Sparkr Backend is a high-performance API service that powers the Sparkr platform, providing campaign management, task tracking, user engagement, and analytics capabilities.

## Features

- Campaign creation and management
- Task assignment and tracking
- User submission handling
- Leaderboard and rewards system
- Admin dashboard API
- Authentication and authorization
- Rate limiting and security features

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Environment Variables](#environment-variables)
- [Running the Application](#running-the-application)
- [Docker Setup](#docker-setup)
- [Make Targets](#make-targets)
- [API Documentation](#api-documentation)
- [Using the Shared Library](#using-the-shared-library)
- [Monitoring](#monitoring)
- [Testing](#testing)
- [Contributing](#contributing)
- [License](#license)

## Prerequisites

- Python 3.9+
- PostgreSQL
- Redis (optional, but recommended for caching and rate limiting)

## Installation

### Local Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/sparkr-backend.git
   cd sparkr-backend
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   # On Windows
   .\venv\Scripts\activate
   # On macOS/Linux
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your actual values
   ```

## Environment Variables

### Required Environment Variables

| Variable | Description |
|----------|-------------|
| `DB_URL` | PostgreSQL connection string with asyncpg driver |
| `SECRET_KEY` | Secret key for security features |

### Optional Environment Variables

| Variable | Description | Default |
|----------|-------------|--------|
| `REDIS_URL` | Redis connection string | redis://localhost:6379/0 |
| `DEBUG` | Enable debug mode | true |
| `HOST` | Host to bind the server | 0.0.0.0 |
| `PORT` | Port to bind the server | 8000 |
| `TWITTER_BEARER` | Twitter API bearer token | - |
| `IG_APP_ID` | Instagram App ID | - |
| `IG_APP_SECRET` | Instagram App Secret | - |

### Monitoring Variables

| Variable | Description | Default |
|----------|-------------|--------|
| `SENTRY_DSN` | Sentry Data Source Name | - |
| `SENTRY_TRACES_SAMPLE_RATE` | Percentage of transactions to sample | 0.2 |
| `SENTRY_PROFILES_SAMPLE_RATE` | Percentage of profiles to sample | 0.1 |
| `ENVIRONMENT` | Environment name (development, staging, production) | development |
| `PROMETHEUS_METRICS_ENABLED` | Enable Prometheus metrics | true |
| `PROMETHEUS_METRICS_PATH` | Path for Prometheus metrics endpoint | /metrics |

Refer to `.env.example` for a complete list of environment variables.

## Running the Application

### Local Development

```bash
python app/main.py
```

Access the API at http://localhost:8000/api/v1

### Production Deployment

For production deployment, we recommend using Docker with the provided Dockerfile and docker-compose.yml. See the [production deployment checklist](docs/production-deployment-checklist.md) for more details.

## Docker Setup

Sparkr Backend can be run using Docker and Docker Compose for easier deployment and development.

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

## Make Targets

The project includes a Makefile with the following targets:

| Target | Description |
|--------|-------------|
| `make up` | Start all services with Docker Compose |
| `make down` | Stop and remove all services |
| `make build` | Build or rebuild services |
| `make logs` | View output from containers |
| `make ps` | List running containers |
| `make clean` | Remove all containers, networks, and volumes |
| `make help` | Display available commands |

## API Documentation

The API documentation is available in OpenAPI format and can be accessed at:

- Development: http://localhost:8000/docs
- Production: https://your-domain.com/docs

The OpenAPI specification is also available at `/docs/openapi/openapi.json`.

## Using the Shared Library

Sparkr Backend uses a shared library for common functionality with the Social Suit project. To install the shared library:

```bash
cd ../shared
pip install -e .
```

Refer to the shared library documentation for more details.

## Monitoring

Sparkr Backend includes monitoring with Sentry for error tracking and Prometheus for metrics collection. See the [monitoring documentation](../docs/monitoring.md) for details.

## Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_file.py

# Run with coverage report
pytest --cov=app tests/
```

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.