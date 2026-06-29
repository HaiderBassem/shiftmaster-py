from pydantic import BaseModel
from uuid import UUID
from datetime import datetime

class HandoverCommentBase(BaseModel):
    employee_id: UUID
    comment: str

class HandoverCommentResponse(HandoverCommentBase):
    created_at: datetime
    employee_name: str | None = None
    profile_image: str | None = None

class HandoverBase(BaseModel):
    department_id: UUID
    shift_id: UUID | None = None
    general_notes: str | None = None
    issues_reported: str | None = None
    pending_tasks: str | None = None
    keys_handed_over: bool = False
    equipment_status: str | None = None

class HandoverCreate(HandoverBase):
    pass

class HandoverResponse(HandoverBase):
    id: UUID
    handover_date: datetime
    status: str
    created_by: UUID
    claimed_by: UUID | None = None
    claimed_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime | None = None
    comments: list[HandoverCommentResponse] = []

    model_config = {"from_attributes": True}
