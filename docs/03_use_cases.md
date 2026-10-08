# Phase 3: Requirements Analysis & UML Use Cases

**Course:** 24CYS401 – Secure Software Engineering  
**System:** 23. Autonomous Warehouse Management System  
**Document Ref:** `docs/03_use_cases.md`  
**Marks:** 7  

---

## 1. Use Case Model Overview

The system model captures human and autonomous machine interactions across the warehouse fulfillment lifecycle.

### Actors
1. **Customer:** Authenticated user who places orders and tracks fulfillment.
2. **Warehouse Operator:** Operational personnel monitoring robot activity and initiating dispatch.
3. **Warehouse Manager:** Supervisory personnel managing stock balances, products, locations, and exceptions.
4. **System Administrator:** Security and platform personnel managing users, RBAC roles, and system credentials.
5. **Security Auditor:** Independent actor reviewing immutable security audit trails.
6. **Robot Device (AGV):** Autonomous mobile robot executing discrete movement steps and picking/dropping goods.
7. **Dispatcher Worker:** Automated scheduler orchestrating state changes and path steps.

### Use Case Inventory & Relationships
- **UC-01:** Authenticate & End Session *(Actors: All Human Users)*
- **UC-02:** Manage Users & Roles *(Actor: Administrator)*
- **UC-03:** Manage Catalog, Locations & Inventory *(Actors: Manager, Operator [read-only])*
  - `<<include>>` Validate Stock Invariants
- **UC-04:** Place Order & Submit Fulfillment Request *(Actor: Customer)*
  - `<<include>>` Validate Order & Reserve Inventory Atomically
- **UC-05:** Register & Maintain Robot *(Actors: Manager, Administrator)*
- **UC-06:** Assign Robot & Execute Fulfillment Task *(Actors: Operator/Manager, Dispatcher, Robot Device)*
  - `<<include>>` Authorize Operation & Verify Robot Eligibility
  - `<<include>>` Record Attributable Movement & Audit Event
  - `<<extend>>` Handle Robot Collision / Stale Heartbeat Fault *(Trigger: Route blocked or heartbeat elapsed)*
- **UC-07:** Cancel, Pause, Stop & Recover *(Actors: Customer [own unpicked], Operator, Manager)*
- **UC-08:** View Fulfillment Results *(Actors: Customer [own order], Manager [all orders])*
- **UC-09:** Review Security Audit & Health Telemetry *(Actors: Auditor, Administrator)*

---

## 2. Detailed Critical Use Case Specification 1: UC-04

### Use Case ID: UC-04 – Place Order and Submit Fulfillment Request
- **Primary Actor:** Customer (`CUSTOMER` role)
- **Stakeholders & Interests:**
  - Customer: Expects guaranteed stock reservation and reliable order fulfillment.
  - Warehouse Manager: Requires inventory integrity without risk of overselling.
- **Preconditions:**
  1. Customer possesses an active, authenticated session with a valid CSRF token.
  2. Warehouse operational state is not paused.
  3. Catalog contains active products with stocked inventory balances.
- **Trigger:** Customer clicks "Submit Order" with selected items, quantities, and an idempotency key.

#### Main Success Scenario (MSS):
1. Customer selects one or more products with positive integer quantities and submits the order request along with a client-generated UUIDv4 idempotency key.
2. System validates input syntax: non-empty item array, positive integer quantities, valid product UUIDs.
3. System extracts the customer ID directly from the authenticated session context (preventing identity spoofing).
4. System initiates a database transaction and acquires an actor-scoped idempotency lock.
5. System checks for prior execution with the same idempotency key: none found.
6. System locks candidate `inventory_balances` rows using `SELECT ... FOR UPDATE` ordered deterministically by product UUID (preventing deadlocks).
7. System verifies for every requested item that `available_quantity (on_hand - reserved) >= requested_quantity`.
8. System creates the `orders` header record with status `RESERVED`.
9. For each item, system creates an `order_items` record, increments `reserved` on the inventory balance, creates a `stock_reservations` record, and inserts a `tasks` record with state `QUEUED`.
10. System writes a structured `audit_events` record attributing the order creation and stock reservation to the customer.
11. System commits the transaction atomically.
12. System returns HTTP 201 Created with the order details and reserved task references.

#### Extensions / Alternative Flows:
- **4a. Idempotent Replay Submission:**
  - System discovers an existing idempotency record with identical actor ID, endpoint, and payload hash.
  - System verifies previous status `COMMITTED` and returns the previously generated order confirmation with HTTP 200 OK without double-reserving inventory.
- **6a. Conflicting Idempotency Payload:**
  - System discovers an existing idempotency record with the same key but different payload hash.
  - System aborts transaction and returns HTTP 409 Conflict ("Idempotency key reused with differing parameters").
