# Structured Logging Formats

This document provides examples of structured log formats used in our applications, which are compatible with Kibana and Grafana.

## Log Format Structure

Our structured logs use a JSON format with the following standard fields:

| Field | Description |
|-------|-------------|
| `@timestamp` | ISO 8601 timestamp in UTC |
| `message` | The log message |
| `logger` | The name of the logger |
| `service` | The name of the service |
| `environment` | The environment (e.g., production, staging) |
| `level` | The log level (e.g., INFO, ERROR) |
| `level_number` | The numeric log level |
| `correlation_id` | The request correlation ID |
| `host` | The hostname of the server |

## Sample Log Lines

### Standard Info Log

```json
{
  "@timestamp": "2023-06-15T12:34:56.789Z",
  "message": "User login successful",
  "logger": "auth.service",
  "service": "user-service",
  "environment": "production",
  "level": "INFO",
  "level_number": 20,
  "correlation_id": "c0ff33-b33f-f00d-cafe-deadbeef1234",
  "host": "app-server-01",
  "user_id": "user123",
  "ip_address": "192.168.1.1"
}
```

### Error Log with Exception

```json
{
  "@timestamp": "2023-06-15T12:35:22.123Z",
  "message": "Failed to process payment",
  "logger": "payment.service",
  "service": "payment-service",
  "environment": "production",
  "level": "ERROR",
  "level_number": 40,
  "correlation_id": "c0ff33-b33f-f00d-cafe-deadbeef5678",
  "host": "app-server-02",
  "exception": "Traceback (most recent call last):\n  File \"payment.py\", line 42, in process_payment\n    response = payment_gateway.charge(amount)\nPaymentGatewayError: Insufficient funds",
  "user_id": "user456",
  "payment_id": "pmt_789",
  "amount": 99.99,
  "currency": "USD"
}
```

### Request Log with Correlation ID

```json
{
  "@timestamp": "2023-06-15T12:36:15.456Z",
  "message": "HTTP request processed",
  "logger": "middleware.request",
  "service": "api-gateway",
  "environment": "production",
  "level": "INFO",
  "level_number": 20,
  "correlation_id": "c0ff33-b33f-f00d-cafe-deadbeef9012",
  "host": "api-server-01",
  "method": "POST",
  "path": "/api/v1/orders",
  "status_code": 201,
  "duration_ms": 125,
  "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
  "ip_address": "192.168.1.2"
}
```

### Rate Limit Log

```json
{
  "@timestamp": "2023-06-15T12:37:01.789Z",
  "message": "Rate limit exceeded",
  "logger": "middleware.rate_limiter",
  "service": "api-gateway",
  "environment": "production",
  "level": "WARNING",
  "level_number": 30,
  "correlation_id": "c0ff33-b33f-f00d-cafe-deadbeef3456",
  "host": "api-server-01",
  "method": "GET",
  "path": "/api/v1/products",
  "ip_address": "192.168.1.3",
  "rate_limit": 100,
  "current_count": 101
}
```

### Health Check Log

```json
{
  "@timestamp": "2023-06-15T12:38:00.123Z",
  "message": "Health check performed",
  "logger": "middleware.health",
  "service": "user-service",
  "environment": "production",
  "level": "INFO",
  "level_number": 20,
  "correlation_id": "health-check-c0ff33-b33f-f00d-cafe-deadbeef7890",
  "host": "app-server-01",
  "check_type": "readiness",
  "status": "healthy",
  "duration_ms": 15,
  "checks": {
    "database": "ok",
    "redis": "ok",
    "external_api": "ok"
  }
}
```

## Kibana/Grafana Integration

### Kibana Index Pattern

When setting up Kibana, create an index pattern that matches your log indices. For example, if your logs are stored in indices named `logs-*`, create an index pattern with that name.

### Useful Kibana Queries

- Find all logs for a specific correlation ID:
  ```
  correlation_id: "c0ff33-b33f-f00d-cafe-deadbeef1234"
  ```

- Find all error logs:
  ```
  level: "ERROR"
  ```

- Find all logs for a specific service and environment:
  ```
  service: "user-service" AND environment: "production"
  ```

- Find all rate limit exceeded warnings:
  ```
  message: "Rate limit exceeded" AND level: "WARNING"
  ```

### Grafana Dashboard Examples

1. **Request Volume Dashboard**
   - Graph of requests per minute
   - Breakdown by endpoint
   - Filter by service and environment

2. **Error Rate Dashboard**
   - Error count over time
   - Top error types
   - Correlation ID links to detailed logs

3. **Performance Dashboard**
   - Request duration percentiles
   - Slowest endpoints
   - Database query times

4. **Health Check Dashboard**
   - Current status of all services
   - History of health check results
   - Alert on failed health checks