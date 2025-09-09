from fastapi import FastAPI
import uvicorn
import os
import platform
import time
import argparse

def create_app(service_name):
    """Create a FastAPI app with health check endpoints."""
    app = FastAPI(title=f"{service_name} API")
    
    @app.get("/healthz")
    def health_check():
        """Health check endpoint."""
        return {
            "status": "healthy",
            "timestamp": time.time(),
            "service": service_name,
            "environment": os.getenv("ENVIRONMENT", "development"),
            "system": platform.system()
        }
    
    @app.get("/ping")
    def ping():
        """Ping endpoint."""
        return {"ping": "pong"}
    
    @app.get("/")
    def root():
        """Root endpoint."""
        return {"message": f"Welcome to {service_name} API"}
    
    return app

def main():
    """Main function to run the server."""
    parser = argparse.ArgumentParser(description="Run a health check server")
    parser.add_argument("--service", type=str, default="Test Service", help="Service name")
    parser.add_argument("--port", type=int, default=8000, help="Port to run the server on")
    args = parser.parse_args()
    
    app = create_app(args.service)
    
    print(f"Starting {args.service} health check server on port {args.port}...")
    uvicorn.run(app, host="0.0.0.0", port=args.port)

if __name__ == "__main__":
    main()