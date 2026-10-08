import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, ForeignKey, 
    Text, UniqueConstraint, Index, CheckConstraint
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

def generate_uuid() -> str:
    return str(uuid.uuid4())

def get_utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    username = Column(String(64), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(32), nullable=False, default="CUSTOMER")
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)

    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="customer")

class Session(Base):
    __tablename__ = "sessions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token_digest = Column(String(64), unique=True, nullable=False, index=True)
    csrf_token = Column(String(64), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)

    user = relationship("User", back_populates="sessions")

class Warehouse(Base):
    __tablename__ = "warehouses"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(128), nullable=False)
    grid_width = Column(Integer, default=10, nullable=False)
    grid_height = Column(Integer, default=10, nullable=False)
    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)

    locations = relationship("Location", back_populates="warehouse")
    robots = relationship("Robot", back_populates="warehouse")
    control = relationship("WarehouseControl", back_populates="warehouse", uselist=False)

class WarehouseControl(Base):
    __tablename__ = "warehouse_controls"

    warehouse_id = Column(String(36), ForeignKey("warehouses.id", ondelete="CASCADE"), primary_key=True)
    paused = Column(Boolean, default=False, nullable=False)
    stop_reason = Column(Text, nullable=True)
    current_tick = Column(Integer, default=0, nullable=False)
    version = Column(Integer, default=1, nullable=False)

    warehouse = relationship("Warehouse", back_populates="control")

class Location(Base):
    __tablename__ = "locations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    warehouse_id = Column(String(36), ForeignKey("warehouses.id", ondelete="CASCADE"), nullable=False)
    code = Column(String(32), nullable=False)
    type = Column(String(32), nullable=False)  # STORAGE, PACKING, CHARGING, TRANSIT
    x = Column(Integer, nullable=False)
    y = Column(Integer, nullable=False)
    is_blocked = Column(Boolean, default=False, nullable=False)

    warehouse = relationship("Warehouse", back_populates="locations")
    balances = relationship("InventoryBalance", back_populates="location")

    __table_args__ = (
        UniqueConstraint("warehouse_id", "code", name="uq_wh_location_code"),
        UniqueConstraint("warehouse_id", "x", "y", name="uq_wh_location_coords"),
    )

