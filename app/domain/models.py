from enum import Enum
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from datetime import datetime

class Role(str, Enum):
    CUSTOMER = "CUSTOMER"
    OPERATOR = "OPERATOR"
    MANAGER = "MANAGER"
    ADMIN = "ADMIN"
    AUDITOR = "AUDITOR"

class TaskState(str, Enum):
    QUEUED = "QUEUED"
    ASSIGNED = "ASSIGNED"
    TO_PICKUP = "TO_PICKUP"
    PICKING = "PICKING"
    TO_DROP = "TO_DROP"
    DROPPING = "DROPPING"
    COMPLETED = "COMPLETED"
    BLOCKED = "BLOCKED"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"

class RobotStatus(str, Enum):
    IDLE = "IDLE"
    BUSY = "BUSY"
    BLOCKED = "BLOCKED"
    OFFLINE = "OFFLINE"
    MAINTENANCE = "MAINTENANCE"

class OrderStatus(str, Enum):
    CREATED = "CREATED"
    RESERVED = "RESERVED"
    IN_PROGRESS = "IN_PROGRESS"
    FULFILLED = "FULFILLED"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"

class LocationType(str, Enum):
    STORAGE = "STORAGE"
    PACKING = "PACKING"
    CHARGING = "CHARGING"
    TRANSIT = "TRANSIT"

class MovementType(str, Enum):
    PICK = "PICK"
    DROP = "DROP"
    ADJUSTMENT = "ADJUSTMENT"
    RETURN = "RETURN"

class CommandType(str, Enum):
    MOVE_TO_STEP = "MOVE_TO_STEP"
    PICK_AT_LOCATION = "PICK_AT_LOCATION"
    DROP_AT_PACKING = "DROP_AT_PACKING"
    EMERGENCY_STOP = "EMERGENCY_STOP"

class CommandStatus(str, Enum):
    PENDING = "PENDING"
    CLAIMED = "CLAIMED"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    FAILED = "FAILED"

class AuditOutcome(str, Enum):
    SUCCESS = "SUCCESS"
    DENIED = "DENIED"
    FAILED = "FAILED"

# Domain Exceptions
class WarehouseSecurityException(Exception):
    def __init__(self, message: str, code: str = "SECURITY_VIOLATION", status_code: int = 403):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code

class InsufficientStockException(WarehouseSecurityException):
    def __init__(self, message: str = "Insufficient available stock"):
        super().__init__(message, code="INSUFFICIENT_STOCK", status_code=409)

class ConcurrencyConflictException(WarehouseSecurityException):
    def __init__(self, message: str = "Resource locked or state conflict"):
        super().__init__(message, code="CONCURRENCY_CONFLICT", status_code=409)

class EntityNotFoundException(WarehouseSecurityException):
    def __init__(self, message: str = "Requested resource not found"):
        super().__init__(message, code="NOT_FOUND", status_code=404)

class ValidationException(WarehouseSecurityException):
    def __init__(self, message: str = "Invalid input data"):
        super().__init__(message, code="VALIDATION_ERROR", status_code=422)

class UnauthorizedException(WarehouseSecurityException):
    def __init__(self, message: str = "Authentication required"):
        super().__init__(message, code="UNAUTHORIZED", status_code=401)
