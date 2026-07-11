from pydantic import BaseModel, EmailStr, Field
from uuid import UUID
from datetime import date, datetime
from typing import Any

from app.core.enums import EmployeeRole, EmployeeStatus
from pydantic import field_validator

class EmployeeBase(BaseModel):
    employee_code: str
    first_name: str
    last_name: str
    gender: str
    phone: str | None = None
    email: EmailStr
    hire_date: date
    role: EmployeeRole = EmployeeRole.EMPLOYEE
    department_id: UUID | None = None
    position: str | None = None
    default_shift_id: UUID | None = None
    weekly_off_days: int | None = None
    can_cover_night_shift: bool = False
    secondary_phone: str | None = None
    secondary_email: EmailStr | None = None
    can_create_tables: bool = False
    can_manage_help_docs: bool = False
    can_post_announcements: bool = False
    can_manage_fiberx_data: bool = False
    ui_preferences: dict[str, Any] | None = None

    @field_validator("department_id", "default_shift_id", mode="before")
    @classmethod
    def empty_str_to_none(cls, v: Any) -> Any:
        if v == "":
            return None
        return v

class EmployeeCreate(EmployeeBase):
    password: str = Field(min_length=6)

class EmployeeUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    gender: str | None = None
    phone: str | None = None
    email: EmailStr | None = None
    role: EmployeeRole | None = None
    department_id: UUID | None = None
    position: str | None = None
    default_shift_id: UUID | None = None
    weekly_off_days: int | None = None
    can_cover_night_shift: bool | None = None
    status: EmployeeStatus | None = None
    secondary_phone: str | None = None
    secondary_email: EmailStr | None = None
    can_create_tables: bool | None = None
    can_manage_help_docs: bool | None = None
    can_post_announcements: bool | None = None
    can_manage_fiberx_data: bool | None = None
    ui_preferences: dict[str, Any] | None = None

class EmployeeResponse(EmployeeBase):
    id: UUID
    status: EmployeeStatus
    profile_image: str | None = None
    last_login: datetime | None = None
    created_at: datetime
    updated_at: datetime | None = None
    created_by: UUID | None = None

    model_config = {"from_attributes": True}
