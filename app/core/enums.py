from enum import StrEnum


class EmployeeRole(StrEnum):
    ADMIN = "admin"
    MANAGER = "manager"
    TEAM_LEADER = "team_leader"
    EMPLOYEE = "employee"


class EmployeeStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


class ShiftStatus(StrEnum):
    SCHEDULED = "scheduled"
    ON_LEAVE = "on_leave"
    OFF = "off"
    REPLACED = "replaced"


class LeaveStatus(StrEnum):
    PENDING = "pending"
    TL_APPROVED = "tl_approved"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class SwapStatus(StrEnum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    TL_APPROVED = "tl_approved"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class TaskStatus(StrEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ScheduleStatus(StrEnum):
    DRAFT = "draft"
    PUBLISHED = "published"
