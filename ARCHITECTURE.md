# Project Architecture Documentation

## Overview

This document describes the architecture of the separated Social Suit and Sparkr projects, along with the shared library that contains common components. The separation was performed to improve maintainability, reduce code duplication, and allow independent development of each project.

## Project Structure

The codebase is organized into three main components:

```
├── social-suit/       # Social media management platform
├── sparkr/            # Campaign and task management platform
└── shared/            # Shared library used by both projects
```

### Social Suit

Social Suit is a social media management platform with the following components:

```
├── social-suit/
│   ├── services/             # Service modules
│   │   ├── api/              # API endpoints
│   │   ├── models/           # Data models
│   │   ├── tasks/            # Background tasks
│   │   └── ...
│   ├── tests/                # Test suite
│   ├── main.py               # Application entry point
│   ├── celery_app.py         # Celery configuration
│   ├── requirements.txt      # Dependencies
│   ├── Dockerfile            # Container definition
│   └── docker-compose.yml    # Container orchestration
```

### Sparkr

Sparkr is a campaign and task management platform with the following components:

```
├── sparkr/
│   ├── app/                  # Application code
│   │   ├── api/              # API endpoints
│   │   ├── models/           # Data models
│   │   ├── core/             # Core functionality
│   │   └── ...
│   ├── tests/                # Test suite
│   ├── main.py               # Application entry point
│   ├── requirements.txt      # Dependencies
│   ├── Dockerfile            # Container definition
│   ├── docker-compose.yml    # Container orchestration
│   └── fly.toml              # Fly.io deployment configuration
```

### Shared Library

The shared library contains components used by both Social Suit and Sparkr:

```
├── shared/
│   ├── auth/                 # Authentication utilities
│   │   ├── jwt.py            # JWT handling
│   │   └── ...
│   ├── database/             # Database utilities
│   │   ├── connection.py     # Connection management
│   │   └── ...
│   ├── utils/                # Utility functions
│   │   ├── datetime.py       # Date/time utilities
│   │   └── ...
│   └── README.md             # Documentation
```

## Key Components

### Authentication

Both projects use JWT-based authentication, with common utilities in the shared library:

- Token generation and validation
- Password hashing and verification
- User authentication flows

### Database

The projects use different ORM approaches:

- Social Suit: SQLAlchemy with `declarative_base`
- Sparkr: SQLModel (built on SQLAlchemy)

Common database utilities are in the shared library:

- Connection management
- Transaction handling
- Migration utilities

### API Structure

- Social Suit: FastAPI with routers in `services/endpoint`
- Sparkr: FastAPI with routers in `app/api/v1`

### Background Tasks

- Social Suit: Celery with Redis as the message broker
- Sparkr: Celery with Redis as the message broker

## Dependencies

### Social Suit Dependencies

Key dependencies include:

- FastAPI
- SQLAlchemy
- Celery
- Redis
- Various Google API client libraries

### Sparkr Dependencies

Key dependencies include:

- FastAPI
- SQLModel
- Celery
- Redis
- Alembic for migrations

### Shared Dependencies

Dependencies required by the shared library:

- SQLAlchemy (core)
- Pydantic
- Python-jose (JWT)
- Passlib (password hashing)

## Migration Process

The migration from the monorepo to the separated projects involved the following steps:

1. **Project Separation**
   - Created the three main directories: `social-suit`, `sparkr`, and `shared`
   - Moved Social Suit files to the `social-suit` directory
   - Moved Sparkr files from `sparkr-backend` to the `sparkr` directory

2. **Shared Component Extraction**
   - Identified common components used by both projects
   - Extracted these components to the `shared` library
   - Created a clear structure for the shared components

3. **Import Path Updates**
   - Updated import statements in both projects to reference the shared library
   - Ensured that all imports resolve correctly

4. **Verification**
   - Verified that all files are in the correct locations
   - Checked that Python syntax is valid in all files
   - Verified that imports resolve correctly
   - Ran tests to ensure functionality is preserved

## Best Practices

### Shared Library Development

1. **Versioning**
   - Use semantic versioning for the shared library
   - Document breaking changes clearly

2. **Ownership**
   - Establish clear ownership for shared components
   - Define contribution guidelines

3. **Testing**
   - Write comprehensive tests for shared components
   - Ensure backward compatibility

### Project-Specific Development

1. **Independence**
   - Keep project-specific code in the respective project directories
   - Avoid creating dependencies between projects

2. **Consistency**
   - Follow consistent coding standards across projects
   - Use similar patterns for similar functionality

3. **Documentation**
   - Document project-specific features
   - Keep documentation up to date

### Deployment

1. **Containerization**
   - Use Docker for consistent environments
   - Define separate Docker Compose configurations for each project

2. **CI/CD**
   - Set up CI/CD pipelines for each project
   - Include tests for the shared library in both pipelines

3. **Monitoring**
   - Implement monitoring for each project
   - Track usage of shared components

## Maintenance Strategy

### Regular Reviews

- Conduct regular code reviews
- Review shared components for potential improvements
- Identify opportunities for further separation or consolidation

### Dependency Management

- Keep dependencies up to date
- Ensure compatibility between projects and the shared library
- Document dependency changes

### Documentation

- Keep architecture documentation up to date
- Document changes to the shared library
- Maintain clear usage examples

## Conclusion

The separation of Social Suit and Sparkr into distinct projects with a shared library improves maintainability, reduces code duplication, and allows for independent development. By following the best practices outlined in this document, the projects can continue to evolve while maintaining the benefits of code sharing where appropriate.