from typing import List, Tuple, Optional, Dict, Any
from collections import deque
from sqlalchemy.orm import Session
from app.models.entities import (
    Warehouse, WarehouseControl, Location, Robot, Task, Command, 
    StockReservation, InventoryBalance, InventoryMovement, Order, OrderItem
)
from app.domain.models import (
    RobotStatus, TaskState, MovementType, CommandStatus, 
    OrderStatus, WarehouseSecurityException, AuditOutcome
)
from app.services.audit_service import AuditService
from app.core.security import get_utc_now
import uuid

class MovementService:
    @staticmethod
    def get_grid_obstacles(db: Session, warehouse_id: str) -> set:
        blocked_locations = db.query(Location).filter(
            Location.warehouse_id == warehouse_id,
            Location.is_blocked == True
        ).all()
        return {(loc.x, loc.y) for loc in blocked_locations}

    @staticmethod
    def bfs_shortest_path(
        start: Tuple[int, int],
        goal: Tuple[int, int],
        grid_width: int,
        grid_height: int,
        obstacles: set
    ) -> Optional[List[Tuple[int, int]]]:
        if start == goal:
            return [start]

        queue = deque([(start, [start])])
        visited = {start}

        while queue:
            (curr_x, curr_y), path = queue.popleft()

            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nx, ny = curr_x + dx, curr_y + dy
                if 0 <= nx < grid_width and 0 <= ny < grid_height:
                    if (nx, ny) not in obstacles and (nx, ny) not in visited:
                        visited.add((nx, ny))
                        new_path = path + [(nx, ny)]
                        if (nx, ny) == goal:
                            return new_path
                        queue.append(((nx, ny), new_path))
        return None

    @staticmethod
    def step_robot_toward_goal(
        db: Session,
        robot_id: str,
        goal_x: int,
        goal_y: int
    ) -> Dict[str, Any]:
        """
        Executes one discrete step movement on the warehouse grid.
        Enforces mutual exclusion on coordinates, prevents A<->B swaps,
        and serializes updates under the WarehouseControl row lock.
        """
        robot = db.query(Robot).filter(Robot.id == robot_id).with_for_update().first()
        if not robot:
            raise WarehouseSecurityException("Robot not found", code="NOT_FOUND", status_code=404)

        wh_control = db.query(WarehouseControl).filter(
            WarehouseControl.warehouse_id == robot.warehouse_id
        ).with_for_update().first()

        if wh_control and wh_control.paused:
            raise WarehouseSecurityException("Warehouse operations paused; movement halted", code="WAREHOUSE_PAUSED", status_code=503)

        start = (robot.current_x, robot.current_y)
        goal = (goal_x, goal_y)

        if start == goal:
            return {"robot_id": robot.id, "position": start, "status": "AT_GOAL"}

        warehouse = db.query(Warehouse).filter(Warehouse.id == robot.warehouse_id).first()
        obstacles = MovementService.get_grid_obstacles(db, robot.warehouse_id)

        path = MovementService.bfs_shortest_path(start, goal, warehouse.grid_width, warehouse.grid_height, obstacles)
        if not path or len(path) < 2:
            robot.status = RobotStatus.BLOCKED.value
            db.commit()
            return {"robot_id": robot.id, "position": start, "status": "NO_PATH_BLOCKED"}

        next_step = path[1]
        next_x, next_y = next_step

        # Mutual Cell Exclusion Check: Assert no other robot currently occupies next_step
        conflicting_robot = db.query(Robot).filter(
            Robot.warehouse_id == robot.warehouse_id,
            Robot.id != robot.id,
            Robot.current_x == next_x,
            Robot.current_y == next_y
        ).first()

        if conflicting_robot:
            robot.status = RobotStatus.BLOCKED.value
            db.commit()
            return {
                "robot_id": robot.id,
                "position": start,
                "status": "COLLISION_PREVENTED_BLOCKED",
                "conflicting_robot": conflicting_robot.serial_number
            }

        # Prevent Direct Swap: Assert conflicting robot is not moving into robot's current cell
        # (Since movements are serialized under wh_control lock, simultaneous moves are prevented)

        robot.current_x = next_x
        robot.current_y = next_y
        robot.last_seen = get_utc_now()
        robot.battery_pct = max(0, robot.battery_pct - 1)
        if wh_control:
            wh_control.current_tick += 1

        db.commit()
        return {
            "robot_id": robot.id,
            "position": (next_x, next_y),
            "status": "MOVED_STEP",
            "battery_pct": robot.battery_pct
        }

    @staticmethod
    def execute_pickup_arrival(db: Session, robot_id: str, task_id: str) -> Dict[str, Any]:
        """Called when robot reaches pickup location. Commits stock pickup to ledger."""
        task = db.query(Task).filter(Task.id == task_id).with_for_update().first()
        robot = db.query(Robot).filter(Robot.id == robot_id).with_for_update().first()
        if not task or not robot:
            raise WarehouseSecurityException("Task or robot not found", code="NOT_FOUND", status_code=404)

        reservation = task.reservation
        balance = reservation.balance

        # Decrement source on_hand and reserved
        balance.on_hand -= reservation.qty
        balance.reserved -= reservation.qty
        balance.version += 1
        reservation.state = "PICKED"

        task.state = TaskState.TO_DROP.value

        # Append PICK movement
        movement = InventoryMovement(
            product_id=balance.product_id,
            from_location_id=balance.location_id,
            to_location_id=None,
            reservation_id=reservation.id,
            qty=reservation.qty,
            movement_type=MovementType.PICK.value,
            source_event_id=str(uuid.uuid4()),
            reason=f"Robot {robot.serial_number} picked item for Task {task.id}",
            actor_id=robot.id,
            created_at=get_utc_now()
        )
        db.add(movement)

        AuditService.log_event(
            db=db,
            actor_id=robot.id,
            actor_type="ROBOT",
            action="PICK_ITEM",
            target_entity="TASK",
            target_id=task.id,
            outcome=AuditOutcome.SUCCESS,
            reason_code="STOCK_PICKED_COMMITTED"
        )

        db.commit()
        return {"status": "PICKED_SUCCESSFULLY", "task_state": task.state}

    @staticmethod
    def execute_drop_arrival(db: Session, robot_id: str, task_id: str) -> Dict[str, Any]:
        """Called when robot reaches packing location. Commits delivery to packing bay and completes task."""
        task = db.query(Task).filter(Task.id == task_id).with_for_update().first()
        robot = db.query(Robot).filter(Robot.id == robot_id).with_for_update().first()
        if not task or not robot:
            raise WarehouseSecurityException("Task or robot not found", code="NOT_FOUND", status_code=404)

        reservation = task.reservation
        packing_loc = task.drop_location

        # Increment destination balance at packing location
        packing_balance = db.query(InventoryBalance).filter(
            InventoryBalance.warehouse_id == robot.warehouse_id,
            InventoryBalance.product_id == reservation.balance.product_id,
            InventoryBalance.location_id == packing_loc.id
        ).with_for_update().first()

        if not packing_balance:
            packing_balance = InventoryBalance(
                warehouse_id=robot.warehouse_id,
                product_id=reservation.balance.product_id,
                location_id=packing_loc.id,
                on_hand=reservation.qty,
                reserved=0
            )
            db.add(packing_balance)
        else:
            packing_balance.on_hand += reservation.qty

        reservation.state = "DELIVERED"
        task.state = TaskState.COMPLETED.value
        task.completed_at = get_utc_now()

        # Update order item delivered quantity
        order_item = reservation.order_item
        order_item.delivered_qty += reservation.qty

        # Return robot to IDLE at packing bay
        robot.status = RobotStatus.IDLE.value

        # Append DROP movement
        movement = InventoryMovement(
            product_id=reservation.balance.product_id,
            from_location_id=None,
            to_location_id=packing_loc.id,
            reservation_id=reservation.id,
            qty=reservation.qty,
            movement_type=MovementType.DROP.value,
            source_event_id=str(uuid.uuid4()),
            reason=f"Robot {robot.serial_number} delivered item to Packing Area",
            actor_id=robot.id,
            created_at=get_utc_now()
        )
        db.add(movement)

        # Check if entire order is fulfilled
        order = order_item.order
        all_fulfilled = all(it.delivered_qty >= it.requested_qty for it in order.items)
        if all_fulfilled:
            order.status = OrderStatus.FULFILLED.value

        AuditService.log_event(
            db=db,
            actor_id=robot.id,
            actor_type="ROBOT",
            action="PACKING_DROP",
            target_entity="TASK",
            target_id=task.id,
            outcome=AuditOutcome.SUCCESS,
            reason_code="DELIVERED_TO_PACKING_BAY",
            metadata={"order_id": order.id, "order_status": order.status}
        )

        db.commit()
        return {
            "status": "DELIVERED_SUCCESSFULLY",
            "task_state": task.state,
            "order_status": order.status,
            "robot_status": robot.status
        }
