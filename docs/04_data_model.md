# Phase 4: Data Model & Entity-Relationship Specification

**Course:** 24CYS401 – Secure Software Engineering  
**System:** 23. Autonomous Warehouse Management System  
**Document Ref:** `docs/04_data_model.md`  
**Marks:** 7  

---

## 1. Relational Entities & Data Dictionary

All primary keys use CSPRNG UUIDv4 values. Audit trails and physical inventory ledgers are append-only.

| Entity Name | Primary Key | Foreign Keys | Key Attributes & Security Constraints | Cardinalities & Relationships |
|---|---|---|---|---|
| **`users`** | `id` (UUID) | None | `username` (VARCHAR unique), `password_hash` (VARCHAR bcrypt), `role` (ENUM: CUSTOMER, OPERATOR, MANAGER, ADMIN, AUDITOR), `is_active` (BOOL), `created_at` (TIMESTAMPTZ) | 1 user : N sessions, 1 user : N orders, 1 user : N audit_events |
| **`sessions`** | `id` (UUID) | `user_id` -> `users.id` | `token_digest` (VARCHAR(64) SHA-256 unique), `csrf_token` (VARCHAR(64)), `expires_at` (TIMESTAMPTZ), `revoked_at` (TIMESTAMPTZ nullable) | N sessions : 1 user |
| **`warehouses`** | `id` (UUID) | None | `name` (VARCHAR), `grid_width` (INT default 10), `grid_height` (INT default 10), `created_at` (TIMESTAMPTZ) | 1 warehouse : N locations, 1 warehouse : N robots |
| **`warehouse_controls`** | `warehouse_id` (UUID PK/FK) | `warehouse_id` -> `warehouses.id` | `paused` (BOOL default FALSE), `stop_reason` (TEXT nullable), `current_tick` (BIGINT default 0), `version` (INT optimistic lock) | 1 : 1 warehouse control lock |
| **`locations`** | `id` (UUID) | `warehouse_id` -> `warehouses.id` | `code` (VARCHAR unique per wh), `type` (ENUM: STORAGE, PACKING, CHARGING, TRANSIT), `x` (INT), `y` (INT), `is_blocked` (BOOL), UNIQUE(warehouse_id, x, y) | 1 location : N inventory_balances, 1 location : N tasks |
| **`products`** | `id` (UUID) | None | `sku` (VARCHAR(64) unique), `name` (VARCHAR), `weight` (NUMERIC CHECK weight > 0), `is_active` (BOOL) | 1 product : N balances, 1 product : N order_items |
| **`inventory_balances`**| `id` (UUID) | `warehouse_id`, `product_id`, `location_id` | `on_hand` (INT CHECK >= 0), `reserved` (INT CHECK >= 0 AND reserved <= on_hand), UNIQUE(warehouse_id, product_id, location_id) | 1 balance : N reservations, 1 balance : N movements |
| **`orders`** | `id` (UUID) | `customer_id` -> `users.id`, `warehouse_id` -> `warehouses.id` | `status` (ENUM: CREATED, RESERVED, IN_PROGRESS, FULFILLED, CANCELLED, FAILED), `created_at` (TIMESTAMPTZ), `version` (INT) | 1 order : N order_items |
| **`order_items`** | `id` (UUID) | `order_id` -> `orders.id`, `product_id` -> `products.id` | `requested_qty` (INT CHECK > 0), `delivered_qty` (INT default 0 CHECK <= requested_qty) | N order_items : 1 order |
| **`stock_reservations`**| `id` (UUID) | `order_item_id` -> `order_items.id`, `balance_id` -> `inventory_balances.id` | `qty` (INT CHECK > 0), `state` (ENUM: RESERVED, PICKED, DELIVERED, RELEASED, QUARANTINED), `created_at` (TIMESTAMPTZ) | 1 reservation : 1 task |
| **`robots`** | `id` (UUID) | `warehouse_id` -> `warehouses.id`, `current_location_id` -> `locations.id` | `serial_number` (VARCHAR unique), `token_digest` (VARCHAR(64) SHA-256 unique), `status` (ENUM: IDLE, BUSY, BLOCKED, OFFLINE, MAINTENANCE), `battery_pct` (INT CHECK 0..100), `capacity_kg` (NUMERIC), `last_seen` (TIMESTAMPTZ) | 1 robot : N historical tasks, 1 robot : N commands |
| **`tasks`** | `id` (UUID) | `reservation_id` (unique), `robot_id` (nullable), `pickup_location_id`, `drop_location_id` | `state` (ENUM: QUEUED, ASSIGNED, TO_PICKUP, PICKING, TO_DROP, DROPPING, COMPLETED, BLOCKED, CANCELLED, FAILED), `resume_state` (VARCHAR nullable), `quantity` (INT) | Partial Unique Index on `robot_id` for active states |
| **`commands`** | `id` (UUID) | `robot_id` -> `robots.id`, `task_id` -> `tasks.id` | `sequence_number` (INT), `command_type` (ENUM: MOVE_TO_STEP, PICK_AT_LOCATION, DROP_AT_PACKING, EMERGENCY_STOP), `expected_state` (VARCHAR), `status` (ENUM: PENDING, CLAIMED, ACKNOWLEDGED, FAILED), UNIQUE(robot_id, sequence_number) | N commands : 1 robot |
| **`inventory_movements`**| `id` (UUID) | `product_id`, `from_location_id`, `to_location_id`, `reservation_id` | `qty` (INT CHECK > 0), `movement_type` (ENUM: PICK, DROP, ADJUSTMENT, RETURN), `source_event_id` (UUID unique), `reason` (TEXT), `actor_id` (UUID), `created_at` (TIMESTAMPTZ) | Immutable Append-Only Physical Ledger |
| **`idempotency_records`**| `id` (UUID) | None | `actor_id` (UUID), `endpoint` (VARCHAR), `idempotency_key` (VARCHAR(64)), `request_hash` (VARCHAR(64)), `response_status` (INT), `response_body` (TEXT), UNIQUE(actor_id, endpoint, idempotency_key) | Safe Replay Engine |
| **`audit_events`** | `id` (UUID) | None | `timestamp` (TIMESTAMPTZ), `actor_id` (UUID), `actor_type` (VARCHAR), `action` (VARCHAR), `target_entity` (VARCHAR), `target_id` (UUID), `outcome` (ENUM: SUCCESS, DENIED, FAILED), `reason_code` (VARCHAR), `ip_address` (VARCHAR), `metadata_json` (JSONB) | Append-Only Compliance & Security Trail |

---

## 2. Integrity Constraints & Concurrency Protection

1. **Partial Unique Index on Active Tasks:**
   ```sql
   CREATE UNIQUE INDEX idx_single_active_task_per_robot 
   ON tasks (robot_id) 
   WHERE state IN ('ASSIGNED', 'TO_PICKUP', 'PICKING', 'TO_DROP', 'DROPPING', 'BLOCKED');
   ```
   *Guarantees at the database level that no robot can ever be assigned to two simultaneous tasks under race conditions.*

2. **Inventory Conservation Formula:**
   For every SKU at all times:
   $$\sum \text{Location.on\_hand} + \text{In\_Transit\_Quantity} = \text{Initial\_Total} + \sum \Delta \text{Legitimate\_Adjustments}$$
   Where $\text{In\_Transit\_Quantity} = \sum \text{Reservations}_{\text{state}=\text{PICKED}}$.

3. **No Direct Cascade Deletions:**
   Foreign key relationships to historical operational tables (`tasks`, `inventory_movements`, `audit_events`) utilize `ON DELETE RESTRICT`. Disabling a user or robot sets `is_active = FALSE` or `status = 'OFFLINE'` rather than deleting audit-linked records.
