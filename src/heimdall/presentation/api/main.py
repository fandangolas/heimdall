"""FastAPI main application configuration."""

import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from heimdall.presentation.api.health import router as health_router
from heimdall.presentation.api.routes import router as auth_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """Application lifespan manager for startup and shutdown events."""
    # Startup
    print("🚀 Heimdall authentication service starting up...")

    # TODO: Initialize database connections, Redis, etc.
    # For now using in-memory implementations

    print("✅ Heimdall ready to guard the Bifrost Bridge!")

    yield

    # Shutdown
    print("🛑 Heimdall authentication service shutting down...")

    # TODO: Close database connections, cleanup resources

    print("✅ Heimdall shutdown complete")


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    # Application metadata
    app = FastAPI(
        title="Heimdall Authentication Service",
        description="High-performance distributed authentication and authorization system",
        version=os.getenv("HEIMDALL_VERSION", "1.0.0-dev"),
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # CORS middleware for frontend integration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # TODO: Configure for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Custom exception handlers
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        """Handle HTTP exceptions with consistent error format."""
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.detail,
                "status_code": exc.status_code,
                "path": str(request.url),
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ):
        """Handle request validation errors."""
        return JSONResponse(
            status_code=422,
            content={
                "error": "Validation error",
                "detail": exc.errors(),
                "status_code": 422,
                "path": str(request.url),
            },
        )

    # Include routers
    app.include_router(health_router)
    app.include_router(auth_router)

    # Root endpoint
    @app.get("/", tags=["root"])
    async def root():
        """Root endpoint with service information."""
        return {
            "service": "Heimdall Authentication Service",
            "version": os.getenv("HEIMDALL_VERSION", "1.0.0-dev"),
            "description": "Guardian of the Bifrost Bridge - High-performance auth for microservices",
            "docs": "/docs",
            "health": "/health",
            "auth_endpoints": {
                "login": "/auth/login",
                "register": "/auth/register",
                "validate": "/auth/validate",
                "me": "/auth/me",
            },
        }

    return app


# Create the application instance
app = create_app()


# For development server
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "heimdall.presentation.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
