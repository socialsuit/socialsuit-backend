from flask import Flask, jsonify
import os
import platform
import time
import argparse

def create_app(service_name):
    """Create a Flask app with health check endpoints."""
    app = Flask(service_name)
    
    @app.route("/healthz")
    def health_check():
        """Health check endpoint."""
        return jsonify({
            "status": "healthy",
            "timestamp": time.time(),
            "service": service_name,
            "environment": os.getenv("ENVIRONMENT", "development"),
            "system": platform.system()
        })
    
    @app.route("/ping")
    def ping():
        """Ping endpoint."""
        return jsonify({"ping": "pong"})
    
    @app.route("/")
    def root():
        """Root endpoint."""
        return jsonify({"message": f"Welcome to {service_name} API"})
    
    return app

def main():
    """Main function to run the server."""
    parser = argparse.ArgumentParser(description="Run a health check server")
    parser.add_argument("--service", type=str, default="Test Service", help="Service name")
    parser.add_argument("--port", type=int, default=8000, help="Port to run the server on")
    args = parser.parse_args()
    
    app = create_app(args.service)
    
    print(f"Starting {args.service} health check server on port {args.port}...")
    app.run(host="0.0.0.0", port=args.port)

if __name__ == "__main__":
    main()