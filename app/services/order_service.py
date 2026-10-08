import json
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.entities import (
    User, Order, OrderItem, InventoryBalance, StockReservation, 
    Task, Location, Product, IdempotencyRecord, WarehouseControl
)
from app.domain.models import Role, OrderStatus, TaskState, WarehouseSecurityException, AuditOutcome
from app.services.policy import AccessPolicy
from app.services.audit_service import AuditService
from app.core.security import hash_request_payload, get_utc_now
import uuid

class OrderService:
    @staticmethod
    def create_order_with_reservation(
        db: Session,
        customer: User,
        warehouse_id: str,
        items_payload: List[Dict[str, Any]],
        idempotency_key: str
    ) -> Dict[str, Any]:
        AccessPolicy.require_role(customer, [Role.CUSTOMER, Role.ADMIN], db=db, action_name="CREATE_ORDER")

        if not items_payload:
            raise WarehouseSecurityException("Order must contain at least one item", code="EMPTY_ORDER", status_code=422)

        if not idempotency_key:
            raise WarehouseSecurityException("Idempotency-Key header is mandatory", code="MISSING_IDEMPOTENCY_KEY", status_code=422)

        # Validate warehouse status
        wh_control = db.query(WarehouseControl).filter(WarehouseControl.warehouse_id == warehouse_id).first()
        if wh_control and wh_control.paused:
            raise WarehouseSecurityException("Warehouse operations are currently paused", code="WAREHOUSE_PAUSED", status_code=503)

        payload_str = json.dumps(items_payload, sort_keys=True)
        request_hash = hash_request_payload(payload_str)

        # 1. Idempotency Check
        idemp_rec = db.query(IdempotencyRecord).filter(
            IdempotencyRecord.actor_id == customer.id,
            IdempotencyRecord.endpoint == "/orders",
            IdempotencyRecord.idempotency_key == idempotency_key
        ).first()

        if idemp_rec:
            if idemp_rec.request_hash != request_hash:
                raise WarehouseSecurityException("Idempotency key reused with differing parameters", code="IDEMPOTENCY_CONFLICT", status_code=409)
            if idemp_rec.response_body:
                return json.loads(idemp_rec.response_body)

        # 2. Extract & Validate requested products
        requested_skus = []
        for it in items_payload:
            sku = it.get("sku")
            qty = it.get("quantity")
            if not sku or not isinstance(qty, int) or qty <= 0 or qty > 100:
                raise WarehouseSecurityException("Each item requires a valid SKU and quantity (1..100)", code="INVALID_QUANTITY", status_code=422)
            requested_skus.append((sku, qty))

        # 3. Deterministic balance row locking (sorted by product SKU to prevent deadlocks)
        requested_skus.sort(key=lambda x: x[0])

        locked_balances = []
        for sku, qty in requested_skus:
            product = db.query(Product).filter(Product.sku == sku, Product.is_active == True).first()
            if not product:
                raise WarehouseSecurityException(f"Product '{sku}' not available", code="PRODUCT_NOT_FOUND", status_code=404)

            # Find storage location balance
            balance = db.query(InventoryBalance).join(Location).filter(
                InventoryBalance.warehouse_id == warehouse_id,
                InventoryBalance.product_id == product.id,
                Location.type == "STORAGE"
            ).with_for_update().first()

            if not balance:
                raise WarehouseSecurityException(f"No storage balance found for '{sku}'", code="INSUFFICIENT_STOCK", status_code=409)

            available = balance.on_hand - balance.reserved
            if available < qty:
                raise WarehouseSecurityException(
                    f"Insufficient stock for '{sku}': requested {qty}, available {available}",
                    code="INSUFFICIENT_STOCK",
                    status_code=409
                )
            locked_balances.append((product, balance, qty))

        # Find Packing Location
        packing_loc = db.query(Location).filter(
            Location.warehouse_id == warehouse_id,
            Location.type == "PACKING"
        ).first()
        if not packing_loc:
            raise WarehouseSecurityException("Warehouse has no configured packing location", code="PACKING_LOC_MISSING", status_code=500)

        # 4. Atomic Creation of Order, Items, Reservations, and Queued Tasks
        new_order = Order(
            customer_id=customer.id,
            warehouse_id=warehouse_id,
            status=OrderStatus.RESERVED.value,
            version=1
        )
        db.add(new_order)
        db.flush()

        created_items = []
        for product, balance, qty in locked_balances:
            # Increment reserved quantity
            balance.reserved += qty
            balance.version += 1

            order_item = OrderItem(
                order_id=new_order.id,
                product_id=product.id,
                requested_qty=qty,
                delivered_qty=0
            )
            db.add(order_item)
            db.flush()

            reservation = StockReservation(
                order_item_id=order_item.id,
                balance_id=balance.id,
                qty=qty,
                state="RESERVED"
            )
            db.add(reservation)
            db.flush()

            # Create Task in QUEUED state
            task_id = str(uuid.uuid4())
            task = Task(
                id=task_id,
                reservation_id=reservation.id,
                robot_id=None,
                pickup_location_id=balance.location_id,
                drop_location_id=packing_loc.id,
                state=TaskState.QUEUED.value,
                quantity=qty,
                attempt=1
            )
            db.add(task)
            db.flush()
            created_items.append({"sku": product.sku, "quantity": qty, "task_id": task.id})

        # Save Idempotency Record
        response_data = {
            "order_id": new_order.id,
            "status": new_order.status,
            "items": created_items,
            "created_at": new_order.created_at.isoformat()
        }

        idemp_record = IdempotencyRecord(
            actor_id=customer.id,
            endpoint="/orders",
            idempotency_key=idempotency_key,
            request_hash=request_hash,
            response_status=201,
            response_body=json.dumps(response_data)
        )
        db.add(idemp_record)

        AuditService.log_event(
            db=db,
            actor_id=customer.id,
            actor_type="USER",
            action="ORDER_CREATE",
            target_entity="ORDER",
            target_id=new_order.id,
            outcome=AuditOutcome.SUCCESS,
            reason_code="ORDER_AND_RESERVATIONS_COMMITTED",
            metadata={"items": created_items, "order_id": new_order.id}
        )

        db.commit()
        return response_data

    @staticmethod
    def get_order_by_id(db: Session, customer: User, order_id: str) -> Dict[str, Any]:
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise WarehouseSecurityException("Order not found", code="NOT_FOUND", status_code=404)

        AccessPolicy.require_ownership_or_manager(customer, order.customer_id, db=db, action_name="VIEW_ORDER")

        items_info = []
        for it in order.items:
            res = it.reservations[0] if it.reservations else None
            task = res.task if res else None
            items_info.append({
                "sku": it.product.sku,
                "product_name": it.product.name,
                "requested_qty": it.requested_qty,
                "delivered_qty": it.delivered_qty,
                "task_state": task.state if task else "NONE",
                "assigned_robot": task.robot.serial_number if task and task.robot else None
            })

        return {
            "order_id": order.id,
            "status": order.status,
            "customer_id": order.customer_id,
            "created_at": order.created_at.isoformat(),
            "items": items_info
        }

    @staticmethod
    def list_customer_orders(db: Session, customer: User) -> List[Dict[str, Any]]:
        query = db.query(Order)
        if customer.role not in [Role.MANAGER.value, Role.ADMIN.value]:
            query = query.filter(Order.customer_id == customer.id)
        orders = query.order_by(Order.created_at.desc()).all()
        return [{
            "order_id": o.id,
            "status": o.status,
            "created_at": o.created_at.isoformat(),
            "item_count": len(o.items)
        } for o in orders]
