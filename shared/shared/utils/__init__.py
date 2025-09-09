"""General utilities for shared projects.

This module provides common utility functions including datetime handling,
validation helpers, and other general-purpose utilities.
"""

# Import key components to make them available when importing the utils module
from shared.utils.datetime import format_datetime, parse_datetime, get_utc_now
from shared.utils.validation import validate_email, validate_phone_number