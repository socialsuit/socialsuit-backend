"""
Security Configuration for Social Suit Application

This module provides centralized security configuration including:
- Rate limiting settings
- Validation rules
- Security headers
- CORS configuration
- Authentication settings
"""

from typing import Dict, List, Optional, Set
from pydantic import BaseSettings, Field
import os
from datetime import timedelta

class SecuritySettings(BaseSettings):
    """Security settings configuration."""
    
    # JWT Settings
    jwt_secret_key: str = Field(..., env="JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    jwt_access_token_expire_minutes: int = Field(default=30, env="JWT_ACCESS_TOKEN_EXPIRE_MINUTES")
    jwt_refresh_token_expire_days: int = Field(default=7, env="JWT_REFRESH_TOKEN_EXPIRE_DAYS")
    
    # Rate Limiting Settings
    rate_limit_enabled: bool = Field(default=True, env="RATE_LIMIT_ENABLED")
    rate_limit_redis_url: str = Field(..., env="REDIS_URL")
    rate_limit_default_requests_per_minute: int = Field(default=60, env="RATE_LIMIT_DEFAULT_RPM")
    rate_limit_default_burst_size: int = Field(default=10, env="RATE_LIMIT_DEFAULT_BURST")
    
    # CORS Settings
    cors_allow_origins: List[str] = Field(default=["http://localhost:3000"], env="CORS_ALLOW_ORIGINS")
    cors_allow_credentials: bool = Field(default=True, env="CORS_ALLOW_CREDENTIALS")
    cors_allow_methods: List[str] = Field(default=["GET", "POST", "PUT", "DELETE", "OPTIONS"], env="CORS_ALLOW_METHODS")
    cors_allow_headers: List[str] = Field(default=["*"], env="CORS_ALLOW_HEADERS")
    
    # Security Headers
    security_headers_enabled: bool = Field(default=True, env="SECURITY_HEADERS_ENABLED")
    hsts_max_age: int = Field(default=31536000, env="HSTS_MAX_AGE")  # 1 year
    
    # Content Security Policy
    csp_enabled: bool = Field(default=True, env="CSP_ENABLED")
    csp_default_src: List[str] = Field(default=["'self'"], env="CSP_DEFAULT_SRC")
    csp_script_src: List[str] = Field(default=["'self'", "'unsafe-inline'"], env="CSP_SCRIPT_SRC")
    csp_style_src: List[str] = Field(default=["'self'", "'unsafe-inline'"], env="CSP_STYLE_SRC")
    csp_img_src: List[str] = Field(default=["'self'", "data:", "https:"], env="CSP_IMG_SRC")
    
    # Input Validation Settings
    max_content_length: int = Field(default=10000, env="MAX_CONTENT_LENGTH")
    max_file_size_mb: int = Field(default=10, env="MAX_FILE_SIZE_MB")
    allowed_file_extensions: Set[str] = Field(
        default={".jpg", ".jpeg", ".png", ".gif", ".pdf", ".txt", ".docx"},
        env="ALLOWED_FILE_EXTENSIONS"
    )
    blocked_file_extensions: Set[str] = Field(
        default={".exe", ".bat", ".cmd", ".scr", ".vbs", ".js", ".jar"},
        env="BLOCKED_FILE_EXTENSIONS"
    )
    
    # IP Whitelist/Blacklist
    ip_whitelist: List[str] = Field(default=[], env="IP_WHITELIST")
    ip_blacklist: List[str] = Field(default=[], env="IP_BLACKLIST")
    
    # Admin Settings
    admin_emails: List[str] = Field(default=[], env="ADMIN_EMAILS")
    admin_ips: List[str] = Field(default=[], env="ADMIN_IPS")
    
    # Audit Settings
    audit_enabled: bool = Field(default=True, env="AUDIT_ENABLED")
    audit_log_file: str = Field(default="security_audit.log", env="AUDIT_LOG_FILE")
    audit_retention_days: int = Field(default=90, env="AUDIT_RETENTION_DAYS")
    
    # Database Security
    db_connection_timeout: int = Field(default=30, env="DB_CONNECTION_TIMEOUT")
    db_query_timeout: int = Field(default=60, env="DB_QUERY_TIMEOUT")
    db_max_connections: int = Field(default=20, env="DB_MAX_CONNECTIONS")
    
    # Session Security
    session_timeout_minutes: int = Field(default=60, env="SESSION_TIMEOUT_MINUTES")
    session_secure_cookies: bool = Field(default=True, env="SESSION_SECURE_COOKIES")
    session_httponly_cookies: bool = Field(default=True, env="SESSION_HTTPONLY_COOKIES")
    session_samesite: str = Field(default="lax", env="SESSION_SAMESITE")
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Global security settings instance
security_settings = SecuritySettings()

# Rate limiting configuration
RATE_LIMIT_CONFIG = {
    "default_requests_per_minute": security_settings.rate_limit_default_requests_per_minute,
    "default_burst_size": security_settings.rate_limit_default_burst_size,
    "endpoint_limits": {
        # Authentication endpoints - stricter limits
        "/auth/login": 5,
        "/auth/register": 3,
        "/auth/forgot-password": 3,
        "/auth/reset-password": 3,
        
        # Data collection endpoints - moderate limits
        "/analytics/collect": 10,
        "/scheduled-posts/bulk": 15,
        
        # Regular API endpoints - standard limits
        "/analytics/overview": 30,
        "/analytics/chart": 40,
        "/scheduled-posts/create": 20,
        "/scheduled-posts/update": 25,
        "/ab-test/create": 10,
        "/ab-test/details": 30,
        
        # Search and listing endpoints - higher limits
        "/scheduled-posts/search": 50,
        "/scheduled-posts/list": 60,
        "/analytics/recommendations": 20,
    },
    "whitelist_ips": security_settings.ip_whitelist + security_settings.admin_ips,
    "whitelist_paths": [
        "/health",
        "/docs",
        "/openapi.json",
        "/favicon.ico"
    ]
}

# Security headers configuration
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
    "Strict-Transport-Security": f"max-age={security_settings.hsts_max_age}; includeSubDomains"
}

