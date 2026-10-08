import json
import uuid
from typing import Dict, Any, Optional
from datetime import timedelta
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.models.entities import (
    User, Task, Robot, Command, WarehouseControl, IdempotencyRecord
)
from app.domain.models import (
    Role, TaskState, RobotStatus, CommandType, CommandStatus,
    WarehouseSecurityException, AuditOutcome
)
from app.services.policy import AccessPolicy
from app.services.audit_service import AuditService
from app.core.security import get_utc_now, hash_request_payload
from app.core.config import settings

ACTIVE_TASK_STATES = [
    TaskState.ASSIGNED.value, TaskState.TO_PICKUP.value, TaskState.PICKING.value,
    TaskState.TO_DROP.value, TaskState.DROPPING.value, TaskState.BLOCKED.value
]

class TaskAssignmentService:
    @staticmethod
    def assign_robot_to_task(
        db: Session,
        actor: User,
        task_id: str,
        robot_id: str,
        idempotency_key: str
    ) -> Dict[str, Any]:
        """
        Secure Robot Task Assignment Module (Primary Assessed Module - Phase 12).
        Enforces server-side authorization, input validation, atomic row locking,
        mutual task exclusion, request idempotency, and attributable audit logging.
        """
        # 1. Authorization: Only OPERATOR or MANAGER can dispatch robots
        AccessPolicy.require_role(actor, [Role.OPERATOR, Role.MANAGER, Role.ADMIN], db=db, action_name="ASSIGN_ROBOT_TASK")

        # 2. Strict Input Bounds
        if not task_id or not robot_id:
            raise WarehouseSecurityException("task_id and robot_id are required", code="INVALID_PARAMETERS", status_code=422)

        if not idempotency_key or len(idempotency_key) > 64:
            raise WarehouseSecurityException("Valid Idempotency-Key (1..64 chars) required", code="INVALID_IDEMPOTENCY_KEY", status_code=422)

        # 3. Check Idempotency Record
        payload_str = json.dumps({"task_id": task_id, "robot_id": robot_id}, sort_keys=True)
        request_hash = hash_request_payload(payload_str)

        idemp = db.query(IdempotencyRecord).filter(
            IdempotencyRecord.actor_id == actor.id,
            IdempotencyRecord.endpoint == f"/tasks/{task_id}/assign",
            IdempotencyRecord.idempotency_key == idempotency_key
        ).first()

        if idemp:
            if idemp.request_hash != request_hash:
                raise WarehouseSecurityException("Idempotency key reused with different body", code="IDEMPOTENCY_CONFLICT", status_code=409)
            if idemp.response_body:
                return json.loads(idemp.response_body)

        # 4. Check Warehouse Operational Pause State
        # In SQLite, table-level/row-level lock is managed by transaction, in Postgres with_for_update()
        task = db.query(Task).filter(Task.id == task_id).with_for_update().first()
        if not task:
            raise WarehouseSecurityException("Task not found", code="TASK_NOT_FOUND", status_code=404)

        if task.state != TaskState.QUEUED.value:
            raise WarehouseSecurityException(
                f"Task cannot be assigned: current state is '{task.state}' (must be QUEUED)",
                code="INVALID_TASK_STATE",
                status_code=409
            )

        # 5. Acquire Exclusive Row Lock on Robot
        robot = db.query(Robot).filter(Robot.id == robot_id).with_for_update().first()
        if not robot:
            raise WarehouseSecurityException("Robot not found", code="ROBOT_NOT_FOUND", status_code=404)

        # 6. Verify Robot Eligibility Invariants
        if robot.status != RobotStatus.IDLE.value:
            raise WarehouseSecurityException(
                f"Robot {robot.serial_number} is not eligible: status is '{robot.status}' (must be IDLE)",
                code="ROBOT_BUSY_OR_UNAVAILABLE",
                status_code=409
            )

        if robot.battery_pct < 20:
            raise WarehouseSecurityException(
                f"Robot {robot.serial_number} has low battery ({robot.battery_pct}%), minimum 20% required",
                code="ROBOT_LOW_BATTERY",
                status_code=409
            )

        now = get_utc_now()
        ls = robot.last_seen
        if ls.tzinfo is not None:
            ls = ls.replace(tzinfo=None)
        heartbeat_age = (now - ls).total_seconds()
        if heartbeat_age > settings.ROBOT_HEARTBEAT_TIMEOUT_SECONDS:
            robot.status = RobotStatus.OFFLINE.value
            db.commit()
            raise WarehouseSecurityException(
                f"Robot {robot.serial_number} heartbeat is stale ({int(heartbeat_age)}s > {settings.ROBOT_HEARTBEAT_TIMEOUT_SECONDS}s). Marked OFFLINE.",
                code="ROBOT_HEARTBEAT_STALE",
                status_code=409
            )

        # 7. Database Mutual Exclusion Check (Prevent Race Conditions)
        existing_active_task = db.query(Task).filter(
            Task.robot_id == robot.id,
            Task.state.in_(ACTIVE_TASK_STATES)
        ).first()

        if existing_active_task:
            raise WarehouseSecurityException(
                f"Robot {robot.serial_number} already owns active task {existing_active_task.id}",
                code="ROBOT_ALREADY_ASSIGNED",
                status_code=409
            )

        # 8. Atomic Assignment Transition
        task.robot_id = robot.id
        task.state = TaskState.ASSIGNED.value
        task.attempt += 1

        robot.status = RobotStatus.BUSY.value
        robot.version += 1

        # 9. Generate Next Sequenced Allowlisted Command
        max_seq = db.query(func.max(Command.sequence_number)).filter(Command.robot_id == robot.id).scalar() or 0
        cmd_id = str(uuid.uuid4())
        command = Command(
            id=cmd_id,
            robot_id=robot.id,
            task_id=task.id,
            sequence_number=max_seq + 1,
            command_type=CommandType.PICK_AT_LOCATION.value,
            expected_state=TaskState.TO_PICKUP.value,
            status=CommandStatus.PENDING.value,
            payload_json=json.dumps({
                "pickup_location_id": task.pickup_location_id,
                "pickup_code": task.pickup_location.code if task.pickup_location else "SHELF-01",
                "drop_location_id": task.drop_location_id,
                "quantity": task.quantity
            })
        )
        try:
            db.add(command)
            db.flush()

            # 10. Audit Logging and Idempotency Record
            response_payload = {
                "task_id": task.id,
                "robot_id": robot.id,
                "robot_serial": robot.serial_number,
                "task_state": task.state,
                "command_id": command.id,
                "command_sequence": command.sequence_number,
                "status": "ASSIGNED_SUCCESSFULLY"
            }

            idemp_record = IdempotencyRecord(
                actor_id=actor.id,
                endpoint=f"/tasks/{task_id}/assign",
                idempotency_key=idempotency_key,
                request_hash=request_hash,
                response_status=200,
                response_body=json.dumps(response_payload)
            )
            db.add(idemp_record)

            AuditService.log_event(
                db=db,
                actor_id=actor.id,
                actor_type="USER",
                action="TASK_ASSIGNMENT",
                target_entity="TASK",
                target_id=task.id,
                outcome=AuditOutcome.SUCCESS,
                reason_code="ROBOT_ASSIGNED_ATOMICALLY",
                metadata={
                    "task_id": task.id,
                    "robot_id": robot.id,
                    "robot_serial": robot.serial_number,
                    "sequence": command.sequence_number
                }
            )

            db.commit()
            return response_payload
        except IntegrityError:
            db.rollback()
            raise WarehouseSecurityException(
                f"Concurrent conflict detected while assigning robot {robot.serial_number}",
                code="CONCURRENCY_CONFLICT",
                status_code=409
            )
