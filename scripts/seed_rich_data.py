import os
import sys
import uuid
import hashlib
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.repositories.base import SessionLocal, init_db
from app.models.entities import (
    User, Warehouse, Location, Product, InventoryBalance, Robot,
    Order, OrderItem, StockReservation, Task, Command, InventoryMovement, AuditEvent
)

def run_seed():
    print("Seeding rich database records...")
    init_db()
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc).replace(tzinfo=None)

        wh = db.query(Warehouse).first()
        if not wh:
            print("No warehouse found, running base seed first...")
            from scripts.seed_demo import seed
            seed()
            wh = db.query(Warehouse).first()

        customer = db.query(User).filter(User.username == "customer_bob").first()
        customer2 = db.query(User).filter(User.username == "customer_charlie").first()
        if not customer2:
            import bcrypt
            pwd_hash = bcrypt.hashpw(b"CustomerPass123!", bcrypt.gensalt()).decode()
            customer2 = User(
                id=str(uuid.uuid4()),
                username="customer_charlie",
                password_hash=pwd_hash,
                role="CUSTOMER",
                is_active=True
            )
            db.add(customer2)
            db.commit()

        operator = db.query(User).filter(User.username == "operator_alice").first()
        manager = db.query(User).filter(User.username == "manager_carol").first()
        auditor = db.query(User).filter(User.username == "auditor_eve").first()

        prod1 = db.query(Product).filter(Product.sku == "SKU-001").first()
        prod2 = db.query(Product).filter(Product.sku == "SKU-002").first()
        prod3 = db.query(Product).filter(Product.sku == "SKU-003").first()

        shelf1 = db.query(Location).filter(Location.code == "SHELF-01").first()
        shelf2 = db.query(Location).filter(Location.code == "SHELF-02").first()
        packing1 = db.query(Location).filter(Location.code == "PACKING-BAY-1").first()
        packing2 = db.query(Location).filter(Location.code == "PACKING-BAY-2").first()

        r1 = db.query(Robot).filter(Robot.serial_number == "AGV-01").first()
        r2 = db.query(Robot).filter(Robot.serial_number == "AGV-02").first()

        if r1:
            r1.current_x = 2
            r1.current_y = 4
            r1.battery_pct = 92
            r1.status = "BUSY"
            r1.last_seen = now
        if r2:
            r2.current_x = 0
            r2.current_y = 0
            r2.battery_pct = 85
            r2.status = "IDLE"
            r2.last_seen = now
        db.commit()

        # Clean demo transactions
        db.query(AuditEvent).delete()
        db.query(InventoryMovement).delete()
        db.query(Command).delete()
        db.query(Task).delete()
        db.query(StockReservation).delete()
        db.query(OrderItem).delete()
        db.query(Order).delete()
        db.commit()

        # 1. Orders
        ord1 = Order(
            id=str(uuid.uuid4()),
            customer_id=customer.id,
            warehouse_id=wh.id,
            status="FULFILLED",
            created_at=now - timedelta(hours=2)
        )
        ord2 = Order(
            id=str(uuid.uuid4()),
            customer_id=customer.id,
            warehouse_id=wh.id,
            status="IN_PROGRESS",
            created_at=now - timedelta(minutes=50)
        )
        ord3 = Order(
            id=str(uuid.uuid4()),
            customer_id=customer2.id,
            warehouse_id=wh.id,
            status="RESERVED",
            created_at=now - timedelta(minutes=15)
        )
        db.add_all([ord1, ord2, ord3])
        db.commit()

        # 2. Order Items
        oi1 = OrderItem(id=str(uuid.uuid4()), order_id=ord1.id, product_id=prod1.id, requested_qty=10, delivered_qty=10)
        oi2 = OrderItem(id=str(uuid.uuid4()), order_id=ord2.id, product_id=prod2.id, requested_qty=40, delivered_qty=0)
        oi3 = OrderItem(id=str(uuid.uuid4()), order_id=ord3.id, product_id=prod3.id, requested_qty=16, delivered_qty=0)
        db.add_all([oi1, oi2, oi3])
        db.commit()

        bal1 = db.query(InventoryBalance).filter(InventoryBalance.product_id == prod1.id, InventoryBalance.location_id == shelf1.id).first()
        bal2 = db.query(InventoryBalance).filter(InventoryBalance.product_id == prod2.id, InventoryBalance.location_id == shelf1.id).first()
        bal3 = db.query(InventoryBalance).filter(InventoryBalance.product_id == prod3.id, InventoryBalance.location_id == shelf2.id).first()

        # 3. Stock Reservations
        res1 = StockReservation(id=str(uuid.uuid4()), order_item_id=oi1.id, balance_id=bal1.id, qty=10, state="DELIVERED", created_at=now - timedelta(hours=1, minutes=55))
        res2 = StockReservation(id=str(uuid.uuid4()), order_item_id=oi2.id, balance_id=bal2.id, qty=40, state="RESERVED", created_at=now - timedelta(minutes=48))
        res3 = StockReservation(id=str(uuid.uuid4()), order_item_id=oi3.id, balance_id=bal3.id, qty=16, state="RESERVED", created_at=now - timedelta(minutes=14))
        db.add_all([res1, res2, res3])
        db.commit()

        # 4. Tasks
        t1 = Task(id=str(uuid.uuid4()), reservation_id=res1.id, robot_id=r1.id, pickup_location_id=shelf1.id, drop_location_id=packing1.id, state="COMPLETED", quantity=10, created_at=now - timedelta(hours=1, minutes=50), completed_at=now - timedelta(hours=1, minutes=10))
        t2 = Task(id=str(uuid.uuid4()), reservation_id=res2.id, robot_id=r1.id, pickup_location_id=shelf1.id, drop_location_id=packing1.id, state="MOVING_TO_DROP", quantity=40, created_at=now - timedelta(minutes=40))
        t3 = Task(id=str(uuid.uuid4()), reservation_id=res3.id, robot_id=r2.id, pickup_location_id=shelf2.id, drop_location_id=packing2.id, state="QUEUED", quantity=16, created_at=now - timedelta(minutes=10))
        db.add_all([t1, t2, t3])
        db.commit()

        # 5. Inventory Movements
        m1 = InventoryMovement(id=str(uuid.uuid4()), product_id=prod1.id, from_location_id=shelf1.id, to_location_id=packing1.id, reservation_id=res1.id, qty=10, movement_type="DROP", source_event_id=str(uuid.uuid4()), reason="ORDER_FULFILLMENT", actor_id=r1.id, created_at=now - timedelta(hours=1, minutes=10))
        m2 = InventoryMovement(id=str(uuid.uuid4()), product_id=prod2.id, from_location_id=shelf1.id, to_location_id=None, reservation_id=res2.id, qty=40, movement_type="PICK", source_event_id=str(uuid.uuid4()), reason="TASK_PICK", actor_id=r1.id, created_at=now - timedelta(minutes=35))
        db.add_all([m1, m2])

        # 6. Audit Events (Immutable Chain)
        audit_events = [
            (now - timedelta(hours=2, minutes=5), customer.id, "USER", "USER_LOGIN", "AUTH_SESSION", None, "SUCCESS", "CREDENTIALS_VERIFIED"),
            (now - timedelta(hours=2), customer.id, "USER", "ORDER_CREATE", "ORDER", ord1.id, "SUCCESS", "ORDER_SUBMITTED"),
            (now - timedelta(hours=1, minutes=55), "SCHEDULER", "SYSTEM", "STOCK_RESERVE", "INVENTORY", prod1.id, "SUCCESS", "RESERVED_10_UNITS"),
            (now - timedelta(hours=1, minutes=50), operator.id, "USER", "TASK_DISPATCH", "TASK", t1.id, "SUCCESS", "ASSIGNED_TO_AGV-01"),
            (now - timedelta(hours=1, minutes=10), r1.id, "ROBOT", "MISSION_COMPLETED", "ORDER", ord1.id, "SUCCESS", "DROPPED_AT_PACKING_BAY_1"),
            (now - timedelta(minutes=50), customer.id, "USER", "ORDER_CREATE", "ORDER", ord2.id, "SUCCESS", "ORDER_SUBMITTED"),
            (now - timedelta(minutes=42), "ATTACKER_IP_192.168.1.105", "ANONYMOUS", "IDOR_PROBE", "ORDER", ord1.id, "DENIED", "TENANT_ISOLATION_VIOLATION_BLOCKED"),
            (now - timedelta(minutes=40), operator.id, "USER", "TASK_DISPATCH", "TASK", t2.id, "SUCCESS", "ASSIGNED_TO_AGV-01"),
            (now - timedelta(minutes=35), r1.id, "ROBOT", "INVENTORY_PICK", "SHELF", shelf1.id, "SUCCESS", "PICKED_40_UNITS_SKU-002"),
            (now - timedelta(minutes=25), "ATTACKER_IP_192.168.1.105", "ANONYMOUS", "API_ACCESS", "FLEET_COMMAND", None, "DENIED", "RBAC_403_INSUFFICIENT_PRIVILEGES"),
            (now - timedelta(minutes=15), customer2.id, "USER", "ORDER_CREATE", "ORDER", ord3.id, "SUCCESS", "ORDER_SUBMITTED"),
            (now - timedelta(minutes=5), auditor.id, "USER", "AUDIT_EXPORT", "AUDIT_LEDGER", None, "SUCCESS", "LEDGER_INTEGRITY_VERIFIED_SHA256"),
        ]

        for ev_time, actor_i, actor_t, act, res_t, res_i, outc, reas in audit_events:
            ev = AuditEvent(
                id=str(uuid.uuid4()),
                timestamp=ev_time,
                actor_id=actor_i,
                actor_type=actor_t,
                action=act,
                target_entity=res_t,
                target_id=res_i,
                outcome=outc,
                reason_code=reas,
                ip_address="127.0.0.1",
                metadata_json='{"integrity": "verified", "signed": "HMAC-SHA256"}'
            )
            db.add(ev)

        db.commit()
        print("✓ Rich database records successfully populated!")
    except Exception as e:
        db.rollback()
        print(f"Error during seed: {e}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    run_seed()
