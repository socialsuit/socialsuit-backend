# Monitoring and Logging System

A comprehensive monitoring, logging, and alerting solution for the Social Suit application using `loguru` for structured logging, performance monitoring, and automated alerting.

## Features

### 🔍 Structured Logging
- **JSON-formatted logs** for easy parsing and analysis
- **Multiple log levels** (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- **Event categorization** (API, SECURITY, BACKGROUND_TASK, etc.)
- **Automatic log rotation** and retention
- **Performance metrics** tracking
- **Context-aware logging** with request IDs and user information

### 🚨 Alerting System
- **Multiple alert channels** (Email, Webhook/Slack/Discord)
- **Configurable alert rules** with severity levels
- **Alert cooldowns** to prevent spam
- **Background task failure monitoring**
- **API performance degradation alerts**
- **High error rate detection**

### 📊 Performance Monitoring
- **Request/response time tracking**
- **Background task monitoring**
- **System resource usage**
- **Error rate monitoring**
- **Performance summaries and reports**

### 🛡️ Security Event Logging
- **Security event categorization**
- **Failed authentication tracking**
- **Suspicious activity detection**
- **Audit trail maintenance**

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements_monitoring.txt
```

### 2. Basic Setup

```python
from services.monitoring import setup_monitoring
from fastapi import FastAPI

app = FastAPI()

# Quick setup with email and webhook alerts
monitoring = setup_monitoring(
    app=app,
    email_config={
        "smtp_host": "smtp.gmail.com",
        "smtp_port": 587,
        "username": "your-email@gmail.com",
        "password": "your-app-password",
        "from_email": "your-email@gmail.com",
        "to_emails": ["admin@yourcompany.com"]
    },
    webhook_url="https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK",
    enable_middleware=True
)
```

### 3. Using Structured Logging

```python
from services.monitoring import structured_logger, LogLevel, EventType

# Basic structured logging
structured_logger.log_structured(
    LogLevel.INFO,
    "User logged in successfully",
    EventType.SECURITY,
    user_id="user123",
    ip_address="192.168.1.1"
)

# API request logging (automatic with middleware)
structured_logger.log_api_request(
    method="POST",
    endpoint="/api/users",
    user_id="user123",
    status_code=201,
    response_time=0.145
)

# Error logging with context
try:
    # Some operation
    pass
except Exception as e:
    structured_logger.log_error(
        e,
        context={"user_id": "user123", "operation": "create_post"}
    )
```

### 4. Performance Monitoring

```python
from services.monitoring import log_performance, log_operation

# Decorator for automatic performance logging
@log_performance
async def expensive_operation():
    # Your code here
    return result

# Context manager for operation tracking
with log_operation("data_processing"):
    # Your code here
    pass
```

### 5. Background Task Monitoring

```python
from services.monitoring import BackgroundTaskMonitoringMixin

class TaskManager(BackgroundTaskMonitoringMixin):
    async def process_data(self, data_id: str):
        try:
            # Your task logic
            result = await self.do_processing(data_id)
            return result
        except Exception as e:
            # Automatic alert on failure
            await self.handle_task_failure("process_data", str(e))
            raise
```

## Configuration

### Log Configuration

Logs are automatically configured with the following structure:

```
logs/
├── app.log          # Human-readable application logs
├── app.json         # Structured JSON logs
├── performance.json # Performance metrics
└── errors.log       # Error-only logs
```

### Alert Configuration

```python
from services.monitoring import alert_manager, AlertRule, AlertSeverity, AlertType

# Add custom alert rule
alert_manager.add_rule(AlertRule(
    name="high_memory_usage",
    alert_type=AlertType.PERFORMANCE,
    severity=AlertSeverity.WARNING,
    condition=lambda: get_memory_usage() > 0.8,
    cooldown_minutes=15
))
```

### Email Alert Setup

```python
from services.monitoring import EmailAlertChannel

email_channel = EmailAlertChannel(
    smtp_host="smtp.gmail.com",
    smtp_port=587,
    username="your-email@gmail.com",
    password="your-app-password",  # Use app password for Gmail
    from_email="your-email@gmail.com",
    to_emails=["admin@yourcompany.com", "dev@yourcompany.com"]
)

alert_manager.add_channel(email_channel)
```

### Webhook/Slack Alert Setup

```python
from services.monitoring import WebhookAlertChannel

# For Slack
slack_channel = WebhookAlertChannel(
    webhook_url="https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"
)

# For Discord
discord_channel = WebhookAlertChannel(
    webhook_url="https://discord.com/api/webhooks/YOUR/DISCORD/WEBHOOK"
)

alert_manager.add_channel(slack_channel)
```

## API Endpoints

When middleware is enabled, the following endpoints are automatically available:

- `GET /health` - Health check endpoint
- `GET /metrics` - Performance and error metrics

## Log Format

### Structured JSON Logs

```json
{
  "timestamp": "2024-01-10T15:30:45.123456Z",
  "level": "INFO",
  "message": "User logged in successfully",
  "event_type": "SECURITY",
  "request_id": "req_123456",
  "user_id": "user123",
  "ip_address": "192.168.1.1",
  "context": {
    "additional": "data"
  }
}
```

### Performance Logs

```json
{
  "timestamp": "2024-01-10T15:30:45.123456Z",
  "operation": "api_request",
  "duration": 0.145,
  "success": true,
  "endpoint": "/api/users",
  "method": "POST",
  "status_code": 201,
  "user_id": "user123"
}
```

## Testing

Run the monitoring system tests:

```bash
python test_monitoring.py
```

This will test:
- Structured logging functionality
- Performance monitoring
- Alerting system
- Log file creation
- Performance summaries

## Example Integration

See `examples/monitoring_setup.py` for a complete FastAPI integration example.

## Best Practices

### 1. Use Appropriate Log Levels
- `DEBUG`: Detailed diagnostic information
- `INFO`: General application flow
- `WARNING`: Something unexpected happened
- `ERROR`: Serious problem occurred
- `CRITICAL`: Very serious error occurred

### 2. Include Context
Always include relevant context in your logs:

```python
structured_logger.log_structured(
    LogLevel.INFO,
    "Order processed successfully",
    EventType.BUSINESS_LOGIC,
    user_id=user_id,
    order_id=order_id,
    amount=order.amount,
    payment_method=order.payment_method
)
```

### 3. Monitor Critical Operations
Use performance monitoring for critical operations:

```python
@log_performance
async def critical_database_operation():
    # Your database operation
    pass
```

### 4. Set Up Appropriate Alerts
Configure alerts for critical failures:

```python
# Alert on background task failures
await alert_background_task_failure(
    task_name="payment_processing",
    error_message=str(error),
    context={"user_id": user_id, "amount": amount}
)
```

### 5. Regular Monitoring
- Check `/health` endpoint regularly
- Monitor `/metrics` for performance trends
- Review error logs daily
- Set up dashboard for key metrics

## Troubleshooting

### Common Issues

1. **Logs not appearing**: Check file permissions in the `logs/` directory
2. **Email alerts not working**: Verify SMTP settings and app passwords
3. **High memory usage**: Adjust log retention settings
4. **Missing performance data**: Ensure decorators and middleware are properly applied

### Debug Mode

Enable debug logging for troubleshooting:

```python
structured_logger.log_structured(
    LogLevel.DEBUG,
    "Debug information",
    EventType.SYSTEM,
    debug_data={"key": "value"}
)
```

## Performance Considerations

- Log files are automatically rotated to prevent disk space issues
- JSON logs are optimized for parsing performance
- Alert cooldowns prevent notification spam
- Performance metrics are aggregated to reduce overhead

## Security

- Sensitive data is automatically filtered from logs
- Security events are logged with appropriate detail
- Alert channels use secure communication protocols
- Log files have restricted permissions

## Contributing

When adding new monitoring features:

1. Follow the existing log structure
2. Add appropriate tests
3. Update documentation
4. Consider performance impact
5. Test alert functionality

## License

This monitoring system is part of the Social Suit application.