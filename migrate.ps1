# PowerShell script to migrate the monorepo into separate projects

# Create the main directories if they don't exist
if (-not (Test-Path -Path "social-suit")) { New-Item -Path "social-suit" -ItemType Directory }
if (-not (Test-Path -Path "sparkr")) { New-Item -Path "sparkr" -ItemType Directory }
if (-not (Test-Path -Path "shared")) { New-Item -Path "shared" -ItemType Directory }

# Phase 1: Project Separation

# Step 1: Create necessary subdirectories in social-suit
Write-Host "Creating directories for Social Suit..." -ForegroundColor Green
if (-not (Test-Path -Path "social-suit\services")) { New-Item -Path "social-suit\services" -ItemType Directory }
if (-not (Test-Path -Path "social-suit\services\api")) { New-Item -Path "social-suit\services\api" -ItemType Directory }
if (-not (Test-Path -Path "social-suit\services\models")) { New-Item -Path "social-suit\services\models" -ItemType Directory }
if (-not (Test-Path -Path "social-suit\services\tasks")) { New-Item -Path "social-suit\services\tasks" -ItemType Directory }
if (-not (Test-Path -Path "social-suit\tests")) { New-Item -Path "social-suit\tests" -ItemType Directory }

# Step 2: Copy main.py, celery_app.py, and other root files to social-suit
Write-Host "Copying core files to Social Suit..." -ForegroundColor Green
if (Test-Path -Path "main.py") { Copy-Item -Path "main.py" -Destination "social-suit\" }
if (Test-Path -Path "celery_app.py") { Copy-Item -Path "celery_app.py" -Destination "social-suit\" }
if (Test-Path -Path "requirements.txt") { Copy-Item -Path "requirements.txt" -Destination "social-suit\" }
if (Test-Path -Path "Dockerfile") { Copy-Item -Path "Dockerfile" -Destination "social-suit\" }
if (Test-Path -Path "docker-compose.yml") { Copy-Item -Path "docker-compose.yml" -Destination "social-suit\" }

# Step 3: Copy services directory to social-suit
Write-Host "Copying services directory to Social Suit..." -ForegroundColor Green
if (Test-Path -Path "services") {
    Copy-Item -Path "services\*" -Destination "social-suit\services\" -Recurse -Force
}

# Step 4: Copy tests directory to social-suit
Write-Host "Copying tests directory to Social Suit..." -ForegroundColor Green
if (Test-Path -Path "tests") {
    Copy-Item -Path "tests\*" -Destination "social-suit\tests\" -Recurse -Force
}

# Step 5: Create necessary subdirectories in sparkr
Write-Host "Creating directories for Sparkr..." -ForegroundColor Green
if (-not (Test-Path -Path "sparkr\app")) { New-Item -Path "sparkr\app" -ItemType Directory }
if (-not (Test-Path -Path "sparkr\app\api")) { New-Item -Path "sparkr\app\api" -ItemType Directory }
if (-not (Test-Path -Path "sparkr\app\models")) { New-Item -Path "sparkr\app\models" -ItemType Directory }
if (-not (Test-Path -Path "sparkr\app\core")) { New-Item -Path "sparkr\app\core" -ItemType Directory }
if (-not (Test-Path -Path "sparkr\tests")) { New-Item -Path "sparkr\tests" -ItemType Directory }

# Step 6: Copy sparkr-backend files to sparkr
Write-Host "Copying files from sparkr-backend to Sparkr..." -ForegroundColor Green
if (Test-Path -Path "sparkr-backend\app") {
    Copy-Item -Path "sparkr-backend\app\*" -Destination "sparkr\app\" -Recurse -Force
}
if (Test-Path -Path "sparkr-backend\tests") {
    Copy-Item -Path "sparkr-backend\tests\*" -Destination "sparkr\tests\" -Recurse -Force
}
if (Test-Path -Path "sparkr-backend\requirements.txt") { Copy-Item -Path "sparkr-backend\requirements.txt" -Destination "sparkr\" }
if (Test-Path -Path "sparkr-backend\Dockerfile") { Copy-Item -Path "sparkr-backend\Dockerfile" -Destination "sparkr\" }
if (Test-Path -Path "sparkr-backend\docker-compose.yml") { Copy-Item -Path "sparkr-backend\docker-compose.yml" -Destination "sparkr\" }
if (Test-Path -Path "sparkr-backend\fly.toml") { Copy-Item -Path "sparkr-backend\fly.toml" -Destination "sparkr\" }

# Phase 2: Shared Component Extraction

# Step 1: Create necessary subdirectories in shared
Write-Host "Creating directories for shared components..." -ForegroundColor Green
if (-not (Test-Path -Path "shared\auth")) { New-Item -Path "shared\auth" -ItemType Directory }
if (-not (Test-Path -Path "shared\database")) { New-Item -Path "shared\database" -ItemType Directory }
if (-not (Test-Path -Path "shared\utils")) { New-Item -Path "shared\utils" -ItemType Directory }
if (-not (Test-Path -Path "shared\models")) { New-Item -Path "shared\models" -ItemType Directory }
if (-not (Test-Path -Path "shared\schemas")) { New-Item -Path "shared\schemas" -ItemType Directory }

# Step 2: Extract common components to shared library
Write-Host "Extracting shared components..." -ForegroundColor Green

# Note: The actual files to copy will depend on the specific shared components identified
# This is a placeholder for the actual extraction process

# Create a README for the shared library
Write-Host "Creating README for shared library..." -ForegroundColor Green
$sharedReadme = @"
# Shared Library

This library contains shared components used by both Social Suit and Sparkr projects.

## Components

- auth: Authentication utilities
- database: Database connection utilities
- models: Common data models
- schemas: Common schemas
- utils: Utility functions

## Usage

Import components from this library in both Social Suit and Sparkr projects.

Example:

```python
from shared.auth import authenticate_user
from shared.database import get_db_connection
```
"@

Set-Content -Path "shared\README.md" -Value $sharedReadme

# Create a README for the Social Suit project
Write-Host "Creating README for Social Suit..." -ForegroundColor Green
$socialSuitReadme = @"
# Social Suit

Social Suit is a comprehensive social media management platform.

## Features

- Authentication and user management
- Social media platform integrations
- Analytics and reporting
- Content scheduling and management

## Setup

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Run the application:
   ```
   uvicorn main:app --reload
   ```

## Docker

To run with Docker:

```
docker-compose up -d
```
"@

Set-Content -Path "social-suit\README.md" -Value $socialSuitReadme

# Create a README for the Sparkr project
Write-Host "Creating README for Sparkr..." -ForegroundColor Green
$sparkrReadme = @"
# Sparkr

Sparkr is a campaign and task management platform.

## Features

- User authentication
- Campaign management
- Task tracking
- Rewards and leaderboards

## Setup

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Run the application:
   ```
   uvicorn app.main:app --reload
   ```

## Docker

To run with Docker:

```
docker-compose up -d
```

## Deployment

This project is configured for deployment with Fly.io.
"@

Set-Content -Path "sparkr\README.md" -Value $sparkrReadme

Write-Host "Migration script completed!" -ForegroundColor Green
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Review the migrated files" -ForegroundColor Yellow
Write-Host "2. Identify and extract shared components" -ForegroundColor Yellow
Write-Host "3. Update import paths in both projects" -ForegroundColor Yellow
Write-Host "4. Test both projects to ensure they work correctly" -ForegroundColor Yellow