import os
import sys

# Ensure repository root is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.repositories.base import SessionLocal, init_db
from app.models.entities import (
    User, Warehouse, WarehouseControl, Location, Product, InventoryBalance, Robot
)
from app.core.security import hash_password, hash_token, get_utc_now
from app.core.config import settings

def seed_database():
    print("Initializing database tables...")
    init_db()
    db = SessionLocal()

    try:
        # 1. Warehouse & Control
        wh = db.query(Warehouse).filter(Warehouse.id == settings.WAREHOUSE_ID).first()
        if not wh:
            print("Creating Warehouse...")
            wh = Warehouse(
                id=settings.WAREHOUSE_ID,
                name="Central Fulfillment Warehouse Alpha",
                grid_width=10,
                grid_height=10
            )
            db.add(wh)
            db.flush()

            wh_ctrl = WarehouseControl(
                warehouse_id=wh.id,
                paused=False,
                current_tick=0,
                version=1
            )
            db.add(wh_ctrl)

        # 2. Locations (Shelves, Packing, Obstacles, Charging)
        locations_data = [
            # Storage bays
            {"code": "SHELF-01", "type": "STORAGE", "x": 2, "y": 4, "is_blocked": False},
            {"code": "SHELF-02", "type": "STORAGE", "x": 5, "y": 5, "is_blocked": False},
            # Packing bays (off transit corridor)
            {"code": "PACKING-BAY-1", "type": "PACKING", "x": 1, "y": 9, "is_blocked": False},
            {"code": "PACKING-BAY-2", "type": "PACKING", "x": 2, "y": 9, "is_blocked": False},
            # Charging
            {"code": "CHARGING-01", "type": "CHARGING", "x": 0, "y": 0, "is_blocked": False},
            # Blocked Shelving Obstacles
            {"code": "OBS-01", "type": "TRANSIT", "x": 3, "y": 3, "is_blocked": True},
            {"code": "OBS-02", "type": "TRANSIT", "x": 3, "y": 4, "is_blocked": True},
            {"code": "OBS-03", "type": "TRANSIT", "x": 7, "y": 7, "is_blocked": True},
        ]

        loc_map = {}
        for loc in locations_data:
            existing_loc = db.query(Location).filter(
                Location.warehouse_id == wh.id,
                Location.code == loc["code"]
            ).first()
            if not existing_loc:
                existing_loc = Location(
                    warehouse_id=wh.id,
                    code=loc["code"],
                    type=loc["type"],
                    x=loc["x"],
                    y=loc["y"],
                    is_blocked=loc["is_blocked"]
                )
                db.add(existing_loc)
                db.flush()
            loc_map[loc["code"]] = existing_loc

        # 3. Products
        products_data = [
            {"sku": "SKU-001", "name": "Precision Sensor Module", "weight": 0.5},
            {"sku": "SKU-002", "name": "Industrial Servo Motor", "weight": 2.5},
            {"sku": "SKU-003", "name": "Embedded Microcontroller Kit", "weight": 0.3},
        ]
        prod_map = {}
        for p in products_data:
            existing_p = db.query(Product).filter(Product.sku == p["sku"]).first()
            if not existing_p:
                existing_p = Product(
                    sku=p["sku"],
                    name=p["name"],
                    weight=p["weight"],
                    is_active=True
                )
                db.add(existing_p)
                db.flush()
            prod_map[p["sku"]] = existing_p

        # 4. Inventory Balances (Deterministic initial quantities)
        balances_data = [
            {"sku": "SKU-001", "loc": "SHELF-01", "on_hand": 50, "reserved": 0},
            {"sku": "SKU-002", "loc": "SHELF-01", "on_hand": 20, "reserved": 0},
            {"sku": "SKU-003", "loc": "SHELF-02", "on_hand": 100, "reserved": 0},
            {"sku": "SKU-001", "loc": "PACKING-BAY-1", "on_hand": 0, "reserved": 0},
            {"sku": "SKU-002", "loc": "PACKING-BAY-1", "on_hand": 0, "reserved": 0},
            {"sku": "SKU-003", "loc": "PACKING-BAY-1", "on_hand": 0, "reserved": 0},
        ]
        for b in balances_data:
            p = prod_map[b["sku"]]
            l = loc_map[b["loc"]]
            existing_b = db.query(InventoryBalance).filter(
                InventoryBalance.warehouse_id == wh.id,
                InventoryBalance.product_id == p.id,
                InventoryBalance.location_id == l.id
            ).first()
            if not existing_b:
                existing_b = InventoryBalance(
                    warehouse_id=wh.id,
                    product_id=p.id,
                    location_id=l.id,
                    on_hand=b["on_hand"],
                    reserved=b["reserved"],
                    version=1
                )
                db.add(existing_b)

        # 5. Robot Fleet (2 Registered AGVs in distinct valid cells)
        robots_data = [
            {"serial": "AGV-01", "token": "robot-token-alpha-001", "x": 0, "y": 1, "battery": 95},
            {"serial": "AGV-02", "token": "robot-token-beta-002", "x": 8, "y": 8, "battery": 90},
        ]
        for r in robots_data:
            existing_r = db.query(Robot).filter(Robot.serial_number == r["serial"]).first()
            if not existing_r:
                existing_r = Robot(
                    warehouse_id=wh.id,
                    serial_number=r["serial"],
                    token_digest=hash_token(r["token"], secret_key=settings.DEVICE_TOKEN_PEPPER),
                    status="IDLE",
                    battery_pct=r["battery"],
                    capacity_kg=50.0,
                    current_x=r["x"],
                    current_y=r["y"],
                    last_seen=get_utc_now()
                )
                db.add(existing_r)

        # 6. Human User Accounts (5 distinct roles)
        users_data = [
            {"username": "customer_bob", "password": "CustomerPass123!", "role": "CUSTOMER"},
            {"username": "customer_charlie", "password": "CustomerPass123!", "role": "CUSTOMER"},
            {"username": "operator_alice", "password": "OperatorPass123!", "role": "OPERATOR"},
            {"username": "manager_carol", "password": "ManagerPass123!", "role": "MANAGER"},
            {"username": "admin_dan", "password": "AdminPass123!", "role": "ADMIN"},
            {"username": "auditor_eve", "password": "AuditorPass123!", "role": "AUDITOR"},
        ]
        for u in users_data:
            existing_u = db.query(User).filter(User.username == u["username"]).first()
            if not existing_u:
                existing_u = User(
                    username=u["username"],
                    password_hash=hash_password(u["password"]),
                    role=u["role"],
                    is_active=True
                )
                db.add(existing_u)

        db.commit()
        print("Database seed completed successfully with deterministic initial state!")
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
