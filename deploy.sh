#!/bin/bash
set -e

# Configuration variables
APP_NAME="sparkr-backend"
REGISTRY="your-registry.com"  # Change to your registry (e.g., ghcr.io, docker.io, etc.)
ENV_FILE=".env.production"    # Path to your production env file

# Parse command line arguments
VERSION="latest"
DEPLOY_TARGET=""

print_usage() {
  echo "Usage: $0 --version VERSION --target [render|fly|docker] [--skip-migrations] [--skip-build] [--skip-push]"
  echo "  --version VERSION   The version tag for the Docker image (default: latest)"
  echo "  --target TARGET     The deployment target (render, fly, or docker)"
  echo "  --skip-migrations   Skip running database migrations"
  echo "  --skip-build        Skip building the Docker image"
  echo "  --skip-push         Skip pushing the Docker image"
  exit 1
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --version)
      VERSION="$2"
      shift 2
      ;;
    --target)
      DEPLOY_TARGET="$2"
      shift 2
      ;;
    --skip-migrations)
      SKIP_MIGRATIONS=true
      shift
      ;;
    --skip-build)
      SKIP_BUILD=true
      shift
      ;;
    --skip-push)
      SKIP_PUSH=true
      shift
      ;;
    --help)
      print_usage
      ;;
    *)
      echo "Unknown option: $1"
      print_usage
      ;;
  esac
done

if [ -z "$DEPLOY_TARGET" ]; then
  echo "Error: --target is required"
  print_usage
fi

# Validate that the .env file exists
if [ ! -f "$ENV_FILE" ]; then
  echo "Error: Environment file $ENV_FILE not found"
  exit 1
fi

# Load environment variables
set -a
source "$ENV_FILE"
set +a

echo "🚀 Deploying $APP_NAME version $VERSION to $DEPLOY_TARGET"

# Run database migrations
if [ "$SKIP_MIGRATIONS" != "true" ]; then
  echo "\n📊 Running database migrations..."
  
  # For local development
  if [ "$DEPLOY_TARGET" = "docker" ]; then
    docker-compose run --rm app alembic upgrade head
  
  # For Render
  elif [ "$DEPLOY_TARGET" = "render" ]; then
    # Render automatically runs migrations via the start command
    echo "Migrations will be run automatically on Render deployment"
  
  # For Fly.io
  elif [ "$DEPLOY_TARGET" = "fly" ]; then
    fly ssh console -C "cd /app && alembic upgrade head"
  fi
  
  echo "✅ Migrations completed"
fi

# Build Docker image
if [ "$SKIP_BUILD" != "true" ]; then
  echo "\n🔨 Building Docker image..."
  docker build -t "$REGISTRY/$APP_NAME:$VERSION" .
  
  # Also tag as latest if version is not already latest
  if [ "$VERSION" != "latest" ]; then
    docker tag "$REGISTRY/$APP_NAME:$VERSION" "$REGISTRY/$APP_NAME:latest"
  fi
  
  echo "✅ Docker image built"
fi

# Push Docker image to registry
if [ "$SKIP_PUSH" != "true" ]; then
  echo "\n📤 Pushing Docker image to registry..."
  docker push "$REGISTRY/$APP_NAME:$VERSION"
  
  # Also push latest tag if version is not already latest
  if [ "$VERSION" != "latest" ]; then
    docker push "$REGISTRY/$APP_NAME:latest"
  fi
  
  echo "✅ Docker image pushed to registry"
fi

# Deploy to specific platform
echo "\n🚀 Deploying to $DEPLOY_TARGET..."

case "$DEPLOY_TARGET" in
  render)
    echo "📝 For Render deployment:"
    echo "1. Go to your Render dashboard"
    echo "2. Select your service"
    echo "3. Click 'Manual Deploy' and select 'Clear build cache & deploy'"
    echo "4. Or set up Render to automatically deploy on push to your repository"
    ;;
    
  fly)
    echo "📝 Deploying to Fly.io..."
    fly deploy --image="$REGISTRY/$APP_NAME:$VERSION"
    echo "✅ Deployed to Fly.io"
    ;;
    
  docker)
    echo "📝 For deployment to a generic Docker host:"
    echo "Run the following command on your server:"
    echo "docker pull $REGISTRY/$APP_NAME:$VERSION"
    echo "docker stop $APP_NAME || true"
    echo "docker rm $APP_NAME || true"
    echo "docker run -d --name $APP_NAME \\"
    echo "  --restart unless-stopped \\"
    echo "  -p 8000:8000 \\"
    echo "  --env-file /path/to/your/.env \\"
    echo "  $REGISTRY/$APP_NAME:$VERSION"
    ;;
    
  *)
    echo "❌ Unknown deployment target: $DEPLOY_TARGET"
    exit 1
    ;;
esac

echo "\n✅ Deployment process completed!"