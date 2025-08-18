"""Test FastAPI application entry point without database dependencies."""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.api.v1.api import api_router, oauth_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events - simplified for testing."""
    # Startup - skip database initialization for testing
    print("Starting FastAPI server in test mode...")
    
    yield
    
    # Shutdown
    print("Shutting down FastAPI server...")


# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(api_router, prefix=settings.API_V1_STR)
app.include_router(oauth_router, prefix="/oauth")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to Suit Research API",
        "version": settings.PROJECT_VERSION,
        "docs": "/docs",
        "openapi": f"{settings.API_V1_STR}/openapi.json"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "mode": "test"}


if __name__ == "__main__":
    uvicorn.run(
        "main_test:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True,
        log_level="info"
    )