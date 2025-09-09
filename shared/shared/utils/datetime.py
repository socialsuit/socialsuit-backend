"""Datetime utilities.

This module provides utilities for working with dates and times.
"""

from datetime import datetime, timezone, timedelta
from typing import Optional, Union


def get_utc_now() -> datetime:
    """Get the current UTC datetime.
    
    Returns:
        The current UTC datetime with timezone information
    """
    return datetime.now(timezone.utc)


def format_datetime(
    dt: datetime,
    format_str: str = "%Y-%m-%d %H:%M:%S",
    use_utc: bool = True
) -> str:
    """Format a datetime object as a string.
    
    Args:
        dt: The datetime to format
        format_str: The format string to use
        use_utc: Whether to convert to UTC before formatting
        
    Returns:
        The formatted datetime string
    """
    if use_utc and dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc)
    
    return dt.strftime(format_str)


def parse_datetime(
    dt_str: str,
    format_str: str = "%Y-%m-%d %H:%M:%S",
    default_timezone: Optional[timezone] = timezone.utc
) -> datetime:
    """Parse a string into a datetime object.
    
    Args:
        dt_str: The datetime string to parse
        format_str: The format string to use
        default_timezone: The timezone to use if not specified in the string
        
    Returns:
        The parsed datetime object
        
    Raises:
        ValueError: If the string cannot be parsed
    """
    dt = datetime.strptime(dt_str, format_str)
    
    # Add timezone if not present
    if dt.tzinfo is None and default_timezone is not None:
        dt = dt.replace(tzinfo=default_timezone)
    
    return dt


def add_time(
    dt: datetime,
    days: int = 0,
    hours: int = 0,
    minutes: int = 0,
    seconds: int = 0
) -> datetime:
    """Add time to a datetime object.
    
    Args:
        dt: The datetime to add to
        days: The number of days to add
        hours: The number of hours to add
        minutes: The number of minutes to add
        seconds: The number of seconds to add
        
    Returns:
        The new datetime
    """
    delta = timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)
    return dt + delta


def get_time_difference(
    dt1: datetime,
    dt2: datetime,
    unit: str = "seconds"
) -> Union[int, float]:
    """Get the difference between two datetime objects.
    
    Args:
        dt1: The first datetime
        dt2: The second datetime
        unit: The unit to return the difference in (seconds, minutes, hours, days)
        
    Returns:
        The difference in the specified unit
        
    Raises:
        ValueError: If the unit is not supported
    """
    # Ensure both datetimes have timezone info
    if dt1.tzinfo is None:
        dt1 = dt1.replace(tzinfo=timezone.utc)
    if dt2.tzinfo is None:
        dt2 = dt2.replace(tzinfo=timezone.utc)
    
    # Calculate difference in seconds
    diff_seconds = (dt2 - dt1).total_seconds()
    
    # Convert to requested unit
    if unit == "seconds":
        return diff_seconds
    elif unit == "minutes":
        return diff_seconds / 60
    elif unit == "hours":
        return diff_seconds / 3600
    elif unit == "days":
        return diff_seconds / 86400
    else:
        raise ValueError(f"Unsupported unit: {unit}")