"""Tests for datetime utilities."""

import pytest
from datetime import datetime, timezone, timedelta

from shared.utils.datetime import (
    get_utc_now,
    format_datetime,
    parse_datetime,
    add_time,
    get_time_difference
)


def test_get_utc_now():
    """Test getting the current UTC time."""
    now = get_utc_now()
    
    # Check that it's a datetime
    assert isinstance(now, datetime)
    
    # Check that it has timezone info
    assert now.tzinfo is not None
    
    # Check that it's UTC
    assert now.tzinfo == timezone.utc


def test_format_datetime():
    """Test formatting a datetime as a string."""
    # Create a datetime with timezone
    dt = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    
    # Test default format
    formatted = format_datetime(dt)
    assert formatted == "2023-01-01 12:00:00"
    
    # Test custom format
    formatted = format_datetime(dt, format_str="%Y-%m-%d")
    assert formatted == "2023-01-01"
    
    # Test with a non-UTC timezone
    est = timezone(timedelta(hours=-5))
    dt_est = datetime(2023, 1, 1, 7, 0, 0, tzinfo=est)
    
    # Should convert to UTC (12:00) before formatting
    formatted = format_datetime(dt_est)
    assert formatted == "2023-01-01 12:00:00"
    
    # Should not convert to UTC if use_utc=False
    formatted = format_datetime(dt_est, use_utc=False)
    assert formatted == "2023-01-01 07:00:00"


def test_parse_datetime():
    """Test parsing a string into a datetime."""
    # Test default format
    dt_str = "2023-01-01 12:00:00"
    dt = parse_datetime(dt_str)
    
    assert isinstance(dt, datetime)
    assert dt.year == 2023
    assert dt.month == 1
    assert dt.day == 1
    assert dt.hour == 12
    assert dt.minute == 0
    assert dt.second == 0
    assert dt.tzinfo == timezone.utc
    
    # Test custom format
    dt_str = "2023/01/01"
    dt = parse_datetime(dt_str, format_str="%Y/%m/%d")
    
    assert dt.year == 2023
    assert dt.month == 1
    assert dt.day == 1
    assert dt.hour == 0
    assert dt.minute == 0
    assert dt.second == 0
    
    # Test with custom timezone
    est = timezone(timedelta(hours=-5))
    dt = parse_datetime(dt_str, format_str="%Y/%m/%d", default_timezone=est)
    
    assert dt.tzinfo == est


def test_add_time():
    """Test adding time to a datetime."""
    dt = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    
    # Test adding days
    result = add_time(dt, days=1)
    assert result.day == 2
    assert result.hour == 12
    
    # Test adding hours
    result = add_time(dt, hours=2)
    assert result.day == 1
    assert result.hour == 14
    
    # Test adding minutes
    result = add_time(dt, minutes=30)
    assert result.hour == 12
    assert result.minute == 30
    
    # Test adding seconds
    result = add_time(dt, seconds=45)
    assert result.minute == 0
    assert result.second == 45
    
    # Test adding multiple units
    result = add_time(dt, days=1, hours=2, minutes=30, seconds=45)
    assert result.day == 2
    assert result.hour == 14
    assert result.minute == 30
    assert result.second == 45


def test_get_time_difference():
    """Test getting the difference between two datetimes."""
    dt1 = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    dt2 = datetime(2023, 1, 1, 13, 30, 45, tzinfo=timezone.utc)
    
    # Test difference in seconds
    diff = get_time_difference(dt1, dt2)
    assert diff == 5445  # 1h 30m 45s = 5445s
    
    # Test difference in minutes
    diff = get_time_difference(dt1, dt2, unit="minutes")
    assert diff == 5445 / 60  # 90.75 minutes
    
    # Test difference in hours
    diff = get_time_difference(dt1, dt2, unit="hours")
    assert diff == 5445 / 3600  # 1.5125 hours
    
    # Test difference in days
    diff = get_time_difference(dt1, dt2, unit="days")
    assert diff == 5445 / 86400  # 0.063 days
    
    # Test with timezone conversion
    est = timezone(timedelta(hours=-5))
    dt3 = datetime(2023, 1, 1, 7, 0, 0, tzinfo=est)  # Same as dt1 in UTC
    
    diff = get_time_difference(dt3, dt2)
    assert diff == 5445  # Should handle timezone conversion
    
    # Test with invalid unit
    with pytest.raises(ValueError):
        get_time_difference(dt1, dt2, unit="invalid")