import time
import logging
from sqlalchemy.orm import Session
from app.repositories.base import SessionLocal
from app.models.entities import Task, Robot, WarehouseControl, Command
from app.domain.models import TaskState, RobotStatus, CommandStatus
from app.services.task_service import TaskAssignmentService
from app.services.movement_service import MovementService
from app.core.config import settings

logger = logging.getLogger("warehouse_dispatcher")
logging.basicConfig(level=logging.INFO)

def run_single_tick(db: Session, warehouse_id: str = settings.WAREHOUSE_ID) -> dict:
    """
    Executes one discrete simulation tick:
    1. Checks if warehouse is paused.
    2. Polls queued tasks and assigns available idle robots.
    3. For busy robots with active tasks, advances one step towards pickup or packing bay.
    """
    wh_control = db.query(WarehouseControl).filter(
        WarehouseControl.warehouse_id == warehouse_id
    ).first()

    if wh_control and wh_control.paused:
        return {"status": "PAUSED"}

    # 1. Advance movement for BUSY robots
    busy_robots = db.query(Robot).filter(
        Robot.warehouse_id == warehouse_id,
        Robot.status == RobotStatus.BUSY.value
    ).all()

    moves_executed = 0
    for robot in busy_robots:
        active_task = db.query(Task).filter(
            Task.robot_id == robot.id,
            Task.state.in_([TaskState.ASSIGNED.value, TaskState.TO_PICKUP.value, TaskState.TO_DROP.value])
        ).first()

        if not active_task:
            continue

        # Target goal coordinates
        if active_task.state in [TaskState.ASSIGNED.value, TaskState.TO_PICKUP.value]:
            target_loc = active_task.pickup_location
            goal_x, goal_y = target_loc.x, target_loc.y

            if (robot.current_x, robot.current_y) == (goal_x, goal_y):
                # Arrived at pickup: execute pickup
                MovementService.execute_pickup_arrival(db, robot.id, active_task.id)
            else:
                MovementService.step_robot_toward_goal(db, robot.id, goal_x, goal_y)
                moves_executed += 1

        elif active_task.state == TaskState.TO_DROP.value:
            target_loc = active_task.drop_location
            goal_x, goal_y = target_loc.x, target_loc.y

            if (robot.current_x, robot.current_y) == (goal_x, goal_y):
                # Arrived at packing: execute drop
                MovementService.execute_drop_arrival(db, robot.id, active_task.id)
            else:
                MovementService.step_robot_toward_goal(db, robot.id, goal_x, goal_y)
                moves_executed += 1

    return {"status": "TICK_COMPLETED", "moves": moves_executed}

def run_worker_loop():
    logger.info("Starting Autonomous Warehouse Dispatcher Worker...")
    while True:
        db = SessionLocal()
        try:
            run_single_tick(db)
        except Exception as e:
            logger.error(f"Error in dispatcher loop: {e}")
        finally:
            db.close()
        time.sleep(settings.SIMULATOR_TICK_RATE_MS / 1000.0)

if __name__ == "__main__":
    run_worker_loop()
