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
    shift_summary: str
    pending_issues: str

class HandoverCreate(HandoverBase):
    pass

class HandoverResponse(HandoverBase):
    id: UUID
    creator_id: UUID
    status: str
    claimed_by: UUID | None = None
    done_by: UUID | None = None
    created_at: datetime
    updated_at: datetime | None = None
    comments: list[HandoverCommentResponse] = []
    
    creator_name: str | None = None
    claimer_name: str | None = None
    done_by_name: str | None = None

    model_config = {"from_attributes": True}
