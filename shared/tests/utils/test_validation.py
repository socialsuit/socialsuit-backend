"""Tests for validation utilities."""

import pytest

from shared.utils.validation import (
    validate_email,
    validate_phone_number,
    validate_url,
    validate_length,
    validate_numeric
)


def test_validate_email():
    """Test email validation."""
    # Test valid emails
    valid_emails = [
        "user@example.com",
        "user.name@example.com",
        "user+tag@example.com",
        "user@subdomain.example.com",
    ]
    
    for email in valid_emails:
        is_valid, error = validate_email(email)
        assert is_valid
        assert error is None
    
    # Test invalid emails
    invalid_emails = [
        "",  # Empty
        "user",  # No domain
        "user@",  # No domain
        "@example.com",  # No username
        "user@example",  # Incomplete domain
        "user@.com",  # Missing domain part
        "user@example..com",  # Double dot
    ]
    
    for email in invalid_emails:
        is_valid, error = validate_email(email)
        assert not is_valid
        assert error is not None


def test_validate_phone_number():
    """Test phone number validation."""
    # Test valid phone numbers
    valid_phones = [
        "1234567890",  # Simple 10-digit
        "123-456-7890",  # With dashes
        "(123) 456-7890",  # With parentheses
        "123.456.7890",  # With dots
        "123 456 7890",  # With spaces
        "+11234567890",  # With country code
    ]
    
    for phone in valid_phones:
        is_valid, error = validate_phone_number(phone)
        assert is_valid
        assert error is None
    
    # Test invalid phone numbers
    invalid_phones = [
        "",  # Empty
        "123",  # Too short
        "123456789012345678",  # Too long
        "123-456-789a",  # Contains letters
        "123-456-789#",  # Contains special characters
    ]
    
    for phone in invalid_phones:
        is_valid, error = validate_phone_number(phone)
        assert not is_valid
        assert error is not None


def test_validate_url():
    """Test URL validation."""
    # Test valid URLs
    valid_urls = [
        "http://example.com",
        "https://example.com",
        "http://www.example.com",
        "https://example.com/path",
        "https://example.com/path?query=value",
        "example.com",
    ]
    
    for url in valid_urls:
        is_valid, error = validate_url(url)
        assert is_valid
        assert error is None
    
    # Test invalid URLs
    invalid_urls = [
        "",  # Empty
        "http://",  # No domain
        "http://.com",  # No domain
        "http://example",  # Incomplete domain
        "example",  # Incomplete domain
    ]
    
    for url in invalid_urls:
        is_valid, error = validate_url(url)
        assert not is_valid
        assert error is not None


def test_validate_length():
    """Test string length validation."""
    # Test valid lengths
    value = "test"
    
    # No constraints
    is_valid, error = validate_length(value)
    assert is_valid
    assert error is None
    
    # Within min length
    is_valid, error = validate_length(value, min_length=4)
    assert is_valid
    assert error is None
    
    # Within max length
    is_valid, error = validate_length(value, max_length=4)
    assert is_valid
    assert error is None
    
    # Within min and max length
    is_valid, error = validate_length(value, min_length=2, max_length=6)
    assert is_valid
    assert error is None
    
    # Test invalid lengths
    # Below min length
    is_valid, error = validate_length(value, min_length=5)
    assert not is_valid
    assert "at least" in error
    
    # Above max length
    is_valid, error = validate_length(value, max_length=3)
    assert not is_valid
    assert "at most" in error
    
    # None value
    is_valid, error = validate_length(None)
    assert not is_valid
    assert error is not None


def test_validate_numeric():
    """Test numeric validation."""
    # Test valid numbers
    # Integer as int
    is_valid, error = validate_numeric(42)
    assert is_valid
    assert error is None
    
    # Float as float
    is_valid, error = validate_numeric(42.5)
    assert is_valid
    assert error is None
    
    # Integer as string
    is_valid, error = validate_numeric("42")
    assert is_valid
    assert error is None
    
    # Float as string
    is_valid, error = validate_numeric("42.5")
    assert is_valid
    assert error is None
    
    # Within range
    is_valid, error = validate_numeric(42, min_value=0, max_value=100)
    assert is_valid
    assert error is None
    
    # Test invalid numbers
    # Non-numeric string
    is_valid, error = validate_numeric("not a number")
    assert not is_valid
    assert error is not None
    
    # Float when only integers allowed
    is_valid, error = validate_numeric(42.5, allow_float=False)
    assert not is_valid
    assert error is not None
    
    # Below min value
    is_valid, error = validate_numeric(42, min_value=50)
    assert not is_valid
    assert "at least" in error
    
    # Above max value
    is_valid, error = validate_numeric(42, max_value=40)
    assert not is_valid
    assert "at most" in error