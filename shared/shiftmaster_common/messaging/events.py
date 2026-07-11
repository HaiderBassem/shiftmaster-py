"""
Pydantic schemas for event-driven asynchronous communication.
"""

from pydantic import BaseModel, ConfigDict, Field
from typing import Any, Optional
from uuid import UUID
from datetime import datetime

class BaseEvent(BaseModel):
    """Base schema for all events."""
    event_id: UUID = Field(..., description="Unique ID for this specific event occurrence (used for idempotency)")
    correlation_id: Optional[str] = Field(None, description="Correlation ID for tracing")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(populate_by_name=True)

class AuditLogEvent(BaseEvent):
    """Event triggered when an auditable action occurs."""
    employee_id: Optional[UUID] = None
    action: str
    table_name: str
    record_id: Optional[UUID] = None
    old_data: Optional[dict[str, Any]] = None
    new_data: Optional[dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

class NotificationEvent(BaseEvent):
    """Event triggered to send a notification."""
    recipient_id: UUID
    sender_id: Optional[UUID] = None
    title: str
    message: str
    type: str
    reference_id: Optional[UUID] = None
    reference_type: Optional[str] = None

class EmployeeCreatedEvent(BaseEvent):
    """Event triggered when a new employee is created."""
    employee_id: UUID
    first_name: str
    last_name: str
    department_id: Optional[UUID] = None
    default_shift_id: Optional[UUID] = None
    status: str

class EmployeeUpdatedEvent(BaseEvent):
    """Event triggered when an employee is updated."""
    employee_id: UUID
    first_name: str
    last_name: str
    department_id: Optional[UUID] = None
    default_shift_id: Optional[UUID] = None
    status: str
