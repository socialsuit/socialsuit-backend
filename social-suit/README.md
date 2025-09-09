# Social Suit

[![Version](https://img.shields.io/badge/version-0.1.0-blue.svg)](https://github.com/yourusername/social-suit/releases/tag/v0.1.0)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

Social Suit is a comprehensive social media management platform that helps businesses and individuals manage their social media presence effectively. It provides tools for content creation, scheduling, analytics, and engagement across multiple social media platforms.

## Features

- Multi-platform social media management (Meta, LinkedIn, YouTube, TikTok)
- Content creation with AI assistance
- Post scheduling and automation
- Media management with Cloudinary integration
- Analytics and performance tracking
- User and team management

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
- MongoDB
- Redis
- Node.js 16+ (for frontend development)

## Installation

### Local Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/social-suit.git
   cd social-suit
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
| `OPENROUTER_API_KEY` | API key for OpenRouter AI services |
| `DATABASE_URL` | PostgreSQL connection string |
| `MONGO_URL` | MongoDB connection string |
| `REDIS_URL` | Redis connection string |
| `JWT_SECRET` | Secret key for JWT token generation and validation |

### Optional Environment Variables

| Variable | Description | Default |
|----------|-------------|--------|
| `SDXL_API_KEY` | API key for Stable Diffusion XL image generation | - |
| `CLOUDINARY_CLOUD_NAME` | Cloudinary cloud name | - |
| `CLOUDINARY_API_KEY` | Cloudinary API key | - |
| `CLOUDINARY_API_SECRET` | Cloudinary API secret | - |
| `META_CLIENT_ID` | Meta (Facebook/Instagram) client ID | - |
| `META_REDIRECT_URI` | Meta redirect URI | - |
| `LINKEDIN_CLIENT_ID` | LinkedIn client ID | - |
| `LINKEDIN_REDIRECT_URI` | LinkedIn redirect URI | - |
| `YOUTUBE_CLIENT_ID` | YouTube client ID | - |
| `YOUTUBE_REDIRECT_URI` | YouTube redirect URI | - |
| `TIKTOK_CLIENT_KEY` | TikTok client key | - |
| `TIKTOK_REDIRECT_URI` | TikTok redirect URI | - |

### Monitoring Variables

| Variable | Description | Default |
|----------|-------------|--------|
| `SENTRY_DSN` | Sentry Data Source Name | - |
| `SENTRY_TRACES_SAMPLE_RATE` | Percentage of transactions to sample | 0.1 |
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

Access the application at http://localhost:8000

### Production Deployment

For production deployment, we recommend using Docker with the provided Dockerfile and docker-compose.yml.

## Docker Setup

Social Suit can be run using Docker and Docker Compose for easier deployment and development.

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

Social Suit uses a shared library for common functionality with the Sparkr project. To install the shared library:

```bash
cd ../shared
pip install -e .
```

Refer to the shared library documentation for more details.

## Monitoring

Social Suit includes monitoring with Sentry for error tracking and Prometheus for metrics collection. See the [monitoring documentation](../docs/monitoring.md) for details.

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