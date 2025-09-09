"""
Shared input sanitization utilities for Social Suit and Sparkr projects.
Provides centralized functions to sanitize user inputs and prevent common security issues.
"""

import re
import html
from typing import Any, Dict, List, Union

# HTML/Script tag pattern for detecting potentially malicious content
HTML_TAG_PATTERN = re.compile(r'<[^>]*>')
SCRIPT_PATTERN = re.compile(r'<script[^>]*>[\s\S]*?<\/script>', re.IGNORECASE)
ON_EVENT_PATTERN = re.compile(r'\s+on\w+\s*=\s*["\'][^"\'>]*["\']', re.IGNORECASE)
DANGEROUS_ATTRS = re.compile(r'\s+(href|src|style)\s*=\s*["\'][^"\'>]*["\']', re.IGNORECASE)


def sanitize_string(value: str) -> str:
    """
    Sanitize a string input by escaping HTML entities and removing potentially malicious content.
    
    Args:
        value: The string to sanitize
        
    Returns:
        Sanitized string with HTML entities escaped
    """
    if not isinstance(value, str):
        return value
    
    # Escape HTML entities
    escaped = html.escape(value)
    
    # Remove any remaining script tags (belt and suspenders approach)
    escaped = SCRIPT_PATTERN.sub('', escaped)
    
    # Remove on* event handlers
    escaped = ON_EVENT_PATTERN.sub('', escaped)
    
    return escaped.strip()


def sanitize_html(html_content: str, allowed_tags: List[str] = None) -> str:
    """
    More advanced HTML sanitization that can allow specific safe tags.
    
    Args:
        html_content: The HTML content to sanitize
        allowed_tags: List of allowed HTML tags (e.g., ['p', 'br', 'strong'])
        
    Returns:
        Sanitized HTML with only allowed tags
    """
    if not allowed_tags:
        # If no allowed tags specified, remove all HTML
        return HTML_TAG_PATTERN.sub('', html_content)
    
    # TODO: Implement more sophisticated HTML sanitization with allowed tags
    # This is a placeholder for a more robust implementation
    # Consider using a library like bleach for production use
    
    # For now, just escape everything
    return html.escape(html_content)


def sanitize_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively sanitize all string values in a dictionary.
    
    Args:
        data: Dictionary with values to sanitize
        
    Returns:
        Dictionary with sanitized values
    """
    result = {}
    
    for key, value in data.items():
        if isinstance(value, str):
            result[key] = sanitize_string(value)
        elif isinstance(value, dict):
            result[key] = sanitize_dict(value)
        elif isinstance(value, list):
            result[key] = sanitize_list(value)
        else:
            result[key] = value
            
    return result


def sanitize_list(data: List[Any]) -> List[Any]:
    """
    Recursively sanitize all string values in a list.
    
    Args:
        data: List with values to sanitize
        
    Returns:
        List with sanitized values
    """
    result = []
    
    for item in data:
        if isinstance(item, str):
            result.append(sanitize_string(item))
        elif isinstance(item, dict):
            result.append(sanitize_dict(item))
        elif isinstance(item, list):
            result.append(sanitize_list(item))
        else:
            result.append(item)
            
    return result


def sanitize_input(data: Union[str, Dict[str, Any], List[Any]]) -> Union[str, Dict[str, Any], List[Any]]:
    """
    Main entry point for sanitizing any type of input.
    
    Args:
        data: Input data to sanitize (string, dict, or list)
        
    Returns:
        Sanitized data of the same type
    """
    if isinstance(data, str):
        return sanitize_string(data)
    elif isinstance(data, dict):
        return sanitize_dict(data)
    elif isinstance(data, list):
        return sanitize_list(data)
    else:
        return data