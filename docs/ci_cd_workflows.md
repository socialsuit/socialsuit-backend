# CI/CD Workflows Documentation

## Overview

This repository uses GitHub Actions for continuous integration and continuous deployment (CI/CD). We have separate workflows for each project:

1. **Social Suit CI** - For the Social Suit application
2. **Sparkr Backend CI** - For the Sparkr Backend application

Each workflow follows a similar pattern with the following stages:

1. **Lint** - Code quality checks
2. **Test** - Run tests with coverage reporting
3. **Build** - Build Docker images
4. **Push** (optional) - Push Docker images to registry

## Workflow Details

### Social Suit CI

Location: `.github/workflows/ci.yml`

This workflow runs on:
- Push to main, master, or develop branches
- Pull requests to main, master, or develop branches
- Only when files in the `social-suit/` directory or the workflow file itself changes

#### Jobs

1. **Lint**
   - Sets up Python 3.10
   - Installs linting tools (flake8, black, isort)
   - Runs linting checks

2. **Test**
   - Runs after lint job completes
   - Sets up services:
     - PostgreSQL 13
     - Redis 6
   - Runs database migrations
   - Runs tests with coverage reporting
   - Uploads coverage report as an artifact
   - Generates and uploads OpenAPI spec as an artifact

3. **Build**
   - Runs after test job completes
   - Builds Docker image with BuildX
   - Tests the built image
   - Conditionally pushes to Docker Hub if:
     - Not a pull request
     - On main or master branch

### Sparkr Backend CI

Location: `.github/workflows/ci.yml`

This workflow runs on:
- Push to main, master, or develop branches
- Pull requests to main, master, or develop branches

#### Jobs

1. **Lint**
   - Sets up Python 3.11
   - Installs linting tools (ruff, flake8)
   - Runs linting checks

2. **Test**
   - Sets up services:
     - PostgreSQL 15
     - Redis 7
   - Runs tests with coverage reporting
   - Uploads coverage to Codecov
   - Generates and uploads OpenAPI spec as an artifact

3. **Build**
   - Runs after lint and test jobs complete
   - Builds Docker image with BuildX
   - Tests the built image
   - Conditionally pushes to Docker Hub if:
     - Not a pull request
     - On main or master branch

## Artifacts

Both workflows generate and store the following artifacts:

1. **Coverage Reports** - Test coverage data in XML format
2. **OpenAPI Specs** - Generated OpenAPI JSON files
3. **Docker Images** - Built and optionally pushed to Docker Hub

## Environment Variables and Secrets

The workflows use the following secrets:

- `DOCKERHUB_USERNAME` - Docker Hub username for pushing images
- `DOCKERHUB_TOKEN` - Docker Hub access token for authentication

## How to Use

### Viewing Workflow Status

1. Go to the "Actions" tab in your GitHub repository
2. Select the workflow you want to view
3. See the status of current and past workflow runs

### Adding Badges to README

See the `badges.md` file for instructions on adding workflow status badges to your README files.

### Customizing Workflows

You can customize these workflows by editing the YAML files:

- For Social Suit: `.github/workflows/ci.yml`
- For Sparkr Backend: `.github/workflows/ci.yml`

Common customizations include:

- Changing the Python version
- Adding or removing linting tools
- Modifying test environment variables
- Changing Docker image tags

## Troubleshooting

### Common Issues

1. **Workflow fails at lint stage**
   - Check the lint job logs for specific errors
   - Fix code style issues locally before pushing

2. **Tests fail**
   - Check the test job logs for specific test failures
   - Ensure database migrations are up to date
   - Verify environment variables are correctly set

3. **Docker build fails**
   - Check Dockerfile for errors
   - Ensure all required files are included in the build context

4. **Docker push fails**
   - Verify Docker Hub credentials are correctly set in repository secrets
   - Check if you have permission to push to the specified repository