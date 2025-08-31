"""Pydantic schemas for API request/response validation."""

from pydantic import BaseModel, EmailStr, Field


class LoginRequestSchema(BaseModel):
    """Request schema for user login."""

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="User password")

    class Config:
        json_schema_extra = {
            "example": {"email": "user@example.com", "password": "SecurePassword123"}
        }


class LoginResponseSchema(BaseModel):
    """Response schema for successful login."""

    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")

    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                "token_type": "bearer",
            }
        }


class RegisterRequestSchema(BaseModel):
    """Request schema for user registration."""

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="User password")

    class Config:
        json_schema_extra = {
            "example": {"email": "newuser@example.com", "password": "SecurePassword123"}
        }


class RegisterResponseSchema(BaseModel):
    """Response schema for successful registration."""

    user_id: str = Field(..., description="Created user ID")
    email: str = Field(..., description="User email address")
    message: str = Field(
        default="User created successfully", description="Success message"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "550e8400-e29b-41d4-a716-446655440000",
                "email": "newuser@example.com",
                "message": "User created successfully",
            }
        }


class ValidateTokenRequestSchema(BaseModel):
    """Request schema for token validation."""

    token: str = Field(..., description="JWT token to validate")

    class Config:
        json_schema_extra = {
            "example": {"token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."}
        }


class ValidateTokenResponseSchema(BaseModel):
    """Response schema for token validation."""

    is_valid: bool = Field(..., description="Whether the token is valid")
    user_id: str | None = Field(None, description="User ID if token is valid")
    email: str | None = Field(None, description="User email if token is valid")
    permissions: list[str] = Field(default_factory=list, description="User permissions")
    error: str | None = Field(None, description="Error message if token is invalid")

    class Config:
        json_schema_extra = {
            "example": {
                "is_valid": True,
                "user_id": "550e8400-e29b-41d4-a716-446655440000",
                "email": "user@example.com",
                "permissions": ["read", "write"],
                "error": None,
            }
        }


class ErrorResponseSchema(BaseModel):
    """Standard error response schema."""

    error: str = Field(..., description="Error message")
    detail: str | None = Field(None, description="Additional error details")

    class Config:
        json_schema_extra = {
            "example": {
                "error": "Invalid credentials",
                "detail": "Email or password is incorrect",
            }
        }


class HealthCheckResponseSchema(BaseModel):
    """Health check response schema."""

    status: str = Field(..., description="Service health status")
    timestamp: str = Field(..., description="Current timestamp")
    version: str = Field(..., description="Service version")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "timestamp": "2024-01-15T10:30:00Z",
                "version": "1.0.0",
            }
        }
