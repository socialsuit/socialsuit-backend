from typing import Optional
from fastapi import Depends
from services.upload.secure_file_handler import SecureFileHandler
from services.config import settings
import os

# Configure the default upload directory
DEFAULT_UPLOAD_DIR = os.path.join(os.getcwd(), "uploads")

# Create a singleton instance of the secure file handler
_file_handler = None

def get_file_handler(upload_dir: Optional[str] = None) -> SecureFileHandler:
    """
    Get or create a singleton instance of the secure file handler.
    
    Args:
        upload_dir: Optional custom upload directory
        
    Returns:
        SecureFileHandler instance
    """
    global _file_handler
    
    if _file_handler is None:
        # Use the provided upload directory, or the one from settings, or the default
        upload_directory = upload_dir or getattr(settings, "UPLOAD_DIR", DEFAULT_UPLOAD_DIR)
        _file_handler = SecureFileHandler(upload_directory)
        
    return _file_handler