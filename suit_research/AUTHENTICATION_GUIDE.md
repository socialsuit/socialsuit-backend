# Authentication System Guide

## Overview

The Suit Research API implements a comprehensive authentication system with:

- **API Key Authentication** with hashed storage and rotation
- **OAuth2 Client Credentials Flow** for JWT tokens
- **Scope-based Authorization** with granular permissions
- **Redis-based Rate Limiting** per API key
- **Secure Middleware** for request validation

## Authentication Methods

### 1. API Key Authentication

API keys provide direct access to the API with predefined scopes.

**Header Format:**
```
Authorization: ApiKey sk_your_api_key_here
```

**Features:**
- Secure hashing with SHA-256
- Automatic rotation support
- Per-key rate limiting
- Usage tracking
- Revocation capability

### 2. OAuth2 Client Credentials

OAuth2 flow for obtaining JWT tokens using API keys as client credentials.

**Token Request:**
```bash
curl -X POST http://localhost:8000/oauth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials&client_id=your_client_name&client_secret=your_api_key&scope=read:public read:funding"
```

**JWT Token Usage:**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## Available Scopes

| Scope | Description |
|-------|-------------|
| `read:public` | Read public project information |
| `read:funding` | Read funding round data |
| `read:investors` | Read investor information |
| `write:webhooks` | Create and manage webhooks |
| `admin` | Full administrative access |

## API Endpoints

### Authentication Management

#### Create API Key (Admin Only)
```http
POST /api/v1/auth/keys
Authorization: ApiKey <admin_key>
Content-Type: application/json

{
  "name": "client_name",
  "description": "Description of the API key",
  "scopes": ["read:public", "read:funding"]
}
```

**Response:**
```json
{
  "id": 1,
  "name": "client_name",
  "description": "Description of the API key",
  "scopes": ["read:public", "read:funding"],
  "created_at": "2024-01-15T10:30:00Z",
  "last_used_at": null,
  "revoked_at": null,
  "api_key": "sk_abc123def456..."
}
```

#### List API Keys (Admin Only)
```http
GET /api/v1/auth/keys
Authorization: ApiKey <admin_key>
```

#### Get API Key Details (Admin Only)
```http
GET /api/v1/auth/keys/{key_id}
Authorization: ApiKey <admin_key>
```

#### Revoke API Key (Admin Only)
```http
POST /api/v1/auth/keys/{key_id}/revoke
Authorization: ApiKey <admin_key>
Content-Type: application/json

{
  "revoke": true
}
```

#### List Available Scopes
```http
GET /api/v1/auth/scopes
```

#### Get Current Auth Context
```http
GET /api/v1/auth/me
Authorization: ApiKey <your_key> | Bearer <jwt_token>
```

### OAuth2 Endpoints

#### Get Access Token
```http
POST /oauth/token
Content-Type: application/x-www-form-urlencoded

grant_type=client_credentials&client_id=your_client_name&client_secret=your_api_key&scope=read:public
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "scope": "read:public"
}
```

## Protected Endpoints Examples

### Public Data (requires `read:public`)
```http
GET /api/v1/protected/public
Authorization: ApiKey <your_key>
```

### Funding Data (requires `read:funding`)
```http
GET /api/v1/protected/funding
Authorization: Bearer <jwt_token>
```

### Investor Data (requires `read:investors`)
```http
GET /api/v1/protected/investors
Authorization: ApiKey <your_key>
```

### Create Webhook (requires `write:webhooks`)
```http
POST /api/v1/protected/webhooks
Authorization: ApiKey <your_key>
Content-Type: application/json

{
  "url": "https://your-app.com/webhook",
  "events": ["funding.created", "project.updated"]
}
```

### Admin Statistics (requires `admin`)
```http
GET /api/v1/protected/admin/stats
Authorization: ApiKey <admin_key>
```

## Rate Limiting

- **Default Limit:** 1000 requests per hour per API key
- **Window:** Sliding window of 1 hour
- **Storage:** Redis-based with automatic cleanup
- **Response:** HTTP 429 with `Retry-After` header

## Security Features

### API Key Security
- Keys are hashed using SHA-256 before storage
- Original keys are never stored in the database
- Secure comparison using `hmac.compare_digest()`
- Automatic revocation support

### JWT Security
- Signed with HS256 algorithm
- Configurable expiration time
- Includes issued-at timestamp
- Proper error handling for expired/invalid tokens

### Middleware Protection
- Automatic authentication on protected routes
- Scope validation before endpoint access
- Rate limiting enforcement
- Comprehensive error responses

## Usage Examples

### Python Client Example
```python
import httpx

# Using API Key
headers = {"Authorization": "ApiKey sk_your_key_here"}
response = httpx.get("http://localhost:8000/api/v1/protected/public", headers=headers)

# Using OAuth2 JWT
token_response = httpx.post("http://localhost:8000/oauth/token", data={
    "grant_type": "client_credentials",
    "client_id": "your_client",
    "client_secret": "sk_your_key_here",
    "scope": "read:public read:funding"
})
token = token_response.json()["access_token"]

headers = {"Authorization": f"Bearer {token}"}
response = httpx.get("http://localhost:8000/api/v1/protected/funding", headers=headers)
```

### JavaScript Client Example
```javascript
// Using API Key
const response = await fetch('http://localhost:8000/api/v1/protected/public', {
  headers: {
    'Authorization': 'ApiKey sk_your_key_here'
  }
});

// Using OAuth2 JWT
const tokenResponse = await fetch('http://localhost:8000/oauth/token', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/x-www-form-urlencoded'
  },
  body: 'grant_type=client_credentials&client_id=your_client&client_secret=sk_your_key_here&scope=read:public'
});
const { access_token } = await tokenResponse.json();

const dataResponse = await fetch('http://localhost:8000/api/v1/protected/public', {
  headers: {
    'Authorization': `Bearer ${access_token}`
  }
});
```

## Error Responses

### Authentication Errors (401)
```json
{
  "detail": "Authentication required"
}
```

### Authorization Errors (403)
```json
{
  "detail": "Missing required scope: read:funding"
}
```

### Rate Limit Errors (429)
```json
{
  "detail": "Rate limit exceeded"
}
```

## Testing

Run the comprehensive test suite:

```bash
# Start the server
python start_dev.py

# In another terminal, run tests
python test_auth_system.py
```

The test suite covers:
- ✅ Admin API key setup
- ✅ Scope listing
- ✅ API key creation and management
- ✅ OAuth2 token flow
- ✅ Protected endpoint access
- ✅ Authentication context
- ✅ Rate limiting

## Configuration

Add to your `.env` file:

```env
# JWT Configuration
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=480

# Redis for rate limiting
REDIS_URL=redis://localhost:6379/0
```

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Client App    │───▶│  Auth Middleware │───▶│  Protected API  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │  Rate Limiter    │
                       │     (Redis)      │
                       └──────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │   Database       │
                       │  (API Keys)      │
                       └──────────────────┘
```

## Best Practices

1. **API Key Management**
   - Store keys securely on client side
   - Rotate keys regularly
   - Use minimal required scopes
   - Monitor usage patterns

2. **OAuth2 Usage**
   - Use short-lived tokens
   - Implement token refresh if needed
   - Validate scopes on each request

3. **Rate Limiting**
   - Implement client-side rate limiting
   - Handle 429 responses gracefully
   - Use exponential backoff for retries

4. **Security**
   - Use HTTPS in production
   - Validate all input data
   - Log authentication events
   - Monitor for suspicious activity

The authentication system is now fully implemented and ready for production use! 🚀