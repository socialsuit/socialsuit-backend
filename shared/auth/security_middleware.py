from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import time
import logging
import json
import re
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
import ipaddress

logger = logging.getLogger(__name__)

class SecurityMiddleware(BaseHTTPMiddleware):
    """Comprehensive security middleware."""
    
    def __init__(
        self,
        app: ASGIApp,
        rate_limiter: Optional[Any] = None,
        security_headers: Optional[Dict[str, str]] = None,
        enable_rate_limiting: bool = True,
        enable_security_headers: bool = True,
        enable_input_validation: bool = False,
        enable_ip_filtering: bool = False,
        enable_audit_logging: bool = True,
        validation_rules: Optional[Dict[str, Any]] = None,
        ip_whitelist: Optional[List[str]] = None,
        ip_blacklist: Optional[List[str]] = None,
        audit_callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ):
        super().__init__(app)
        self.rate_limiter = rate_limiter
        self.security_headers = security_headers or {}
        self.enable_rate_limiting = enable_rate_limiting
        self.enable_security_headers = enable_security_headers
        self.enable_input_validation = enable_input_validation
        self.enable_ip_filtering = enable_ip_filtering
        self.enable_audit_logging = enable_audit_logging
        self.validation_rules = validation_rules or {}
        self.ip_whitelist = ip_whitelist or []
        self.ip_blacklist = ip_blacklist or []
        self.audit_callback = audit_callback
    
    async def dispatch(self, request: Request, call_next):
        """Process the request through security middleware."""
        start_time = time.time()
        client_ip = self._get_client_ip(request)
        request_id = self._generate_request_id()
        
        # Store request info for audit logging
        audit_info = {
            "request_id": request_id,
            "timestamp": datetime.utcnow().isoformat(),
            "client_ip": client_ip,
            "method": request.method,
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "headers": dict(request.headers),
        }
        
        # 1. IP Filtering
        if self.enable_ip_filtering:
            if not self._is_ip_allowed(client_ip):
                return JSONResponse(
                    status_code=403,
                    content={"detail": "Access denied by IP filtering"}
                )
        
        # 2. Rate Limiting
        if self.enable_rate_limiting and self.rate_limiter:
            try:
                await self.rate_limiter.check_rate_limit(request)
            except HTTPException as exc:
                audit_info["status_code"] = exc.status_code
                audit_info["response"] = {"detail": exc.detail}
                audit_info["processing_time"] = time.time() - start_time
                
                if self.enable_audit_logging:
                    self._log_audit(audit_info)
                
                return JSONResponse(
                    status_code=exc.status_code,
                    content={"detail": exc.detail}
                )
        
        # 3. Input Validation (if enabled)
        if self.enable_input_validation:
            validation_result = await self._validate_request(request)
            if validation_result is not None:
                audit_info["status_code"] = 400
                audit_info["response"] = {"detail": validation_result}
                audit_info["processing_time"] = time.time() - start_time
                
                if self.enable_audit_logging:
                    self._log_audit(audit_info)
                
                return JSONResponse(
                    status_code=400,
                    content={"detail": validation_result}
                )
        
        # Process the request
        try:
            response = await call_next(request)
            
            # 4. Add Security Headers
            if self.enable_security_headers:
                self._add_security_headers(response)
            
            # Complete audit info
            audit_info["status_code"] = response.status_code
            audit_info["processing_time"] = time.time() - start_time
            
            # 5. Audit Logging
            if self.enable_audit_logging:
                self._log_audit(audit_info)
            
            return response
            
        except Exception as e:
            logger.error(f"Error in security middleware: {str(e)}")
            audit_info["status_code"] = 500
            audit_info["error"] = str(e)
            audit_info["processing_time"] = time.time() - start_time
            
            if self.enable_audit_logging:
                self._log_audit(audit_info)
            
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error"}
            )
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request headers or connection info."""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"
    
    def _generate_request_id(self) -> str:
        """Generate a unique request ID."""
        import uuid
        return str(uuid.uuid4())
    
    def _is_ip_allowed(self, ip: str) -> bool:
        """Check if an IP is allowed based on whitelist/blacklist."""
        # If IP is in blacklist, deny access
        for ip_range in self.ip_blacklist:
            try:
                if self._ip_in_network(ip, ip_range):
                    return False
            except ValueError:
                continue
        
        # If whitelist is empty, allow all IPs not in blacklist
        if not self.ip_whitelist:
            return True
        
        # If whitelist is not empty, only allow IPs in whitelist
        for ip_range in self.ip_whitelist:
            try:
                if self._ip_in_network(ip, ip_range):
                    return True
            except ValueError:
                continue
        
        return False
    
    def _ip_in_network(self, ip: str, network: str) -> bool:
        """Check if an IP is in a network range."""
        try:
            if '/' in network:
                return ipaddress.ip_address(ip) in ipaddress.ip_network(network, strict=False)
            else:
                return ip == network
        except ValueError:
            return False
    
    async def _validate_request(self, request: Request) -> Optional[str]:
        """Validate request based on validation rules."""
        path = request.url.path
        method = request.method
        
        # Find matching validation rule
        for pattern, rules in self.validation_rules.items():
            if re.match(pattern, path) and method in rules.get("methods", [method]):
                # Validate headers
                if "required_headers" in rules:
                    for header in rules["required_headers"]:
                        if header not in request.headers:
                            return f"Missing required header: {header}"
                
                # Validate query parameters
                if "required_params" in rules:
                    for param in rules["required_params"]:
                        if param not in request.query_params:
                            return f"Missing required query parameter: {param}"
                
                # Validate body (if applicable)
                if "validate_body" in rules and rules["validate_body"]:
                    try:
                        body = await request.json()
                        
                        # Check required fields
                        if "required_fields" in rules:
                            for field in rules["required_fields"]:
                                if field not in body:
                                    return f"Missing required field in request body: {field}"
                        
                        # Check field types
                        if "field_types" in rules:
                            for field, expected_type in rules["field_types"].items():
                                if field in body:
                                    if expected_type == "string" and not isinstance(body[field], str):
                                        return f"Field {field} must be a string"
                                    elif expected_type == "number" and not isinstance(body[field], (int, float)):
                                        return f"Field {field} must be a number"
                                    elif expected_type == "boolean" and not isinstance(body[field], bool):
                                        return f"Field {field} must be a boolean"
                                    elif expected_type == "array" and not isinstance(body[field], list):
                                        return f"Field {field} must be an array"
                                    elif expected_type == "object" and not isinstance(body[field], dict):
                                        return f"Field {field} must be an object"
                    except Exception:
                        return "Invalid JSON in request body"
        
        return None
    
    def _add_security_headers(self, response: Response) -> None:
        """Add security headers to the response."""
        for header, value in self.security_headers.items():
            response.headers[header] = value
    
    def _log_audit(self, audit_info: Dict[str, Any]) -> None:
        """Log audit information."""
        # Log to file/console
        logger.info(f"AUDIT: {json.dumps(audit_info)}")
        
        # Call audit callback if provided
        if self.audit_callback:
            try:
                self.audit_callback(audit_info)
            except Exception as e:
                logger.error(f"Error in audit callback: {str(e)}")