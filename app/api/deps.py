from fastapi import Depends, HTTPException, status, Header
from psycopg_pool import AsyncConnectionPool
from psycopg import AsyncConnection
from redis.asyncio import Redis

import app.db.pool as db_module
from app.core.redis import get_redis as _get_redis

from app.repositories.employee_repo import EmployeeRepository
from app.services.employee_service import EmployeeService

from app.repositories.department_repo import DepartmentRepository
from app.services.department_service import DepartmentService

from app.repositories.shift_repo import ShiftRepository
from app.services.shift_service import ShiftService

from app.services.task_service import TaskService
from app.services.notification_service import NotificationService
from app.repositories.handover_repo import HandoverRepository
from app.services.handover_service import HandoverService

from app.repositories.schedule_repo import ScheduleRepository
from app.services.schedule_service import ScheduleService

from app.repositories.task_repo import TaskRepository
from app.services.task_service import TaskService

from app.repositories.audit_repo import AuditRepository
from app.services.audit_service import AuditService



def get_db_pool() -> AsyncConnectionPool:
    if db_module.pool is None:
        raise Exception("Database pool is not initialized")
    return db_module.pool

async def get_db_connection(pool: AsyncConnectionPool = Depends(get_db_pool)) -> AsyncConnection:
    async with pool.connection() as conn:
        yield conn

def get_redis_client() -> Redis:
    """FastAPI dependency — returns the shared Redis client."""
    return _get_redis()

# Repositories 

def get_employee_repo(conn: AsyncConnection = Depends(get_db_connection)) -> EmployeeRepository:
    return EmployeeRepository(conn)

def get_department_repo(conn: AsyncConnection = Depends(get_db_connection)) -> DepartmentRepository:
    return DepartmentRepository(conn)

def get_shift_repo(conn: AsyncConnection = Depends(get_db_connection)) -> ShiftRepository:
    return ShiftRepository(conn)

def get_handover_repo(conn: AsyncConnection = Depends(get_db_connection)) -> HandoverRepository:
    return HandoverRepository(conn)

def get_schedule_repo(conn: AsyncConnection = Depends(get_db_connection)) -> ScheduleRepository:
    return ScheduleRepository(conn)

def get_task_repo(conn: AsyncConnection = Depends(get_db_connection)) -> TaskRepository:
    return TaskRepository(conn)

def get_audit_repo(conn: AsyncConnection = Depends(get_db_connection)) -> AuditRepository:
    return AuditRepository(conn)

# Services 

def get_employee_service(repo: EmployeeRepository = Depends(get_employee_repo)) -> EmployeeService:
    return EmployeeService(repo)

def get_department_service(repo: DepartmentRepository = Depends(get_department_repo)) -> DepartmentService:
    return DepartmentService(repo)

def get_shift_service(repo: ShiftRepository = Depends(get_shift_repo)) -> ShiftService:
    return ShiftService(repo)

def get_handover_service(repo: HandoverRepository = Depends(get_handover_repo)) -> HandoverService:
    return HandoverService(repo)

def get_schedule_service(repo: ScheduleRepository = Depends(get_schedule_repo)) -> ScheduleService:
    return ScheduleService(repo)

def get_task_service(repo: TaskRepository = Depends(get_task_repo)) -> TaskService:
    return TaskService(repo)

def get_notification_service() -> NotificationService:
    return NotificationService()

def get_audit_service(repo: AuditRepository = Depends(get_audit_repo)) -> AuditService:
    return AuditService(repo)

# Authentication 

async def get_current_user(
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
    employee_service: EmployeeService = Depends(get_employee_service)
) -> dict:
    if not x_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-User-Id header",
        )
    try:
        user = await employee_service.get_by_id(x_user_id)
        if user["status"] != "active":
            raise HTTPException(status_code=403, detail="Inactive user")
        return user
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user")

class RequireRoles:
    def __init__(self, allowed_roles: list[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: dict = Depends(get_current_user)) -> dict:
        if current_user["role"] not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation not permitted. Required roles: {', '.join(self.allowed_roles)}"
            )
        return current_user