# Content Security Policy
def get_csp_header() -> str:
    """Generate Content Security Policy header."""
    if not security_settings.csp_enabled:
        return ""
    
    csp_directives = [
        f"default-src {' '.join(security_settings.csp_default_src)}",
        f"script-src {' '.join(security_settings.csp_script_src)}",
        f"style-src {' '.join(security_settings.csp_style_src)}",
        f"img-src {' '.join(security_settings.csp_img_src)}",
        "object-src 'none'",
        "base-uri 'self'",
        "form-action 'self'",
        "frame-ancestors 'none'"
    ]
    
    return "; ".join(csp_directives)

# Input validation rules
VALIDATION_RULES = {
    "max_content_length": security_settings.max_content_length,
    "max_file_size_bytes": security_settings.max_file_size_mb * 1024 * 1024,
    "allowed_file_extensions": security_settings.allowed_file_extensions,
    "blocked_file_extensions": security_settings.blocked_file_extensions,
    "dangerous_patterns": [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"vbscript:",
        r"onload\s*=",
        r"onerror\s*=",
        r"onclick\s*=",
        r"eval\s*\(",
        r"document\.cookie",
        r"document\.write",
        r"window\.location"
    ],
    "sql_injection_patterns": [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b)",
        r"(\b(OR|AND)\s+\d+\s*=\s*\d+)",
        r"(\b(OR|AND)\s+['\"].*['\"])",
        r"(--|#|/\*|\*/)",
        r"(\bxp_cmdshell\b)",
        r"(\bsp_executesql\b)"
    ],
    "nosql_injection_patterns": [
        r"\$where",
        r"\$ne",
        r"\$gt",
        r"\$lt",
        r"\$regex",
        r"\$or",
        r"\$and",
        r"function\s*\(",
        r"this\.",
        r"sleep\s*\("
    ]
}

