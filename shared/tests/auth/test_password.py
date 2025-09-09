"""Tests for password handling utilities."""

import pytest

from shared.auth.password import hash_password, verify_password, password_meets_requirements


def test_hash_password():
    """Test hashing a password."""
    password = "test_password"
    hashed = hash_password(password)
    
    # Check that the hash is not the same as the original password
    assert hashed != password
    # Check that the hash is a string
    assert isinstance(hashed, str)
    # Check that the hash is not empty
    assert hashed


def test_verify_password():
    """Test verifying a password against a hash."""
    password = "test_password"
    hashed = hash_password(password)
    
    # Check that the correct password verifies
    assert verify_password(password, hashed)
    
    # Check that an incorrect password does not verify
    assert not verify_password("wrong_password", hashed)


def test_password_meets_requirements():
    """Test password requirements checking."""
    # Test a password that meets all requirements
    good_password = "Password123!"
    meets, error = password_meets_requirements(good_password)
    assert meets
    assert error is None
    
    # Test a password that is too short
    short_password = "Pass1!"
    meets, error = password_meets_requirements(short_password)
    assert not meets
    assert "length" in error.lower()
    
    # Test a password without uppercase
    no_upper_password = "password123!"
    meets, error = password_meets_requirements(no_upper_password)
    assert not meets
    assert "uppercase" in error.lower()
    
    # Test a password without lowercase
    no_lower_password = "PASSWORD123!"
    meets, error = password_meets_requirements(no_lower_password)
    assert not meets
    assert "lowercase" in error.lower()
    
    # Test a password without digits
    no_digit_password = "Password!"
    meets, error = password_meets_requirements(no_digit_password)
    assert not meets
    assert "digit" in error.lower()
    
    # Test a password without special characters
    no_special_password = "Password123"
    meets, error = password_meets_requirements(no_special_password)
    assert not meets
    assert "special" in error.lower()


def test_password_meets_requirements_custom():
    """Test password requirements with custom settings."""
    # Test with custom minimum length
    password = "Pass1!"
    meets, error = password_meets_requirements(password, min_length=6)
    assert meets
    assert error is None
    
    # Test with uppercase requirement disabled
    password = "password123!"
    meets, error = password_meets_requirements(password, require_uppercase=False)
    assert meets
    assert error is None
    
    # Test with lowercase requirement disabled
    password = "PASSWORD123!"
    meets, error = password_meets_requirements(password, require_lowercase=False)
    assert meets
    assert error is None
    
    # Test with digit requirement disabled
    password = "Password!"
    meets, error = password_meets_requirements(password, require_digit=False)
    assert meets
    assert error is None
    
    # Test with special character requirement disabled
    password = "Password123"
    meets, error = password_meets_requirements(password, require_special=False)
    assert meets
    assert error is None