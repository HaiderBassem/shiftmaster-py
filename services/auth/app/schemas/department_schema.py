from pydantic import BaseModel
from uuid import UUID
from datetime import datetime

class DepartmentBase(BaseModel):
    department_code: str
    name: str
    description: str | None = None
    max_leaves_per_day: int = 1
    active_modules: list[str] | None = None
    manager_ids: list[UUID] | None = None

class DepartmentCreate(DepartmentBase):
    pass

class DepartmentUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    max_leaves_per_day: int | None = None
    active_modules: list[str] | None = None
    manager_ids: list[UUID] | None = None

class DepartmentResponse(DepartmentBase):
    id: UUID
    fiberx_enabled: bool
    created_at: datetime
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}