# Audit configuration
AUDIT_CONFIG = {
    "enabled": security_settings.audit_enabled,
    "log_file": security_settings.audit_log_file,
    "retention_days": security_settings.audit_retention_days,
    "events_to_log": [
        "authentication",
        "authorization_failure",
        "data_access",
        "data_modification",
        "admin_action",
        "security_violation",
        "rate_limit_exceeded",
        "suspicious_activity"
    ]
}

# Database security configuration
DATABASE_SECURITY = {
    "connection_timeout": security_settings.db_connection_timeout,
    "query_timeout": security_settings.db_query_timeout,
    "max_connections": security_settings.db_max_connections,
    "enable_query_logging": True,
    "log_slow_queries": True,
    "slow_query_threshold_seconds": 5
}

# Session security configuration
SESSION_CONFIG = {
    "timeout_minutes": security_settings.session_timeout_minutes,
    "secure_cookies": security_settings.session_secure_cookies,
    "httponly_cookies": security_settings.session_httponly_cookies,
    "samesite": security_settings.session_samesite,
    "cookie_name": "social_suit_session",
    "cookie_path": "/",
    "cookie_domain": None  # Set based on environment
}

def get_security_middleware_config() -> Dict:
    """Get configuration for security middleware."""
    return {
        "rate_limiting": RATE_LIMIT_CONFIG,
        "security_headers": SECURITY_HEADERS,
        "csp_header": get_csp_header(),
        "validation_rules": VALIDATION_RULES,
        "audit_config": AUDIT_CONFIG,
        "session_config": SESSION_CONFIG
    }

def is_admin_user(user_email: str, user_ip: str = None) -> bool:
    """Check if user is an admin based on email and/or IP."""
    is_admin_email = user_email in security_settings.admin_emails
    is_admin_ip = user_ip in security_settings.admin_ips if user_ip else False
    
    return is_admin_email or is_admin_ip

def is_whitelisted_ip(ip: str) -> bool:
    """Check if IP is whitelisted."""
    return ip in security_settings.ip_whitelist

def is_blacklisted_ip(ip: str) -> bool:
    """Check if IP is blacklisted."""
    return ip in security_settings.ip_blacklist

def validate_file_upload(filename: str, content_type: str, file_size: int) -> Dict[str, any]:
    """Validate file upload based on security rules."""
    import os
    
    # Check file size
    if file_size > VALIDATION_RULES["max_file_size_bytes"]:
        return {
            "valid": False,
            "error": f"File size exceeds maximum allowed size of {security_settings.max_file_size_mb}MB"
        }
    
    # Check file extension
    file_ext = os.path.splitext(filename)[1].lower()
    
    if file_ext in VALIDATION_RULES["blocked_file_extensions"]:
        return {
            "valid": False,
            "error": f"File type '{file_ext}' is not allowed"
        }
    
    if file_ext not in VALIDATION_RULES["allowed_file_extensions"]:
        return {
            "valid": False,
            "error": f"File type '{file_ext}' is not in allowed extensions"
        }
    
    # Check content type
    dangerous_content_types = [
        "application/x-executable",
        "application/x-msdownload",
        "application/x-msdos-program",
        "application/javascript",
        "text/javascript"
    ]
    
    if content_type in dangerous_content_types:
        return {
            "valid": False,
            "error": f"Content type '{content_type}' is not allowed"
        }
    
    return {"valid": True}

# Export main configuration
__all__ = [
    "security_settings",
    "RATE_LIMIT_CONFIG",
    "SECURITY_HEADERS",
    "VALIDATION_RULES",
    "AUDIT_CONFIG",
    "DATABASE_SECURITY",
    "SESSION_CONFIG",
    "get_security_middleware_config",
    "get_csp_header",
    "is_admin_user",
    "is_whitelisted_ip",
    "is_blacklisted_ip",
    "validate_file_upload"
]