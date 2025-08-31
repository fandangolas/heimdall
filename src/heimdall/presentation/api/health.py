"""Health check endpoints for monitoring and observability."""

import os
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from heimdall.presentation.api.schemas import HealthCheckResponseSchema

router = APIRouter(tags=["health"])


def get_system_info() -> dict[str, Any]:
    """Get basic system information for health checks."""
    return {
        "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "version": os.getenv("HEIMDALL_VERSION", "1.0.0-dev"),
        "environment": os.getenv("ENVIRONMENT", "development"),
        "python_version": (
            f"{os.sys.version_info.major}.{os.sys.version_info.minor}."
            f"{os.sys.version_info.micro}"
        ),
    }


@router.get(
    "/health",
    response_model=HealthCheckResponseSchema,
    summary="Health Check",
    description="Basic health check endpoint for load balancer and monitoring",
)
async def health_check(
    system_info: dict[str, Any] = Depends(get_system_info),
) -> HealthCheckResponseSchema:
    """Basic health check endpoint."""
    return HealthCheckResponseSchema(
        status="healthy",
        timestamp=system_info["timestamp"],
        version=system_info["version"],
    )


@router.get(
    "/health/detailed",
    summary="Detailed Health Check",
    description="Detailed health check with system information and dependency status",
)
async def detailed_health_check(
    system_info: dict[str, Any] = Depends(get_system_info),
) -> JSONResponse:
    """Detailed health check with system and dependency information."""
    # TODO: Add actual dependency checks when implemented
    dependencies = {
        "database": {"status": "healthy", "type": "in-memory"},
        "cache": {"status": "healthy", "type": "in-memory"},
        "event_bus": {"status": "healthy", "type": "in-memory"},
    }

    health_data = {
        "status": "healthy",
        "timestamp": system_info["timestamp"],
        "version": system_info["version"],
        "environment": system_info["environment"],
        "system": {
            "python_version": system_info["python_version"],
            "uptime": "N/A",  # TODO: Track service start time
        },
        "dependencies": dependencies,
        "metrics": {
            "total_requests": 0,  # TODO: Add request counter middleware
            "active_sessions": 0,  # TODO: Get from session repository
            "cache_hit_rate": 0.0,  # TODO: Add cache metrics
        },
    }

    return JSONResponse(content=health_data)


@router.get(
    "/ready",
    summary="Readiness Check",
    description="Kubernetes readiness probe endpoint",
)
async def readiness_check() -> JSONResponse:
    """Kubernetes readiness probe endpoint."""
    # TODO: Check if all dependencies are ready
    # For now, always return ready since we use in-memory implementations

    return JSONResponse(
        content={
            "status": "ready",
            "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        }
    )


@router.get(
    "/live",
    summary="Liveness Check",
    description="Kubernetes liveness probe endpoint",
)
async def liveness_check() -> JSONResponse:
    """Kubernetes liveness probe endpoint."""
    # Basic liveness check - if we can respond, we're alive
    return JSONResponse(
        content={
            "status": "alive",
            "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        }
    )