class Product(Base):
    __tablename__ = "products"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    sku = Column(String(64), unique=True, nullable=False, index=True)
    name = Column(String(128), nullable=False)
    weight = Column(Float, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    balances = relationship("InventoryBalance", back_populates="product")
    order_items = relationship("OrderItem", back_populates="product")

    __table_args__ = (
        CheckConstraint("weight > 0", name="chk_positive_product_weight"),
    )

class InventoryBalance(Base):
    __tablename__ = "inventory_balances"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    warehouse_id = Column(String(36), ForeignKey("warehouses.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(String(36), ForeignKey("products.id", ondelete="RESTRICT"), nullable=False)
    location_id = Column(String(36), ForeignKey("locations.id", ondelete="RESTRICT"), nullable=False)
    on_hand = Column(Integer, default=0, nullable=False)
    reserved = Column(Integer, default=0, nullable=False)
    version = Column(Integer, default=1, nullable=False)

    product = relationship("Product", back_populates="balances")
    location = relationship("Location", back_populates="balances")

    __table_args__ = (
        UniqueConstraint("warehouse_id", "product_id", "location_id", name="uq_wh_product_location"),
        CheckConstraint("on_hand >= 0", name="chk_nonnegative_on_hand"),
        CheckConstraint("reserved >= 0", name="chk_nonnegative_reserved"),
        CheckConstraint("reserved <= on_hand", name="chk_reserved_within_on_hand"),
    )

class Order(Base):
    __tablename__ = "orders"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    customer_id = Column(String(36), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    warehouse_id = Column(String(36), ForeignKey("warehouses.id", ondelete="RESTRICT"), nullable=False)
    status = Column(String(32), default="CREATED", nullable=False)  # CREATED, RESERVED, IN_PROGRESS, FULFILLED, CANCELLED, FAILED
    version = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)

    customer = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    order_id = Column(String(36), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(String(36), ForeignKey("products.id", ondelete="RESTRICT"), nullable=False)
    requested_qty = Column(Integer, nullable=False)
    delivered_qty = Column(Integer, default=0, nullable=False)

    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")
    reservations = relationship("StockReservation", back_populates="order_item")

    __table_args__ = (
        CheckConstraint("requested_qty > 0", name="chk_positive_requested_qty"),
        CheckConstraint("delivered_qty >= 0", name="chk_nonnegative_delivered_qty"),
        CheckConstraint("delivered_qty <= requested_qty", name="chk_delivered_within_requested"),
    )

class StockReservation(Base):
    __tablename__ = "stock_reservations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    order_item_id = Column(String(36), ForeignKey("order_items.id", ondelete="CASCADE"), nullable=False)
    balance_id = Column(String(36), ForeignKey("inventory_balances.id", ondelete="RESTRICT"), nullable=False)
    qty = Column(Integer, nullable=False)
    state = Column(String(32), default="RESERVED", nullable=False)  # RESERVED, PICKED, DELIVERED, RELEASED, QUARANTINED
    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)

    order_item = relationship("OrderItem", back_populates="reservations")
    balance = relationship("InventoryBalance")
    task = relationship("Task", back_populates="reservation", uselist=False)

    __table_args__ = (
        CheckConstraint("qty > 0", name="chk_positive_reservation_qty"),
    )

class Robot(Base):
    __tablename__ = "robots"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    warehouse_id = Column(String(36), ForeignKey("warehouses.id", ondelete="CASCADE"), nullable=False)
    serial_number = Column(String(64), unique=True, nullable=False, index=True)
    token_digest = Column(String(64), unique=True, nullable=False)
    status = Column(String(32), default="IDLE", nullable=False)  # IDLE, BUSY, BLOCKED, OFFLINE, MAINTENANCE
    battery_pct = Column(Integer, default=100, nullable=False)
    capacity_kg = Column(Float, default=50.0, nullable=False)
    current_x = Column(Integer, default=0, nullable=False)
    current_y = Column(Integer, default=0, nullable=False)
    last_seen = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)
    version = Column(Integer, default=1, nullable=False)

    warehouse = relationship("Warehouse", back_populates="robots")
    tasks = relationship("Task", back_populates="robot")
    commands = relationship("Command", back_populates="robot")

    __table_args__ = (
        CheckConstraint("battery_pct >= 0 AND battery_pct <= 100", name="chk_battery_percentage_range"),
    )

class Task(Base):
    __tablename__ = "tasks"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    reservation_id = Column(String(36), ForeignKey("stock_reservations.id", ondelete="RESTRICT"), unique=True, nullable=False)
    robot_id = Column(String(36), ForeignKey("robots.id", ondelete="RESTRICT"), nullable=True, index=True)
    pickup_location_id = Column(String(36), ForeignKey("locations.id", ondelete="RESTRICT"), nullable=False)
    drop_location_id = Column(String(36), ForeignKey("locations.id", ondelete="RESTRICT"), nullable=False)
    state = Column(String(32), default="QUEUED", nullable=False)
    resume_state = Column(String(32), nullable=True)
    quantity = Column(Integer, nullable=False)
    attempt = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    reservation = relationship("StockReservation", back_populates="task")
    robot = relationship("Robot", back_populates="tasks")
    pickup_location = relationship("Location", foreign_keys=[pickup_location_id])
    drop_location = relationship("Location", foreign_keys=[drop_location_id])
    commands = relationship("Command", back_populates="task")

    __table_args__ = (
        # Note: In PostgreSQL this is handled by partial unique index idx_single_active_task_per_robot
        Index("ix_task_state_robot", "state", "robot_id"),
    )

class Command(Base):
    __tablename__ = "commands"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    robot_id = Column(String(36), ForeignKey("robots.id", ondelete="CASCADE"), nullable=False)
    task_id = Column(String(36), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    sequence_number = Column(Integer, nullable=False)
    command_type = Column(String(32), nullable=False)  # MOVE_TO_STEP, PICK_AT_LOCATION, DROP_AT_PACKING, EMERGENCY_STOP
    expected_state = Column(String(32), nullable=False)
    status = Column(String(32), default="PENDING", nullable=False)
    payload_json = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)

    robot = relationship("Robot", back_populates="commands")
    task = relationship("Task", back_populates="commands")

    __table_args__ = (
        UniqueConstraint("robot_id", "sequence_number", name="uq_robot_command_sequence"),
    )

class InventoryMovement(Base):
    __tablename__ = "inventory_movements"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    product_id = Column(String(36), ForeignKey("products.id", ondelete="RESTRICT"), nullable=False)
    from_location_id = Column(String(36), ForeignKey("locations.id", ondelete="RESTRICT"), nullable=True)
    to_location_id = Column(String(36), ForeignKey("locations.id", ondelete="RESTRICT"), nullable=True)
    reservation_id = Column(String(36), ForeignKey("stock_reservations.id", ondelete="RESTRICT"), nullable=True)
    qty = Column(Integer, nullable=False)
    movement_type = Column(String(32), nullable=False)  # PICK, DROP, ADJUSTMENT, RETURN
    source_event_id = Column(String(36), unique=True, nullable=False)
    reason = Column(Text, nullable=True)
    actor_id = Column(String(36), nullable=False)
    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)

    product = relationship("Product")

class IdempotencyRecord(Base):
    __tablename__ = "idempotency_records"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    actor_id = Column(String(36), nullable=False)
    endpoint = Column(String(128), nullable=False)
    idempotency_key = Column(String(64), nullable=False)
    request_hash = Column(String(64), nullable=False)
    response_status = Column(Integer, nullable=True)
    response_body = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)

    __table_args__ = (
        UniqueConstraint("actor_id", "endpoint", "idempotency_key", name="uq_actor_endpoint_idemp_key"),
    )

class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    timestamp = Column(DateTime(timezone=True), default=get_utc_now, nullable=False, index=True)
    actor_id = Column(String(36), nullable=False, index=True)
    actor_type = Column(String(32), nullable=False)
    action = Column(String(64), nullable=False, index=True)
    target_entity = Column(String(64), nullable=False)
    target_id = Column(String(36), nullable=True)
    outcome = Column(String(32), nullable=False)  # SUCCESS, DENIED, FAILED
    reason_code = Column(String(64), nullable=False)
    ip_address = Column(String(45), nullable=True)
    metadata_json = Column(Text, nullable=True)
