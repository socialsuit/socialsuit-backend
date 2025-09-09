# Environment Variable Matrix

This document provides a consolidated view of environment variables used across Social Suit and Sparkr projects.

## Environment Variables Comparison

| Variable | Social Suit | Sparkr | Notes |
|----------|------------|--------|-------|
| **Database** |
| DATABASE_URL | ✅ | ✅ | Different connection strings: PostgreSQL standard in Social Suit, asyncpg in Sparkr |
| **Redis** |
| REDIS_URL | ✅ | ❌ | Social Suit uses a single URL |
| REDIS_HOST | ❌ | ✅ | Sparkr uses individual connection parameters |
| REDIS_PORT | ❌ | ✅ | Sparkr uses individual connection parameters |
| REDIS_PASSWORD | ❌ | ✅ | Sparkr uses individual connection parameters |
| REDIS_DB | ❌ | ✅ | Sparkr uses individual connection parameters |
| **Authentication** |
| JWT_SECRET | ✅ | ✅ | Same purpose in both projects |
| JWT_ALGORITHM | ❌ | ✅ | Only in Sparkr, defaults to HS256 |
| ACCESS_TOKEN_EXPIRE_MINUTES | ❌ | ✅ | Only in Sparkr, defaults to 30 |
| **API Configuration** |
| API_V1_PREFIX | ❌ | ✅ | Only in Sparkr |
| BACKEND_CORS_ORIGINS | ❌ | ✅ | Only in Sparkr |
| **External Services** |
| OPENROUTER_API_KEY | ✅ | ❌ | Only in Social Suit |
| SDXL_API_KEY | ✅ | ❌ | Only in Social Suit |
| MONGO_URL | ✅ | ❌ | Only in Social Suit |
| **Media Storage** |
| CLOUDINARY_CLOUD_NAME | ✅ | ❌ | Only in Social Suit |
| CLOUDINARY_API_KEY | ✅ | ❌ | Only in Social Suit |
| CLOUDINARY_API_SECRET | ✅ | ❌ | Only in Social Suit |
| **Social Media Integration** |
| META_CLIENT_ID | ✅ | ❌ | Only in Social Suit |
| META_REDIRECT_URI | ✅ | ❌ | Only in Social Suit |
| LINKEDIN_CLIENT_ID | ✅ | ❌ | Only in Social Suit |
| LINKEDIN_REDIRECT_URI | ✅ | ❌ | Only in Social Suit |
| YOUTUBE_CLIENT_ID | ✅ | ❌ | Only in Social Suit |
| YOUTUBE_REDIRECT_URI | ✅ | ❌ | Only in Social Suit |
| TIKTOK_CLIENT_KEY | ✅ | ❌ | Only in Social Suit |
| TIKTOK_REDIRECT_URI | ✅ | ❌ | Only in Social Suit |
| **Logging** |
| LOG_LEVEL | ❌ | ✅ | Only in Sparkr |
| **Optional Services** |
| SENTRY_DSN | ❌ | ✅ | Only in Sparkr |
| SMTP_SERVER | ❌ | ✅ | Only in Sparkr |
| SMTP_PORT | ❌ | ✅ | Only in Sparkr |
| SMTP_USER | ❌ | ✅ | Only in Sparkr |
| SMTP_PASSWORD | ❌ | ✅ | Only in Sparkr |

## Shared Environment Variables

The following environment variables are used in both projects and could potentially be standardized in the shared library:

1. **DATABASE_URL**: Consider standardizing the connection string format or providing helpers in the shared library to handle both synchronous and asynchronous connections.

2. **JWT_SECRET**: Both projects use JWT for authentication. The shared library's `JWTAuth` class can be configured to use this environment variable.

## Project-Specific Environment Variables

### Social Suit Specific

- External API keys (OPENROUTER_API_KEY, SDXL_API_KEY)
- MongoDB connection (MONGO_URL)
- Cloudinary configuration
- Social media integration keys

### Sparkr Specific

- Detailed API configuration (API_V1_PREFIX, BACKEND_CORS_ORIGINS)
- Detailed JWT configuration (JWT_ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES)
- Logging configuration
- Error tracking and email services

## Recommendations

1. **Standardize Redis Configuration**: Consider updating Social Suit to use individual Redis connection parameters instead of a single URL, or provide helpers in the shared library to handle both formats.

2. **Standardize JWT Configuration**: Move JWT configuration to the shared library and standardize the environment variable names.

3. **Environment Variable Loading**: Use the shared library's `ConfigLoader` to load environment variables in both projects, providing consistent behavior and default values.