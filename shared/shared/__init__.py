"""Shared utilities for Social Suit and Sparkr projects.

This package provides common functionality that can be used across different projects,
including authentication, database utilities, logging, middleware, and general utilities.
"""

__version__ = "0.1.0"

# Import subpackages to make them available when importing the main package
from shared import auth
from shared import database
from shared import logging
from shared import middleware
from shared import utils