from typing import Any, Dict, Generic, Optional, TypeVar, Union
from pydantic import BaseModel, Field

# Type variable for the data payload
T = TypeVar('T')


class ErrorDetail(BaseModel):
    """Error details model for the response envelope."""
    code: str = Field(..., description="Error code for programmatic handling")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")


class ResponseEnvelope(Generic[T], BaseModel):
    """Standard response envelope for all API responses.
    
    This provides a consistent structure for all API responses, including
    success/failure status, data payload, and error details when applicable.
    
    Attributes:
        success: Boolean indicating if the request was successful
        data: The response data payload (when success is True)
        error: Error details (when success is False)
    """
    success: bool = Field(..., description="Indicates if the request was successful")
    data: Optional[T] = Field(None, description="Response data payload")
    error: Optional[ErrorDetail] = Field(None, description="Error details when success is False")

    @classmethod
    def success_response(cls, data: Optional[T] = None) -> "ResponseEnvelope[T]":
        """Create a success response with optional data payload.
        
        Args:
            data: The data to include in the response
            
        Returns:
            A ResponseEnvelope instance with success=True
        """
        return cls(success=True, data=data, error=None)
    
    @classmethod
    def error_response(
        cls, 
        code: str, 
        message: str, 
        details: Optional[Dict[str, Any]] = None
    ) -> "ResponseEnvelope[T]":
        """Create an error response.
        
        Args:
            code: Error code for programmatic handling
            message: Human-readable error message
            details: Additional error details
            
        Returns:
            A ResponseEnvelope instance with success=False and error details
        """
        error = ErrorDetail(code=code, message=message, details=details)
        return cls(success=False, data=None, error=error)