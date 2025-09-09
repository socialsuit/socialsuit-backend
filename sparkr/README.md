# Sparkr

Sparkr is a modern, high-performance application for real-time data processing and analytics.

## Environment Variables

Before running the application, you need to set up the environment variables. Create a `.env` file in the root directory of the project and add the following variables:

### Required Environment Variables

- **DATABASE_URL**: PostgreSQL connection string with asyncpg driver
- **JWT_SECRET**: Secret key for JWT token generation and validation
- **API_V1_PREFIX**: Prefix for API v1 endpoints
- **BACKEND_CORS_ORIGINS**: List of allowed CORS origins

### Optional Environment Variables

- **REDIS_HOST**, **REDIS_PORT**, **REDIS_PASSWORD**, **REDIS_DB**: Redis configuration
- **JWT_ALGORITHM**: Algorithm used for JWT (default: HS256)
- **ACCESS_TOKEN_EXPIRE_MINUTES**: JWT token expiration time in minutes (default: 30)
- **LOG_LEVEL**: Logging level (default: INFO)
- **SENTRY_DSN**: Sentry DSN for error tracking
- **SMTP_SERVER**, **SMTP_PORT**, **SMTP_USER**, **SMTP_PASSWORD**: SMTP configuration for email sending

Refer to `.env.example` for a complete list of environment variables.

## Quick Start

### Prerequisites

- Python 3.9+
- PostgreSQL
- Redis (optional)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/sparkr.git
   cd sparkr
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

5. Run the application:
   ```bash
   python app/main.py
   ```

6. Access the API at http://localhost:8000/api/v1

## Using the Shared Library

Sparkr uses a shared library for common functionality with the Social Suit project. To install the shared library:

```bash
cd ../shared
pip install -e .
```

Refer to the shared library documentation for more details.