from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.repositories.base import get_db
from app.models.entities import Robot, Command
from app.api.deps import get_current_robot
from app.services.movement_service import MovementService
from app.core.security import get_utc_now
from app.domain.models import CommandStatus

router = APIRouter(prefix="/device", tags=["Robot Device Telemetry"])

class HeartbeatRequest(BaseModel):
    battery_pct: int = Field(..., ge=0, le=100)
    current_x: int = Field(..., ge=0, le=20)
    current_y: int = Field(..., ge=0, le=20)

class StepMoveRequest(BaseModel):
    goal_x: int
    goal_y: int

class CommandAckRequest(BaseModel):
    command_id: str
    action_type: str  # PICK or DROP
    task_id: str

@router.post("/heartbeat")
def record_heartbeat(req: HeartbeatRequest, robot: Robot = Depends(get_current_robot), db: Session = Depends(get_db)):
    robot.last_seen = get_utc_now()
    robot.battery_pct = req.battery_pct
    robot.current_x = req.current_x
    robot.current_y = req.current_y
    db.commit()
    return {"status": "ACK", "serial": robot.serial_number}

@router.get("/commands")
def poll_pending_commands(robot: Robot = Depends(get_current_robot), db: Session = Depends(get_db)):
    commands = db.query(Command).filter(
        Command.robot_id == robot.id,
        Command.status == CommandStatus.PENDING.value
    ).order_by(Command.sequence_number.asc()).all()

    return [{
        "command_id": c.id,
        "sequence_number": c.sequence_number,
        "type": c.command_type,
        "expected_state": c.expected_state,
        "payload": c.payload_json
    } for c in commands]

@router.post("/commands/ack")
def acknowledge_command(req: CommandAckRequest, robot: Robot = Depends(get_current_robot), db: Session = Depends(get_db)):
    cmd = db.query(Command).filter(Command.id == req.command_id, Command.robot_id == robot.id).first()
    if not cmd:
        raise HTTPException(status_code=404, detail="Command not found or does not belong to this robot")

    if cmd.status == CommandStatus.ACKNOWLEDGED.value:
        return {"status": "ALREADY_ACKNOWLEDGED"}

    if req.action_type == "PICK":
        result = MovementService.execute_pickup_arrival(db, robot.id, req.task_id)
    elif req.action_type == "DROP":
        result = MovementService.execute_drop_arrival(db, robot.id, req.task_id)
    else:
        raise HTTPException(status_code=422, detail="Invalid action type")

    cmd.status = CommandStatus.ACKNOWLEDGED.value
    db.commit()
    return {"status": "SUCCESS", "details": result}
