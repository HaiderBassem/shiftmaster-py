"""
Authentication routes.

Rate limiting (backed by Redis):
- POST /login         → max 5 attempts per IP per 5 minutes
- POST /swagger-login → same policy

On a successful login the per-IP counter is reset so legitimate users
are never locked out after a brief flood of failed attempts.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from typing import Any

from app.schemas.auth_schema import Token, LoginRequest
from app.schemas.employee_schema import EmployeeResponse
from app.services.employee_service import EmployeeService
from shiftmaster_common.security.jwt_utils import verify_password, create_access_token
from shiftmaster_common.middleware.exceptions import AppException, NotFoundError
from shiftmaster_common.cache.redis_client import rate_limit_check, rate_limit_reset
from app.core.config import settings
from app.api.deps import get_employee_service, get_current_user

router = APIRouter()


def _client_ip(request: Request) -> str:
    """Return the best-guess client IP for rate-limit keying."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


async def _authenticate(
    email: str,
    password: str,
    employee_service: EmployeeService,
    client_ip: str,
) -> dict:
    """
    Shared auth logic used by both the JSON login and Swagger form login.
    Raises HTTPException on any failure so the caller always returns
    the same vague error message regardless of the failure reason.
    """
    rate_key = f"login:{client_ip}"
    exceeded = await rate_limit_check(
        key=rate_key,
        max_requests=settings.redis.login_max_attempts,
        window_seconds=settings.redis.login_window_seconds,
    )
    if exceeded:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please try again later.",
        )

    _bad_credentials = HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Incorrect email or password",
    )

    try:
        user = await employee_service.get_by_email(email)
    except NotFoundError:
        raise _bad_credentials

    if not verify_password(password, user["password_hash"]):
        raise _bad_credentials

    if user["status"] != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user account",
        )

    # Successful login — reset the rate-limit counter for this IP
    await rate_limit_reset(rate_key)
    return user


@router.post("/swagger-login", response_model=Token, include_in_schema=False)
async def swagger_login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    employee_service: EmployeeService = Depends(get_employee_service),
) -> Any:
    """OAuth2-compatible token login required for Swagger UI."""
    user = await _authenticate(
        email=form_data.username,
        password=form_data.password,
        employee_service=employee_service,
        client_ip=_client_ip(request),
    )
    access_token = create_access_token(data={"sub": str(user["id"]), "role": user["role"]}, secret=settings.jwt.secret)
    return {"access_token": access_token, "token_type": "bearer"}


@router.post(
    "/login", 
    response_model=Token,
    summary="Authenticate user and get token",
    description="Authenticates a user via email and password, returning a JWT bearer token.",
    responses={
        200: {"description": "Successfully authenticated"},
        400: {"description": "Incorrect email or password, or inactive account"},
        429: {"description": "Too many login attempts"}
    }
)
async def login(
    request: Request,
    login_data: LoginRequest,
    employee_service: EmployeeService = Depends(get_employee_service),
) -> Any:
    """JSON login endpoint for API clients."""
    user = await _authenticate(
        email=login_data.email,
        password=login_data.password,
        employee_service=employee_service,
        client_ip=_client_ip(request),
    )
    access_token = create_access_token(data={"sub": str(user["id"]), "role": user["role"]}, secret=settings.jwt.secret)
    return {"access_token": access_token, "token_type": "bearer"}


@router.get(
    "/me", 
    response_model=EmployeeResponse,
    summary="Get current user profile",
    description="Returns the profile information of the currently authenticated user based on the provided token.",
    responses={
        200: {"description": "Profile retrieved successfully"},
        401: {"description": "Not authenticated or token expired"},
        403: {"description": "Not enough privileges"}
    }
)
async def get_me(current_user: dict = Depends(get_current_user)) -> Any:
    """Return the currently authenticated user's profile."""
    return current_user