- **7a. Insufficient Stock for Any Item (All-or-None Invariant):**
  - System detects that at least one item has insufficient available stock.
  - System rolls back the entire database transaction (zero partial reservations).
  - System returns HTTP 409 Conflict ("Insufficient stock for SKU [name]. Order aborted.").

#### Exception Flows:
- **2a. Malformed Input / Negative Quantities:**
  - Pydantic validation fails; system returns HTTP 422 Unprocessable Entity with specific field errors.
- **3a. Expired or Revoked Session:**
  - Session verification fails; system terminates request with HTTP 401 Unauthorized.
- **Database Lock Timeout:**
  - High concurrency deadlock avoidance timeout triggers; system rolls back transaction and returns HTTP 503 Service Unavailable ("Transient locking contention, please retry").

#### Postconditions:
- **Success:** An order is created with status `RESERVED`, stock balances have incremented `reserved` counters, fulfillment tasks are `QUEUED`, and audit records are permanently committed.
- **Failure:** Zero changes made to orders, inventory balances, or tasks. Complete rollback.

---

## 3. Detailed Critical Use Case Specification 2: UC-06

### Use Case ID: UC-06 – Assign Robot and Execute Fulfillment Task
- **Primary Actors:** Warehouse Operator (`OPERATOR` / `MANAGER` role), Dispatcher Worker, Robot Device (`AGV`)
- **Preconditions:**
  1. An order item has a corresponding `tasks` record in `QUEUED` state.
  2. At least one registered robot exists in `IDLE` state with battery > 20%, heartbeat age < 30s, and adequate payload capacity.
  3. Warehouse operational state is active (`paused == false`).
- **Trigger:** Operator clicks "Assign Next Robot" or Dispatcher worker triggers automated dispatch tick.

#### Main Success Scenario (MSS):
1. Operator submits task assignment request with target task UUID and idempotency key.
2. System validates operator role and checks warehouse operational status.
3. System opens a database transaction and acquires a row lock on the warehouse control row and target task.
4. System locks eligible candidate robots (`status == 'IDLE'`) with `SELECT ... FOR UPDATE SKIP LOCKED`.
5. System validates robot eligibility: heartbeat freshness <= 30 seconds, battery >= 20%, and robot current position not blocked.
6. System binds the robot to the task: sets task state to `ASSIGNED`, sets robot status to `BUSY`.
7. System generates an allowlisted `Command` record (`PICK_AT_LOCATION`) with sequence number 1 and expected state `TO_PICKUP`.
8. PostgreSQL partial unique constraint validates that no other active task references this robot.
9. System writes an audit event and commits the transaction atomically.
10. Robot simulator daemon polls `/device/commands`, authenticates via bearer token, and receives the pending command.
11. Simulator navigates adjacent grid cells step-by-step; for each step, verifies target cell is unblocked and unoccupied.
12. Upon arriving at storage location, robot issues pickup acknowledgment: system atomically decrements `on_hand` and `reserved` by item quantity, transitions reservation to `PICKED`, and appends a `PICK` record to `inventory_movements`.
13. Robot transitions to `TO_DROP` and traverses coordinates to the designated Packing Area bay.
14. Upon reaching packing bay, robot issues drop acknowledgment: system increments `on_hand` at packing location, marks reservation `DELIVERED`, transitions task to `COMPLETED`, records `DROP` movement, and returns robot to `IDLE`.
15. If all order items are `DELIVERED`, order status transitions to `FULFILLED`.

#### Extensions / Alternative Flows:
- **5a. No Eligible Robots Available:**
  - All robots are busy, low battery, or stale.
  - Task remains in `QUEUED` state; system returns HTTP 200 with notification "No available eligible robots at this time".
- **11a. Grid Route Blocked by Another Robot:**
  - Route calculation identifies target cell is currently occupied by Robot B.
  - Robot A transitions task state to `BLOCKED` with `resume_state = 'TO_PICKUP'`. System emits collision avoidance warning. Robot waits until next tick.
- **13a. Operational Pause Triggered Mid-Transit:**
  - Operator clicks "Emergency Pause".
  - System sets `WarehouseControl.paused = true`. Robot halts at current grid coordinate; active task remains frozen in current state without losing inventory.

#### Exception Flows:
- **1a. Unauthorized Caller (Customer invokes assignment):**
  - AccessPolicy rejects customer identity; returns HTTP 403 Forbidden with security audit log.
- **4a. Race Condition (Two operators assign same robot simultaneously):**
  - Second transaction attempts to acquire locked robot; discovered state is now `BUSY`. Second assignment fails cleanly with HTTP 409 Conflict.
- **10a. Fake Device Impersonation:**
  - Device request carries invalid bearer token; system rejects with HTTP 401 Unauthorized; command is withheld.

#### Postconditions:
- **Success:** Goods physically moved from storage shelf to packing bay; source balance reduced; packing balance increased; task marked `COMPLETED`; robot returned to `IDLE` at packing bay.
