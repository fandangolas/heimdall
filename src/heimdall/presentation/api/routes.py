"""FastAPI authentication routes."""

from collections.abc import Callable
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from heimdall.application.dto import LoginRequest, RegisterRequest
from heimdall.domain.value_objects import Token
from heimdall.presentation.api.dependencies import get_auth_functions
from heimdall.presentation.api.schemas import (
    ErrorResponseSchema,
    LoginRequestSchema,
    LoginResponseSchema,
    RegisterRequestSchema,
    RegisterResponseSchema,
    ValidateTokenRequestSchema,
    ValidateTokenResponseSchema,
)

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post(
    "/login",
    response_model=LoginResponseSchema,
    responses={
        400: {"model": ErrorResponseSchema, "description": "Invalid credentials"},
        422: {"model": ErrorResponseSchema, "description": "Validation error"},
    },
    summary="User Login",
    description="Authenticate user with email and password, returns JWT access token",
)
async def login(
    request: LoginRequestSchema,
    auth_functions: dict[str, Callable[..., Any]] = Depends(get_auth_functions),  # noqa: B008
) -> LoginResponseSchema:
    """Login endpoint for user authentication."""
    try:
        # Convert API schema to domain DTO
        login_request = LoginRequest(
            email=request.email,
            password=request.password,
        )

        # Execute login command through CQRS
        response = await auth_functions["login"](login_request)

        # Convert domain response to API schema
        return LoginResponseSchema(
            access_token=response.access_token,
            token_type="bearer",  # noqa: S106
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from None
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from None


@router.post(
    "/register",
    response_model=RegisterResponseSchema,
    responses={
        400: {"model": ErrorResponseSchema, "description": "User already exists"},
        422: {"model": ErrorResponseSchema, "description": "Validation error"},
    },
    summary="User Registration",
    description="Register a new user account with email and password",
)
async def register(
    request: RegisterRequestSchema,
    auth_functions: dict[str, Callable[..., Any]] = Depends(get_auth_functions),  # noqa: B008
) -> RegisterResponseSchema:
    """Registration endpoint for new user accounts."""
    try:
        # Convert API schema to domain DTO
        register_request = RegisterRequest(
            email=request.email,
            password=request.password,
        )

        # Execute register command through CQRS
        response = await auth_functions["register"](register_request)

        # Convert domain response to API schema
        return RegisterResponseSchema(
            user_id=response.user_id,
            email=response.email,
            message="User created successfully",
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from None
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from None


@router.post(
    "/validate",
    response_model=ValidateTokenResponseSchema,
    responses={
        422: {"model": ErrorResponseSchema, "description": "Validation error"},
    },
    summary="Token Validation",
    description="Validate JWT access token and return user information",
)
async def validate_token(
    request: ValidateTokenRequestSchema,
    auth_functions: dict[str, Callable[..., Any]] = Depends(get_auth_functions),  # noqa: B008
) -> ValidateTokenResponseSchema:
    """Token validation endpoint for authentication verification."""
    try:
        # Convert API schema to domain value object
        token = Token(request.token)

        # Execute validate query through CQRS
        response = await auth_functions["validate"](token)

        # Convert domain response to API schema
        permissions = []
        if response.is_valid and response.permissions:
            permissions = list(response.permissions)

        return ValidateTokenResponseSchema(
            is_valid=response.is_valid,
            user_id=response.user_id if response.is_valid else None,
            email=response.email if response.is_valid else None,
            permissions=permissions,
            error=response.error if not response.is_valid else None,
        )

    except Exception as e:
        # Token validation should not fail with HTTP errors
        # Instead return invalid token response
        return ValidateTokenResponseSchema(
            is_valid=False,
            user_id=None,
            email=None,
            permissions=[],
            error=str(e),
        )


@router.get(
    "/me",
    response_model=ValidateTokenResponseSchema,
    responses={
        401: {"model": ErrorResponseSchema, "description": "Invalid or expired token"},
    },
    summary="Get Current User",
    description="Get current authenticated user information from Authorization header",
)
async def get_current_user(
    authorization: str = Depends(
        lambda: None
    ),  # TODO: Extract from Authorization header
    auth_functions: dict[str, Callable[..., Any]] = Depends(get_auth_functions),  # noqa: B008
) -> ValidateTokenResponseSchema:
    """Get current user information from JWT token in Authorization header."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        # Extract token from Authorization header
        token_value = authorization.replace("Bearer ", "")
        token = Token(token_value)

        # Execute validate query through CQRS
        response = await auth_functions["validate"](token)

        if not response.is_valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=response.error or "Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Convert domain response to API schema
        return ValidateTokenResponseSchema(
            is_valid=response.is_valid,
            user_id=response.user_id,
            email=response.email,
            permissions=list(response.permissions),
            error=None,
        )

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token validation failed",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None
