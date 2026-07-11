from pydantic import BaseModel, constr
from uuid import UUID
from datetime import time, datetime

class ShiftBase(BaseModel):
    shift_code: str
    name: str
    name_en: str | None = None
    start_time: time
    end_time: time
    color_code: str | None = None
    requires_vehicle: bool = False
    min_rest_hours: int = 8
    department_id: UUID | None = None

class ShiftCreate(ShiftBase):
    pass

class ShiftUpdate(BaseModel):
    shift_code: str | None = None
    name: str | None = None
    name_en: str | None = None
    start_time: time | None = None
    end_time: time | None = None
    color_code: str | None = None
    requires_vehicle: bool | None = None
    min_rest_hours: int | None = None
    department_id: UUID | None = None

class ShiftResponse(ShiftBase):
    id: UUID
    created_at: datetime

    model_config = {"from_attributes": True}
