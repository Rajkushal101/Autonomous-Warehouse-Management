from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.repositories.base import get_db
from app.models.entities import Robot, Task, Order, InventoryBalance
from app.core.security import get_utc_now

router = APIRouter(tags=["Health & Telemetry"])

@router.get("/health/live")
def liveness_probe():
    return {"status": "LIVE", "timestamp": get_utc_now().isoformat()}

@router.get("/health/ready")
def readiness_probe(db: Session = Depends(get_db)):
    try:
        # Check DB connectivity
        db.execute(text("SELECT 1"))
        return {"status": "READY", "database": "CONNECTED", "timestamp": get_utc_now().isoformat()}
    except Exception as e:
        return {"status": "UNHEALTHY", "database": "FAILED", "error": str(e)}

@router.get("/metrics")
def get_operational_metrics(db: Session = Depends(get_db)):
    """Provides Phase 15 telemetry metrics & alerts."""
    total_robots = db.query(Robot).count()
    idle_robots = db.query(Robot).filter(Robot.status == "IDLE").count()
    busy_robots = db.query(Robot).filter(Robot.status == "BUSY").count()
    blocked_robots = db.query(Robot).filter(Robot.status == "BLOCKED").count()
    offline_robots = db.query(Robot).filter(Robot.status == "OFFLINE").count()

    queued_tasks = db.query(Task).filter(Task.state == "QUEUED").count()
    completed_tasks = db.query(Task).filter(Task.state == "COMPLETED").count()
    fulfilled_orders = db.query(Order).filter(Order.status == "FULFILLED").count()

    return {
        "fleet": {
            "total": total_robots,
            "idle": idle_robots,
            "busy": busy_robots,
            "blocked": blocked_robots,
            "offline": offline_robots
        },
        "fulfillment": {
            "queued_tasks": queued_tasks,
            "completed_tasks": completed_tasks,
            "fulfilled_orders": fulfilled_orders
        },
        "system": {
            "status": "HEALTHY",
            "timestamp": get_utc_now().isoformat()
        }
    }
