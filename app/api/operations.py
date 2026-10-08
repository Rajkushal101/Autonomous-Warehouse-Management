from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.repositories.base import get_db
from app.models.entities import User, Task, Robot, WarehouseControl, Location
from app.api.deps import get_current_user
from app.services.task_service import TaskAssignmentService
from app.services.policy import AccessPolicy
from app.domain.models import Role, WarehouseSecurityException, AuditOutcome
from app.services.audit_service import AuditService
from app.core.config import settings

router = APIRouter(prefix="/operations", tags=["Operations"])

class AssignTaskRequest(BaseModel):
    task_id: str
    robot_id: str

class PauseRequest(BaseModel):
    reason: str = Field(..., min_length=3, max_length=255)

@router.post("/tasks/assign")
def assign_task(
    req: AssignTaskRequest,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not idempotency_key:
        raise WarehouseSecurityException("Header 'Idempotency-Key' is required", code="MISSING_IDEMPOTENCY_KEY", status_code=422)

    return TaskAssignmentService.assign_robot_to_task(
        db=db,
        actor=current_user,
        task_id=req.task_id,
        robot_id=req.robot_id,
        idempotency_key=idempotency_key
    )

@router.get("/fleet")
def get_fleet_status(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    AccessPolicy.require_role(current_user, [Role.OPERATOR, Role.MANAGER, Role.ADMIN], db=db, action_name="VIEW_FLEET")
    robots = db.query(Robot).filter(Robot.warehouse_id == settings.WAREHOUSE_ID).all()
    tasks = db.query(Task).all()
    wh_control = db.query(WarehouseControl).filter(WarehouseControl.warehouse_id == settings.WAREHOUSE_ID).first()

    return {
        "paused": wh_control.paused if wh_control else False,
        "robots": [{
            "id": r.id,
            "serial": r.serial_number,
            "status": r.status,
            "battery_pct": r.battery_pct,
            "position": (r.current_x, r.current_y),
            "last_seen": r.last_seen.isoformat()
        } for r in robots],
        "tasks": [{
            "id": t.id,
            "state": t.state,
            "robot_id": t.robot_id,
            "quantity": t.quantity
        } for t in tasks]
    }

@router.post("/pause")
def pause_operations(req: PauseRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    AccessPolicy.require_role(current_user, [Role.OPERATOR, Role.MANAGER, Role.ADMIN], db=db, action_name="PAUSE_WAREHOUSE")
    wh_control = db.query(WarehouseControl).filter(WarehouseControl.warehouse_id == settings.WAREHOUSE_ID).with_for_update().first()
    if wh_control:
        wh_control.paused = True
        wh_control.stop_reason = req.reason
        AuditService.log_event(
            db=db,
            actor_id=current_user.id,
            actor_type="USER",
            action="PAUSE_OPERATIONS",
            target_entity="WAREHOUSE",
            target_id=settings.WAREHOUSE_ID,
            outcome=AuditOutcome.SUCCESS,
            reason_code="EMERGENCY_PAUSE_TRIGGERED",
            metadata={"reason": req.reason}
        )
        db.commit()
    return {"status": "PAUSED", "reason": req.reason}

@router.post("/resume")
def resume_operations(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    AccessPolicy.require_role(current_user, [Role.OPERATOR, Role.MANAGER, Role.ADMIN], db=db, action_name="RESUME_WAREHOUSE")
    wh_control = db.query(WarehouseControl).filter(WarehouseControl.warehouse_id == settings.WAREHOUSE_ID).with_for_update().first()
    if wh_control:
        wh_control.paused = False
        wh_control.stop_reason = None
        AuditService.log_event(
            db=db,
            actor_id=current_user.id,
            actor_type="USER",
            action="RESUME_OPERATIONS",
            target_entity="WAREHOUSE",
            target_id=settings.WAREHOUSE_ID,
            outcome=AuditOutcome.SUCCESS,
            reason_code="OPERATIONS_RESUMED"
        )
        db.commit()
    return {"status": "ACTIVE"}
