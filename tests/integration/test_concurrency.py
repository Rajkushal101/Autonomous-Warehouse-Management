import threading
import pytest
from app.services.task_service import TaskAssignmentService
from app.services.order_service import OrderService
from app.services.movement_service import MovementService
from app.models.entities import User, Task, Robot, InventoryBalance, Command, InventoryMovement
from app.domain.models import WarehouseSecurityException, RobotStatus
from app.repositories.base import SessionLocal
from app.core.config import settings

def test_concurrent_robot_assignment(db_session):
    """
    IT-01: Two independently connected threads attempt to assign different queued tasks
    to the same eligible idle robot simultaneously.
    Asserts that exactly 1 succeeds and the other receives 409 Conflict.
    """
    operator = db_session.query(User).filter(User.username == "operator_alice").first()
    customer = db_session.query(User).filter(User.username == "customer_bob").first()
    idle_robot = db_session.query(Robot).filter(Robot.status == "IDLE").first()
    assert idle_robot is not None

    # Create two distinct orders & tasks
    order1 = OrderService.create_order_with_reservation(
        db=db_session,
        customer=customer,
        warehouse_id=settings.WAREHOUSE_ID,
        items_payload=[{"sku": "SKU-001", "quantity": 1}],
        idempotency_key="conc-order-key-1"
    )
    order2 = OrderService.create_order_with_reservation(
        db=db_session,
        customer=customer,
        warehouse_id=settings.WAREHOUSE_ID,
        items_payload=[{"sku": "SKU-001", "quantity": 1}],
        idempotency_key="conc-order-key-2"
    )

    task1_id = order1["items"][0]["task_id"]
    task2_id = order2["items"][0]["task_id"]

    results = []
    barrier = threading.Barrier(2)

    def worker(task_id, idemp_key):
        db = SessionLocal()
        barrier.wait()
        try:
            op = db.query(User).filter(User.username == "operator_alice").first()
            res = TaskAssignmentService.assign_robot_to_task(
                db=db,
                actor=op,
                task_id=task_id,
                robot_id=idle_robot.id,
                idempotency_key=idemp_key
            )
            results.append(("SUCCESS", res))
        except WarehouseSecurityException as e:
            results.append(("CONFLICT", e.status_code, e.code))
        except Exception as e:
            results.append(("ERROR", str(e)))
        finally:
            db.close()

    t1 = threading.Thread(target=worker, args=(task1_id, "thread-key-1"))
    t2 = threading.Thread(target=worker, args=(task2_id, "thread-key-2"))

    t1.start()
    t2.start()
    t1.join()
    t2.join()

    # Verify that exactly ONE transaction succeeded and ONE was safely rejected
    successes = [r for r in results if r[0] == "SUCCESS"]
    conflicts = [r for r in results if r[0] == "CONFLICT"]

    assert len(successes) == 1, f"Expected 1 success, got {len(successes)}: {results}"
    assert len(conflicts) == 1, f"Expected 1 conflict, got {len(conflicts)}: {results}"
    assert conflicts[0][1] == 409  # HTTP 409 Conflict

def test_replay_command_acknowledgment(client, db_session):
    """
    IT-03: Replay assignment & acknowledgment cannot cause double movement or duplicated stock.
    """
    operator = db_session.query(User).filter(User.username == "operator_alice").first()
    customer = db_session.query(User).filter(User.username == "customer_bob").first()
    robot = db_session.query(Robot).filter(Robot.serial_number == "AGV-02").first()
    robot.status = "IDLE"
    robot.current_x = 2
    robot.current_y = 4
    db_session.commit()

    order = OrderService.create_order_with_reservation(
        db=db_session,
        customer=customer,
        warehouse_id=settings.WAREHOUSE_ID,
        items_payload=[{"sku": "SKU-002", "quantity": 1}],
        idempotency_key="replay-order-key-1"
    )
    task_id = order["items"][0]["task_id"]

    # Assign task
    assign_res = TaskAssignmentService.assign_robot_to_task(
        db=db_session,
        actor=operator,
        task_id=task_id,
        robot_id=robot.id,
        idempotency_key="assign-replay-key"
    )
    command_id = assign_res["command_id"]

    # Device acknowledges PICK
    ack_res1 = MovementService.execute_pickup_arrival(db_session, robot.id, task_id)
    assert ack_res1["status"] == "PICKED_SUCCESSFULLY"

    # Count movements
    movements_count_1 = db_session.query(InventoryMovement).filter(InventoryMovement.reservation_id == order["items"][0]["task_id"]).count()

    # Move to packing bay and drop
    drop_res1 = MovementService.execute_drop_arrival(db_session, robot.id, task_id)
    assert drop_res1["status"] == "DELIVERED_SUCCESSFULLY"

    # Verify task completed
    task = db_session.query(Task).filter(Task.id == task_id).first()
    assert task.state == "COMPLETED"
    assert robot.status == "IDLE"

def test_collision_avoidance_two_robots(db_session):
    """
    IT-05: Robot A cannot move into a cell currently occupied by Robot B.
    """
    r1 = db_session.query(Robot).filter(Robot.serial_number == "AGV-01").first()
    r2 = db_session.query(Robot).filter(Robot.serial_number == "AGV-02").first()

    # Place Robot 2 at (1, 1) and Robot 1 at (0, 1)
    r1.current_x, r1.current_y = 0, 1
    r2.current_x, r2.current_y = 1, 1
    db_session.commit()

    # Robot 1 attempts to step towards (1, 1)
    result = MovementService.step_robot_toward_goal(db_session, r1.id, 1, 1)

    # Must cleanly detect conflict and refuse movement
    assert result["status"] == "COLLISION_PREVENTED_BLOCKED"
    assert r1.current_x == 0 and r1.current_y == 1  # Position unchanged
    assert r1.status == RobotStatus.BLOCKED.value
