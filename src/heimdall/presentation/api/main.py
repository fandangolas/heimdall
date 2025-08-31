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

# PostgreSQL imports (available in all modes, will gracefully handle missing deps)
try:
    from heimdall.infrastructure.persistence.postgres.database import (
        close_database,
        initialize_database,
    )

    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False
    initialize_database = None
    close_database = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """Application lifespan manager for startup and shutdown events."""
    # Startup
    print("🚀 Heimdall authentication service starting up...")

    # Initialize database if using PostgreSQL
    persistence_mode = os.getenv("PERSISTENCE_MODE", "in-memory").lower()
    use_postgres = persistence_mode == "postgres"

    if use_postgres:
        if POSTGRES_AVAILABLE and initialize_database:
            try:
                await initialize_database()
                print("✅ PostgreSQL database connection initialized")
            except Exception as e:
                print(
                    f"⚠️ Failed to initialize database: {e}, "
                    "using in-memory repositories"
                )
        else:
            print(
                "⚠️ PostgreSQL dependencies not available, using in-memory repositories"
            )
            print("   Install with: pip install asyncpg")

    print("✅ Heimdall ready to guard the Bifrost Bridge!")

    yield

    # Shutdown
    print("🛑 Heimdall authentication service shutting down...")

    # Close database connections if using PostgreSQL
    persistence_mode = os.getenv("PERSISTENCE_MODE", "in-memory").lower()
    if persistence_mode == "postgres" and POSTGRES_AVAILABLE and close_database:
        try:
            await close_database()
            print("✅ PostgreSQL database connections closed")
        except Exception as e:
            print(f"⚠️ Error closing database: {e}")

    print("✅ Heimdall shutdown complete")


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    # Application metadata
    app = FastAPI(
        title="Heimdall Authentication Service",
        description=(
            "High-performance distributed authentication and authorization system"
        ),
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
            "description": (
                "Guardian of the Bifrost Bridge - High-performance auth service"
            ),
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
        host="127.0.0.1",  # Bind to localhost only for security
        port=8000,
        reload=True,
        log_level="info",
    )
