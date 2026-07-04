from fastapi import APIRouter

from app.api.routers import (
    auth,
    employees,
    departments,
    shifts,
    handovers,
    schedules,
    tasks,
    audit
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(employees.router, prefix="/employees", tags=["Employees"])
api_router.include_router(departments.router, prefix="/departments", tags=["Departments"])
api_router.include_router(shifts.router, prefix="/shifts", tags=["Shifts"])
api_router.include_router(handovers.router, prefix="/handovers", tags=["Handovers"])
api_router.include_router(schedules.router, prefix="/schedules", tags=["Schedules"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["Tasks"])
api_router.include_router(audit.router, prefix="/audit", tags=["Audit"])
