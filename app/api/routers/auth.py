from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from typing import Any

from app.schemas.auth_schema import Token, LoginRequest
from app.schemas.employee_schema import EmployeeResponse
from app.services.employee_service import EmployeeService
from app.core.security import verify_password, create_access_token
from app.api.deps import get_employee_service, get_current_user

router = APIRouter()

@router.post("/swagger-login", response_model=Token, include_in_schema=False)
async def swagger_login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    employee_service: EmployeeService = Depends(get_employee_service)
) -> Any:
    """OAuth2 compatible token login, required for Swagger UI"""
    try:
        user = await employee_service.get_by_email(form_data.username)
    except Exception:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
        
    if not verify_password(form_data.password, user["password_hash"]):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
        
    if user["status"] != "active":
        raise HTTPException(status_code=400, detail="Inactive user account")
        
    access_token = create_access_token(
        subject=str(user["id"]),
        role=user["role"]
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/login", response_model=Token)
async def login(
    login_data: LoginRequest,
    employee_service: EmployeeService = Depends(get_employee_service)
) -> Any:
    # Authenticate user
    try:
        user = await employee_service.get_by_email(login_data.email)
    except Exception:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
        
    if not verify_password(login_data.password, user["password_hash"]):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
        
    if user["status"] != "active":
        raise HTTPException(status_code=400, detail="Inactive user account")
        
    # Generate token
    access_token = create_access_token(
        subject=str(user["id"]),
        role=user["role"]
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=EmployeeResponse)
async def get_me(current_user: dict = Depends(get_current_user)) -> Any:
    """
    Get current logged in user details.
    """
    return current_user
