#!/usr/bin/env python3
"""
Development startup script for Suit Research.
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"\n🔄 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"Error: {e.stderr}")
        return False

def check_dependencies():
    """Check if required dependencies are installed."""
    print("🔍 Checking dependencies...")
    
    try:
        import fastapi
        import uvicorn
        import sqlalchemy
        import pydantic
        import pydantic_settings
        print("✅ Core dependencies are available")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please install dependencies: pip install -r requirements.txt")
        return False

def check_env_file():
    """Check if .env file exists."""
    env_file = Path(".env")
    if not env_file.exists():
        print("⚠️  .env file not found. Creating from template...")
        template_file = Path(".env.template")
        if template_file.exists():
            import shutil
            shutil.copy(template_file, env_file)
            print("✅ .env file created from template")
            print("📝 Please review and update the .env file with your settings")
        else:
            print("❌ .env.template not found")
            return False
    else:
        print("✅ .env file exists")
    return True

def main():
    """Main startup function."""
    print("=" * 60)
    print("🚀 SUIT RESEARCH - DEVELOPMENT STARTUP")
    print("=" * 60)
    
    # Check if we're in the right directory
    if not Path("main.py").exists():
        print("❌ main.py not found. Please run this script from the project root.")
        sys.exit(1)
    
    # Check dependencies
    if not check_dependencies():
        print("\n💡 To install dependencies, run:")
        print("   pip install -r requirements.txt")
        sys.exit(1)
    
    # Check environment file
    if not check_env_file():
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("🎯 STARTING DEVELOPMENT SERVER")
    print("=" * 60)
    
    print("\n📋 Application will be available at:")
    print("   • Main API: http://localhost:8000")
    print("   • API Docs: http://localhost:8000/api/v1/docs")
    print("   • Health Check: http://localhost:8000/api/v1/status/health")
    
    print("\n⚠️  Note: This starts only the FastAPI application.")
    print("   For full functionality, you'll need to start:")
    print("   • PostgreSQL database")
    print("   • MongoDB database") 
    print("   • Redis server")
    print("   • Celery worker (optional)")
    
    print("\n🔄 Starting FastAPI development server...")
    print("   Press Ctrl+C to stop the server")
    print("-" * 60)
    
    try:
        # Start the FastAPI development server
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "main:app", 
            "--reload", 
            "--host", "0.0.0.0", 
            "--port", "8000"
        ], check=True)
    except KeyboardInterrupt:
        print("\n\n🛑 Server stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Server failed to start: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()