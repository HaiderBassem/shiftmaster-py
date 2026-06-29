from pydantic import BaseModel
from uuid import UUID
from datetime import date, datetime
from typing import Any

from app.core.enums import TaskStatus

class TaskScheduleBase(BaseModel):
    title: str
    description: str | None = None
    schedule_type: str
    board_id: UUID | None = None
    shift_id: UUID | None = None
    recurrence: str | None = None
    recurrence_days: list[int] | None = None
    max_assignees: int = 1
    is_active: bool = True

class TaskScheduleCreate(TaskScheduleBase):
    created_by: UUID

class TaskScheduleUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    schedule_type: str | None = None
    board_id: UUID | None = None
    shift_id: UUID | None = None
    recurrence: str | None = None
    recurrence_days: list[int] | None = None
    max_assignees: int | None = None
    is_active: bool | None = None

class TaskScheduleResponse(TaskScheduleBase):
    id: UUID
    created_by: UUID
    created_at: datetime
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}

class TaskAssignmentCreate(BaseModel):
    schedule_id: UUID
    employee_id: UUID
    assigned_date: date
    assigned_by: UUID | None = None

class TaskAssignmentResponse(BaseModel):
    id: UUID
    schedule_id: UUID
    employee_id: UUID
    assigned_date: date
    assigned_by: UUID | None = None
    created_at: datetime

    model_config = {"from_attributes": True}

class TaskExecutionBase(BaseModel):
    assignment_id: UUID
    status: TaskStatus = TaskStatus.PENDING

class TaskExecutionResponse(TaskExecutionBase):
    id: UUID
    started_at: datetime | None = None
    completed_at: datetime | None = None
    completion_type: str | None = None
    notes: str | None = None
    attachments: list[str] | None = None
    created_at: datetime
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}
