from fastapi import APIRouter, Depends
from typing import Any, List
from uuid import UUID

from app.schemas.audit_schema import AuditLogResponse
from app.services.audit_service import AuditService
from app.api.deps import get_audit_service, get_current_user

router = APIRouter()

@router.get("/table/{table_name}", response_model=List[AuditLogResponse])
async def get_audit_by_table(
    table_name: str,
    limit: int = 50,
    service: AuditService = Depends(get_audit_service),
    current_user: dict = Depends(get_current_user)
) -> Any:
    return await service.get_by_table(table_name, limit)

@router.get("/employee/{employee_id}", response_model=List[AuditLogResponse])
async def get_audit_by_employee(
    employee_id: UUID,
    limit: int = 50,
    service: AuditService = Depends(get_audit_service),
    current_user: dict = Depends(get_current_user)
) -> Any:
    return await service.get_by_employee(employee_id, limit)
