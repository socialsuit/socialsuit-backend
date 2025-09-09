"""Health check endpoints for FastAPI applications.

This module provides utilities for setting up health check endpoints in FastAPI applications.
"""

from typing import Callable, Dict, List, Optional, Union

from fastapi import FastAPI, Response, status
from pydantic import BaseModel


class HealthStatus(BaseModel):
    """Health status response model."""
    status: str
    version: str
    details: Dict[str, Dict[str, Union[str, bool]]]


class HealthCheckConfig:
    """Configuration for health check endpoints."""
    
    def __init__(
        self,
        app: FastAPI,
        version: str,
        healthz_path: str = "/healthz",
        readyz_path: str = "/readyz",
        liveness_checks: Optional[List[Callable[[], bool]]] = None,
        readiness_checks: Optional[List[Callable[[], bool]]] = None,
    ):
        """Initialize the health check configuration.
        
        Args:
            app: The FastAPI application
            version: The application version
            healthz_path: The path for the liveness endpoint
            readyz_path: The path for the readiness endpoint
            liveness_checks: Optional list of liveness check functions
            readiness_checks: Optional list of readiness check functions
        """
        self.app = app
        self.version = version
        self.healthz_path = healthz_path
        self.readyz_path = readyz_path
        self.liveness_checks = liveness_checks or []
        self.readiness_checks = readiness_checks or []


def setup_health_endpoints(config: HealthCheckConfig) -> None:
    """Set up health check endpoints in a FastAPI application.
    
    Args:
        config: The health check configuration
    """
    app = config.app
    
    @app.get(config.healthz_path, tags=["Health"])
    async def healthz() -> Response:
        """Liveness probe endpoint.
        
        This endpoint checks if the application is running and responding to requests.
        It is used by Kubernetes to determine if the pod is alive.
        """
        # Run liveness checks
        details = {}
        all_healthy = True
        
        for i, check in enumerate(config.liveness_checks):
            check_name = getattr(check, "__name__", f"liveness_check_{i}")
            try:
                result = check()
                details[check_name] = {
                    "status": "up" if result else "down",
                    "healthy": result,
                }
                if not result:
                    all_healthy = False
            except Exception as e:
                details[check_name] = {
                    "status": "error",
                    "message": str(e),
                    "healthy": False,
                }
                all_healthy = False
        
        # Always include a basic check
        if not details:
            details["application"] = {"status": "up", "healthy": True}
        
        status_code = status.HTTP_200_OK if all_healthy else status.HTTP_503_SERVICE_UNAVAILABLE
        
        return Response(
            content=HealthStatus(
                status="healthy" if all_healthy else "unhealthy",
                version=config.version,
                details=details,
            ).json(),
            media_type="application/json",
            status_code=status_code,
        )
    
    @app.get(config.readyz_path, tags=["Health"])
    async def readyz() -> Response:
        """Readiness probe endpoint.
        
        This endpoint checks if the application is ready to receive traffic.
        It is used by Kubernetes to determine if the pod is ready to receive requests.
        """
        # Run readiness checks
        details = {}
        all_ready = True
        
        # Run liveness checks first
        for i, check in enumerate(config.liveness_checks):
            check_name = getattr(check, "__name__", f"liveness_check_{i}")
            try:
                result = check()
                details[check_name] = {
                    "status": "up" if result else "down",
                    "ready": result,
                }
                if not result:
                    all_ready = False
            except Exception as e:
                details[check_name] = {
                    "status": "error",
                    "message": str(e),
                    "ready": False,
                }
                all_ready = False
        
        # Then run readiness checks
        for i, check in enumerate(config.readiness_checks):
            check_name = getattr(check, "__name__", f"readiness_check_{i}")
            try:
                result = check()
                details[check_name] = {
                    "status": "up" if result else "down",
                    "ready": result,
                }
                if not result:
                    all_ready = False
            except Exception as e:
                details[check_name] = {
                    "status": "error",
                    "message": str(e),
                    "ready": False,
                }
                all_ready = False
        
        # Always include a basic check
        if not details:
            details["application"] = {"status": "up", "ready": True}
        
        status_code = status.HTTP_200_OK if all_ready else status.HTTP_503_SERVICE_UNAVAILABLE
        
        return Response(
            content=HealthStatus(
                status="ready" if all_ready else "not_ready",
                version=config.version,
                details=details,
            ).json(),
            media_type="application/json",
            status_code=status_code,
        )