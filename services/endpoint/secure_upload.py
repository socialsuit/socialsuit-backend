from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from typing import List, Optional
from services.upload.dependencies import get_file_handler
from services.upload.secure_file_handler import SecureFileHandler
from services.auth.dependencies import get_current_user
from services.models.user import User
from utils.sanitization import sanitize_string

router = APIRouter(prefix="/uploads", tags=["uploads"])

@router.post("/", summary="Upload a file securely")
async def upload_file(
    file: UploadFile = File(...),
    description: Optional[str] = Form(None),
    file_handler: SecureFileHandler = Depends(get_file_handler),
    current_user: User = Depends(get_current_user)
):
    """
    Upload a file with sanitization and validation.
    
    Args:
        file: The file to upload
        description: Optional description of the file
        file_handler: Secure file handler dependency
        current_user: Current authenticated user
        
    Returns:
        Information about the uploaded file
    """
    # Sanitize the description if provided
    sanitized_description = sanitize_string(description) if description else None
    
    # Process the file upload
    result = await file_handler.process_upload(
        file=file,
        user_id=str(current_user.id)
    )
    
    # Add the sanitized description to the result
    result["description"] = sanitized_description
    
    return {
        "message": "File uploaded successfully",
        "file_info": result
    }

@router.post("/multiple", summary="Upload multiple files securely")
async def upload_multiple_files(
    files: List[UploadFile] = File(...),
    file_handler: SecureFileHandler = Depends(get_file_handler),
    current_user: User = Depends(get_current_user)
):
    """
    Upload multiple files with sanitization and validation.
    
    Args:
        files: List of files to upload
        file_handler: Secure file handler dependency
        current_user: Current authenticated user
        
    Returns:
        Information about the uploaded files
    """
    # Process multiple file uploads
    results = await file_handler.process_multiple_uploads(
        files=files,
        user_id=str(current_user.id)
    )
    
    return {
        "message": f"{len(results)} files uploaded successfully",
        "files_info": results
    }

@router.delete("/{file_path:path}", summary="Delete an uploaded file")
async def delete_file(
    file_path: str,
    file_handler: SecureFileHandler = Depends(get_file_handler),
    current_user: User = Depends(get_current_user)
):
    """
    Delete an uploaded file.
    
    Args:
        file_path: Path to the file to delete
        file_handler: Secure file handler dependency
        current_user: Current authenticated user
        
    Returns:
        Success message
    """
    # Sanitize the file path
    sanitized_file_path = sanitize_string(file_path)
    
    # Delete the file
    success = file_handler.delete_file(sanitized_file_path)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found or could not be deleted"
        )
    
    return {
        "message": "File deleted successfully"
    }