from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Any

class AuditLogResponse(BaseModel):
    id: UUID
    employee_id: UUID
    action: str
    table_name: str
    record_id: UUID
    old_data: dict[str, Any] | None = None
    new_data: dict[str, Any] | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
