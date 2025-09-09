import os
import logging
from typing import Dict, Any, List, Optional, Tuple
from fastapi import UploadFile, HTTPException, status
from utils.file_sanitization import (
    sanitize_file_upload,
    get_safe_upload_path,
    SAFE_EXTENSIONS,
    SAFE_MIME_TYPES
)

logger = logging.getLogger(__name__)

# Default upload directory
DEFAULT_UPLOAD_DIR = os.path.join(os.getcwd(), "uploads")

class SecureFileHandler:
    """
    Secure file upload handler with sanitization and validation.
    """
    
    def __init__(self, upload_dir: Optional[str] = None):
        """
        Initialize the secure file handler.
        
        Args:
            upload_dir: Base directory for file uploads (optional)
        """
        self.upload_dir = upload_dir or DEFAULT_UPLOAD_DIR
        os.makedirs(self.upload_dir, exist_ok=True)
    
    async def process_upload(self, 
                       file: UploadFile, 
                       user_id: Optional[str] = None,
                       allowed_extensions: Optional[List[str]] = None,
                       max_size: Optional[int] = None) -> Dict[str, Any]:
        """
        Process and validate an uploaded file.
        
        Args:
            file: The uploaded file
            user_id: User ID for user-specific storage (optional)
            allowed_extensions: List of allowed file extensions (optional)
            max_size: Maximum file size in bytes (optional)
            
        Returns:
            Dictionary with file information
            - filename: Original filename
            - sanitized_filename: Sanitized filename
            - content_type: File content type
            - size: File size in bytes
            - file_path: Path where the file is stored
            - file_hash: SHA-256 hash of the file
            
        Raises:
            HTTPException: If the file is invalid or unsafe
        """
        try:
            # Read the file content
            contents = await file.read()
            size = len(contents)
            
            # Create a temporary file path
            temp_file_path = os.path.join(self.upload_dir, "temp_" + os.path.basename(file.filename))
            
            # Write the file to disk temporarily
            with open(temp_file_path, "wb") as f:
                f.write(contents)
            
            # Prepare file data for validation
            file_data = {
                "filename": file.filename,
                "content_type": file.content_type,
                "file_path": temp_file_path,
                "size": size
            }
            
            # Sanitize and validate the file
            validation_result = sanitize_file_upload(file_data)
            
            if not validation_result["is_valid"]:
                # Clean up the temporary file
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
                    
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid file: {validation_result['error']}"
                )
            
            # Get a safe path for the file
            sanitized_filename = validation_result["sanitized_filename"]
            safe_path = get_safe_upload_path(self.upload_dir, sanitized_filename, user_id)
            
            # Move the file to its final location
            os.rename(temp_file_path, safe_path)
            
            # Return file information
            return {
                "filename": file.filename,
                "sanitized_filename": sanitized_filename,
                "content_type": file.content_type,
                "size": size,
                "file_path": safe_path,
                "file_hash": validation_result["file_hash"]
            }
            
        except HTTPException:
            # Re-raise HTTP exceptions
            raise
        except Exception as e:
            logger.error(f"Error processing file upload: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error processing file upload"
            )
    
    async def process_multiple_uploads(self,
                                  files: List[UploadFile],
                                  user_id: Optional[str] = None,
                                  allowed_extensions: Optional[List[str]] = None,
                                  max_size: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Process and validate multiple uploaded files.
        
        Args:
            files: List of uploaded files
            user_id: User ID for user-specific storage (optional)
            allowed_extensions: List of allowed file extensions (optional)
            max_size: Maximum file size in bytes (optional)
            
        Returns:
            List of dictionaries with file information
            
        Raises:
            HTTPException: If any file is invalid or unsafe
        """
        results = []
        
        for file in files:
            result = await self.process_upload(file, user_id, allowed_extensions, max_size)
            results.append(result)
            
        return results
    
    def delete_file(self, file_path: str) -> bool:
        """
        Safely delete a file.
        
        Args:
            file_path: Path to the file to delete
            
        Returns:
            True if the file was deleted, False otherwise
        """
        try:
            # Verify the file is within our upload directory
            if not os.path.abspath(file_path).startswith(os.path.abspath(self.upload_dir)):
                logger.warning(f"Attempted to delete file outside upload directory: {file_path}")
                return False
                
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting file: {str(e)}")
            return False