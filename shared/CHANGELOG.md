# Changelog

All notable changes to the shared utilities package will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-09-04

### Added

- Initial release of shared utilities package
- Authentication module with JWT and password utilities
- Database connection and pagination utilities
- Logging configuration with JSON formatting
- Middleware components for rate limiting and request logging
- Utility functions for datetime handling and validation
- Shim modules in both Social Suit and Sparkr projects for backward compatibility

### Changed

- Extracted common code from both Social Suit and Sparkr projects
- Standardized interfaces for security, session, and logging components

### Deprecated

- Original implementations in both projects are now deprecated in favor of the shared package
- Deprecation warnings added to shim modules to encourage direct imports from shared package