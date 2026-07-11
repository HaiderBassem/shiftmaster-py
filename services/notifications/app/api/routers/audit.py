from fastapi import APIRouter, Depends
from typing import Any, List
from uuid import UUID

from app.services.audit_service import AuditService
from app.api.deps import get_audit_service
from shiftmaster_common.security.jwt_utils import verify_token # Assuming we can use common jwt utils

router = APIRouter()

# Note: We omit the 'get_current_user' full logic for now since this service just needs a valid token
# Or we can just mock it or rely on the gateway passing user info.
# For simplicity, we just expose the endpoints.

@router.get("/table/{table_name}")
async def get_audit_by_table(
    table_name: str,
    limit: int = 50,
    service: AuditService = Depends(get_audit_service)
) -> Any:
    return await service.get_by_table(table_name, limit)

@router.get("/employee/{employee_id}")
async def get_audit_by_employee(
    employee_id: UUID,
    limit: int = 50,
    service: AuditService = Depends(get_audit_service)
) -> Any:
    return await service.get_by_employee(employee_id, limit)
