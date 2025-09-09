# Configuration variables
$APP_NAME = "sparkr-backend"
$REGISTRY = "your-registry.com"  # Change to your registry (e.g., ghcr.io, docker.io, etc.)
$ENV_FILE = ".env.production"    # Path to your production env file

# Default values
$VERSION = "latest"
$DEPLOY_TARGET = $null
$SKIP_MIGRATIONS = $false
$SKIP_BUILD = $false
$SKIP_PUSH = $false

# Parse command line arguments
for ($i = 0; $i -lt $args.Count; $i++) {
    switch ($args[$i]) {
        "--version" {
            $VERSION = $args[++$i]
        }
        "--target" {
            $DEPLOY_TARGET = $args[++$i]
        }
        "--skip-migrations" {
            $SKIP_MIGRATIONS = $true
        }
        "--skip-build" {
            $SKIP_BUILD = $true
        }
        "--skip-push" {
            $SKIP_PUSH = $true
        }
        "--help" {
            Write-Host "Usage: .\deploy.ps1 --version VERSION --target [render|fly|docker] [--skip-migrations] [--skip-build] [--skip-push]"
            Write-Host "  --version VERSION   The version tag for the Docker image (default: latest)"
            Write-Host "  --target TARGET     The deployment target (render, fly, or docker)"
            Write-Host "  --skip-migrations   Skip running database migrations"
            Write-Host "  --skip-build        Skip building the Docker image"
            Write-Host "  --skip-push         Skip pushing the Docker image"
            exit
        }
    }
}

if (-not $DEPLOY_TARGET) {
    Write-Host "Error: --target is required" -ForegroundColor Red
    Write-Host "Usage: .\deploy.ps1 --version VERSION --target [render|fly|docker] [--skip-migrations] [--skip-build] [--skip-push]"
    exit 1
}

# Validate that the .env file exists
if (-not (Test-Path $ENV_FILE)) {
    Write-Host "Error: Environment file $ENV_FILE not found" -ForegroundColor Red
    exit 1
}

# Load environment variables from .env file
$envContent = Get-Content $ENV_FILE
foreach ($line in $envContent) {
    if ($line -match '^([^#][^=]+)=(.*)$') {
        $name = $matches[1].Trim()
        $value = $matches[2].Trim()
        [Environment]::SetEnvironmentVariable($name, $value, "Process")
    }
}

Write-Host "🚀 Deploying $APP_NAME version $VERSION to $DEPLOY_TARGET" -ForegroundColor Cyan

# Run database migrations
if (-not $SKIP_MIGRATIONS) {
    Write-Host "\n📊 Running database migrations..." -ForegroundColor Cyan
    
    # For local development
    if ($DEPLOY_TARGET -eq "docker") {
        docker-compose run --rm app alembic upgrade head
    }
    # For Render
    elseif ($DEPLOY_TARGET -eq "render") {
        # Render automatically runs migrations via the start command
        Write-Host "Migrations will be run automatically on Render deployment"
    }
    # For Fly.io
    elseif ($DEPLOY_TARGET -eq "fly") {
        fly ssh console -C "cd /app && alembic upgrade head"
    }
    
    Write-Host "✅ Migrations completed" -ForegroundColor Green
}

# Build Docker image
if (-not $SKIP_BUILD) {
    Write-Host "\n🔨 Building Docker image..." -ForegroundColor Cyan
    docker build -t "$REGISTRY/$APP_NAME:$VERSION" .
    
    # Also tag as latest if version is not already latest
    if ($VERSION -ne "latest") {
        docker tag "$REGISTRY/$APP_NAME:$VERSION" "$REGISTRY/$APP_NAME:latest"
    }
    
    Write-Host "✅ Docker image built" -ForegroundColor Green
}

# Push Docker image to registry
if (-not $SKIP_PUSH) {
    Write-Host "\n📤 Pushing Docker image to registry..." -ForegroundColor Cyan
    docker push "$REGISTRY/$APP_NAME:$VERSION"
    
    # Also push latest tag if version is not already latest
    if ($VERSION -ne "latest") {
        docker push "$REGISTRY/$APP_NAME:latest"
    }
    
    Write-Host "✅ Docker image pushed to registry" -ForegroundColor Green
}

# Deploy to specific platform
Write-Host "\n🚀 Deploying to $DEPLOY_TARGET..." -ForegroundColor Cyan

switch ($DEPLOY_TARGET) {
    "render" {
        Write-Host "📝 For Render deployment:" -ForegroundColor Yellow
        Write-Host "1. Go to your Render dashboard"
        Write-Host "2. Select your service"
        Write-Host "3. Click 'Manual Deploy' and select 'Clear build cache & deploy'"
        Write-Host "4. Or set up Render to automatically deploy on push to your repository"
    }
    
    "fly" {
        Write-Host "📝 Deploying to Fly.io..." -ForegroundColor Yellow
        fly deploy --image="$REGISTRY/$APP_NAME:$VERSION"
        Write-Host "✅ Deployed to Fly.io" -ForegroundColor Green
    }
    
    "docker" {
        Write-Host "📝 For deployment to a generic Docker host:" -ForegroundColor Yellow
        Write-Host "Run the following command on your server:"
        Write-Host "docker pull $REGISTRY/$APP_NAME:$VERSION"
        Write-Host "docker stop $APP_NAME || true"
        Write-Host "docker rm $APP_NAME || true"
        Write-Host "docker run -d --name $APP_NAME \\"
        Write-Host "  --restart unless-stopped \\"
        Write-Host "  -p 8000:8000 \\"
        Write-Host "  --env-file /path/to/your/.env \\"
        Write-Host "  $REGISTRY/$APP_NAME:$VERSION"
    }
    
    default {
        Write-Host "❌ Unknown deployment target: $DEPLOY_TARGET" -ForegroundColor Red
        exit 1
    }
}

Write-Host "\n✅ Deployment process completed!" -ForegroundColor Green