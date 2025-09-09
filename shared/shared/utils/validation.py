"""Validation utilities.

This module provides utilities for validating common data types.
"""

import re
from typing import Optional, Tuple, Union


def validate_email(email: str) -> Tuple[bool, Optional[str]]:
    """Validate an email address.
    
    Args:
        email: The email address to validate
        
    Returns:
        A tuple containing (is_valid, error_message)
        If the email is valid, error_message will be None
    """
    if not email:
        return False, "Email cannot be empty"
    
    # Simple regex for email validation
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(pattern, email):
        return False, "Invalid email format"
    
    return True, None


def validate_phone_number(phone: str, country_code: str = None) -> Tuple[bool, Optional[str]]:
    """Validate a phone number.
    
    Args:
        phone: The phone number to validate
        country_code: Optional country code for specific validation
        
    Returns:
        A tuple containing (is_valid, error_message)
        If the phone number is valid, error_message will be None
    """
    if not phone:
        return False, "Phone number cannot be empty"
    
    # Remove common separators
    cleaned = re.sub(r'[\s\-\(\)\.]', '', phone)
    
    # Check if it's all digits after cleaning
    if not cleaned.isdigit():
        return False, "Phone number should contain only digits, spaces, and common separators"
    
    # Length check (this is a simple check, could be more sophisticated with country codes)
    if len(cleaned) < 10 or len(cleaned) > 15:
        return False, "Phone number should be between 10 and 15 digits"
    
    return True, None


def validate_url(url: str) -> Tuple[bool, Optional[str]]:
    """Validate a URL.
    
    Args:
        url: The URL to validate
        
    Returns:
        A tuple containing (is_valid, error_message)
        If the URL is valid, error_message will be None
    """
    if not url:
        return False, "URL cannot be empty"
    
    # Simple regex for URL validation
    pattern = r'^(https?:\/\/)?([\da-z\.-]+)\.([a-z\.]{2,6})([\/\w \.-]*)*\/?$'
    
    if not re.match(pattern, url):
        return False, "Invalid URL format"
    
    return True, None


def validate_length(
    value: str,
    min_length: int = None,
    max_length: int = None,
) -> Tuple[bool, Optional[str]]:
    """Validate the length of a string.
    
    Args:
        value: The string to validate
        min_length: The minimum allowed length
        max_length: The maximum allowed length
        
    Returns:
        A tuple containing (is_valid, error_message)
        If the string length is valid, error_message will be None
    """
    if value is None:
        return False, "Value cannot be None"
    
    length = len(value)
    
    if min_length is not None and length < min_length:
        return False, f"Value must be at least {min_length} characters long"
    
    if max_length is not None and length > max_length:
        return False, f"Value must be at most {max_length} characters long"
    
    return True, None


def validate_numeric(
    value: Union[str, int, float],
    min_value: Union[int, float] = None,
    max_value: Union[int, float] = None,
    allow_float: bool = True,
) -> Tuple[bool, Optional[str]]:
    """Validate a numeric value.
    
    Args:
        value: The value to validate
        min_value: The minimum allowed value
        max_value: The maximum allowed value
        allow_float: Whether to allow floating point values
        
    Returns:
        A tuple containing (is_valid, error_message)
        If the value is valid, error_message will be None
    """
    # Convert string to number if needed
    if isinstance(value, str):
        try:
            if allow_float:
                value = float(value)
            else:
                value = int(value)
        except ValueError:
            return False, "Value must be a valid number"
    
    # Check if it's the right type
    if not allow_float and isinstance(value, float) and not value.is_integer():
        return False, "Value must be an integer"
    
    # Range checks
    if min_value is not None and value < min_value:
        return False, f"Value must be at least {min_value}"
    
    if max_value is not None and value > max_value:
        return False, f"Value must be at most {max_value}"
    
    return True, None