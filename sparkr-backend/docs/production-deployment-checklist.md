# Production Deployment Checklist

## Pre-Deployment Preparation

### Code and Repository
- [ ] All feature branches merged to main/master
- [ ] All tests passing (run `pytest`)
- [ ] Code linting and formatting checks passed
- [ ] Git tags created for release version (e.g., `git tag v1.0.0`)
- [ ] Changelog updated with new features and fixes

### Database
- [ ] Database migrations created and tested locally
- [ ] Backup of production database taken before deployment
- [ ] Migration rollback plan documented

### Environment Configuration
- [ ] All required environment variables documented
- [ ] Secrets rotated if necessary
- [ ] Environment-specific configurations reviewed

### Infrastructure
- [ ] Sufficient resources allocated (CPU, memory, disk)
- [ ] Scaling policies configured
- [ ] Monitoring and alerting set up
- [ ] Backup and recovery procedures documented

## Deployment Process

### Build and Push
- [ ] Docker image built with correct version tag
- [ ] Image pushed to container registry
- [ ] Image tagged with both version and latest tags

### Database Migration
- [ ] Alembic migrations run against production database
- [ ] Migration success verified

### Application Deployment
- [ ] New containers deployed with zero downtime strategy
- [ ] Health checks passing
- [ ] Application logs checked for errors

### Post-Deployment Verification
- [ ] Critical user flows tested in production
- [ ] API endpoints returning expected responses
- [ ] Performance metrics within expected ranges
- [ ] Error rates monitored for spikes

## Rollback Plan

### Triggers for Rollback
- [ ] Critical functionality broken
- [ ] Unacceptable performance degradation
- [ ] Security vulnerability discovered

### Rollback Process
- [ ] Revert to previous container image
- [ ] Run database down migrations if necessary
- [ ] Verify system functionality after rollback

## Environment Variables Checklist

### Database Configuration
- [ ] `DB_URL` - PostgreSQL connection string

### Redis Configuration
- [ ] `REDIS_URL` - Redis connection string

### API Settings
- [ ] `DEBUG` - Set to false in production
- [ ] `HOST` - Host to bind the application to
- [ ] `PORT` - Port to run the application on

### Security
- [ ] `SECRET_KEY` - Application secret key for JWT/session

### External APIs
- [ ] `TWITTER_BEARER` - Twitter API bearer token
- [ ] `TWITTER_CLIENT_ID` - Twitter OAuth client ID
- [ ] `TWITTER_CLIENT_SECRET` - Twitter OAuth client secret
- [ ] `IG_APP_ID` - Instagram app ID
- [ ] `IG_APP_SECRET` - Instagram app secret

### Monitoring and Logging
- [ ] `LOG_LEVEL` - Logging level (INFO, WARNING, ERROR)
- [ ] `SENTRY_DSN` - Sentry error tracking DSN

### Caching and Performance
- [ ] `CACHE_TTL` - Cache time-to-live in seconds

### Email and Notifications
- [ ] `SMTP_HOST` - SMTP server host
- [ ] `SMTP_PORT` - SMTP server port
- [ ] `SMTP_USER` - SMTP username
- [ ] `SMTP_PASSWORD` - SMTP password
- [ ] `EMAIL_FROM` - From email address