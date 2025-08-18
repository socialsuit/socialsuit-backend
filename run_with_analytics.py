# run_with_analytics.py
import asyncio
import sys
import uvicorn
from services.utils.logger_config import setup_logger
from services.analytics.init_analytics_db import init_analytics_db

# Set up logger
logger = setup_logger("run_with_analytics")

async def initialize_analytics():
    """Initialize the analytics database before starting the application"""
    logger.info("Initializing analytics database...")
    await init_analytics_db()
    logger.info("Analytics database initialization completed")

def run_app():
    """Run the FastAPI application with uvicorn"""
    logger.info("Starting the application with analytics system...")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

if __name__ == "__main__":
    # Check if we should initialize the analytics database
    if len(sys.argv) > 1 and sys.argv[1] == "--init-analytics":
        # Initialize analytics database
        asyncio.run(initialize_analytics())
    
    # Run the application
    run_app()