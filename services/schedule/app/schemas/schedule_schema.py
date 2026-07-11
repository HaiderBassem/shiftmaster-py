from pydantic import BaseModel
from uuid import UUID
from datetime import date, datetime
from typing import Any

from app.core.enums import ShiftStatus, ScheduleStatus

# ── Templates ──
class ScheduleTemplateBase(BaseModel):
    employee_id: UUID
    day_of_week: int
    shift_id: UUID | None = None
    is_off: bool = False
    valid_from: datetime
    valid_to: datetime | None = None

class ScheduleTemplateCreate(BaseModel):
    employee_id: UUID
    day_of_week: int
    shift_id: UUID | None = None
    is_off: bool = False

class ScheduleTemplateResponse(ScheduleTemplateBase):
    id: UUID
    created_at: datetime
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}

# ── Weekly Schedule ──
class WeeklyScheduleBase(BaseModel):
    week_start_date: date
    week_end_date: date
    template_id: UUID | None = None
    status: ScheduleStatus = ScheduleStatus.DRAFT
    notes: str | None = None

class WeeklyScheduleCreate(WeeklyScheduleBase):
    published_by: UUID | None = None

class WeeklyScheduleResponse(WeeklyScheduleBase):
    id: UUID
    published_by: UUID | None = None
    published_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}

# ── Employee Shift ──
class EmployeeShiftBase(BaseModel):
    schedule_id: UUID | None = None
    employee_id: UUID
    shift_id: UUID | None = None
    shift_date: date
    shift_status: ShiftStatus
    leave_reason: str | None = None

class EmployeeShiftCreate(EmployeeShiftBase):
    created_by: UUID | None = None
    is_replacement: bool = False
    replaced_employee_id: UUID | None = None
    replacement_approved_by: UUID | None = None

class EmployeeShiftUpdate(BaseModel):
    shift_id: UUID | None = None
    shift_status: ShiftStatus | None = None
    leave_reason: str | None = None
    is_replacement: bool | None = None
    replaced_employee_id: UUID | None = None
    replacement_approved_by: UUID | None = None

class EmployeeShiftResponse(EmployeeShiftBase):
    id: UUID
    is_replacement: bool
    replaced_employee_id: UUID | None = None
    replacement_approved_by: UUID | None = None
    check_in_time: datetime | None = None
    check_out_time: datetime | None = None
    actual_worked_hours: float | None = None
    overtime_hours: float | None = None
    created_at: datetime
    updated_at: datetime | None = None
    created_by: UUID | None = None

    model_config = {"from_attributes": True}
