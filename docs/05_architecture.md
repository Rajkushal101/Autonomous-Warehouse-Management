# Phase 5: Software Architecture & Design Engineering

**Course:** 24CYS401 – Secure Software Engineering  
**System:** 23. Autonomous Warehouse Management System  
**Document Ref:** `docs/05_architecture.md`  
**Marks:** 7  

---

## 1. Architecture Style Proposal & Justification

### Selected Architectural Style: Layered Modular Monolith with Background Dispatch Worker
The system is architected as a **Layered Modular Monolith** comprising a FastAPI core web and API service paired with an asynchronous background Dispatch Worker process sharing a single PostgreSQL transactional database.

### Justification & Trade-Off Analysis
1. **Strong ACID Transactional Guarantees:** Distributed microservice architectures introduce eventual consistency, two-phase commit latency, and network partition risks (split-brain). In contrast, warehouse inventory reservation and robot dispatch require strict, immediate consistency (preventing double-allocation of robots or physical stock). A modular monolith enables single-database transactional row locks (`SELECT ... FOR UPDATE`) and atomic multi-table commits.
2. **Defensive Boundary Isolation:** Components are cleanly decoupled into distinct domain modules (`app/domain/`, `app/services/`, `app/repositories/`). Business invariants (e.g., non-negative stock balances, allowed state transitions) are enforced strictly in the domain layer, making services agnostic to the web or CLI presentation protocol.
3. **Operational Simplicity & Reproducibility:** A modular monolith can be containerized into a single hardened OCI image, deployed with minimal footprint onto Minikube/Kubernetes, and smoke-tested without complex distributed tracing or service mesh overhead.
4. **Stated Architectural Trade-Off:** While this architecture simplifies concurrency and deployment for the laboratory benchmark, it operates on a single primary database. In a multi-facility enterprise warehouse across multiple geographical continents, distributed consensus (e.g., Raft) and physical fieldbus edge controllers would be required.

---

## 2. Component Refinement & Responsibilities (CMP-01 to CMP-08)

| Component ID | Component Name | Core Responsibilities & Public Interface Methods | Security Controls Enforced |
|---|---|---|---|
| **CMP-01** | **Identity & Access Management (IAM)** | Manages human login, session lifecycle, opaque token hashing, and centralized RBAC policy.<br>`authenticate(login, pass)`, `authorize(action, role, resource)`, `revoke_session(token)` | Argon2id/bcrypt hashing, SHA-256 session digests, CSRF validation, rate limiting. |
| **CMP-02** | **Catalog & Inventory Ledger** | Manages products, grid locations, balances, and manual stock adjustments.<br>`get_balance(wh_id, sku)`, `adjust_stock(manager_id, sku, delta, reason)` | Non-negative constraint checks, mandatory manager reason codes, immutable movement ledger. |
| **CMP-03** | **Order Reservation Orchestrator** | Enforces atomic all-or-none inventory reservations and safe order cancellation.<br>`create_order(customer_id, items, idemp_key)`, `cancel_order(customer_id, order_id)` | Deterministic lock ordering, request idempotency, strict tenant ownership (IDOR defense). |
| **CMP-04** | **Robot Fleet & Task Dispatcher** | Manages robot registration, device token validation, task binding, and command queues.<br>`register_robot(serial)`, `assign_task(operator_id, task_id, robot_id, idemp_key)` | Partial unique database index, robot eligibility predicates, sequenced command generation. |
| **CMP-05** | **Discrete Movement Simulator** | Simulates 2D coordinate traversal, verifies cell availability, and enforces collision invariants.<br>`compute_path(start, end)`, `step_move(robot_id, next_pos)` | Serialized warehouse control row lock, mutual exclusion on coordinates, swap prevention. |
| **CMP-06** | **Fulfillment & Reporting Engine** | Validates packing bay delivery and produces tenant-isolated order fulfillment receipts.<br>`confirm_packing_drop(robot_id, task_id)`, `get_customer_receipt(cust_id, order_id)` | Delivery-to-packing validation before state completion, owner-filtered query predicates. |
| **CMP-07** | **Security Audit & Telemetry** | Collects structured forensic events and exposes live/ready health and security metrics.<br>`log_event(actor, action, target, outcome, meta)`, `get_metrics()` | Append-only database rules, credential redaction, read-only auditor inspection. |
| **CMP-08** | **Persistence & Unit of Work** | Encapsulates SQLAlchemy repositories, transaction boundaries, and Alembic migrations.<br>`UnitOfWork.begin()`, `UnitOfWork.commit()`, `UnitOfWork.rollback()` | Connection pool isolation, parameterized queries, rollback on transient failures. |

---

## 3. Mapping of Mandatory Exam Functions to Components

In compliance with Phase 5 instruction requirements:

| Required Exam Function | Warehouse System Component Mapping | Concrete Implementation Class |
|---|---|---|
| **Authentication** | **CMP-01: Identity & Access Management** | `app/services/auth_service.py` (`SessionSecurityService`) |
| **Examination Orchestration** | **CMP-03 & CMP-04: Order & Robot Task Orchestrator** | `app/services/order_service.py` & `app/services/task_service.py` |
| **Evaluation and Results** | **CMP-06: Fulfillment & Reporting Engine** | `app/services/fulfillment_service.py` (`FulfillmentService`) |
| **Audit and Logging** | **CMP-07: Security Audit & Telemetry** | `app/services/audit_service.py` (`AuditService`) |

---

## 4. Software Design Patterns & Concepts (PAT-01 to PAT-06)

Six specific architectural patterns are implemented across the codebase:

1. **PAT-01: Layered Architecture & Separation of Concerns:**
   - *Application:* Strict unidirectional dependency flow: HTTP Controllers (`app/api/`) → Domain Services (`app/services/`) → Data Repositories (`app/repositories/`) → Database Models (`app/models/`). Controllers never make direct SQL queries.
2. **PAT-02: Repository & Unit of Work Pattern:**
   - *Application:* In `TaskAssignmentService`, multiple entity modifications (robot status to `BUSY`, task state to `ASSIGNED`, command insertion, and audit event insertion) are grouped under a single `UnitOfWork` database transaction that commits or rolls back atomically.
3. **PAT-03: Explicit Finite State Machine (FSM):**
   - *Application:* Implemented for `TaskState` (`QUEUED` → `ASSIGNED` → `TO_PICKUP` → `PICKING` → `TO_DROP` → `DROPPING` → `COMPLETED`) and `RobotStatus` (`IDLE`, `BUSY`, `BLOCKED`, `OFFLINE`). Unlawful state transitions (e.g., jumping from `QUEUED` directly to `COMPLETED`) raise an immutable `IllegalStateTransitionError`.
4. **PAT-04: Strategy Pattern (Pathfinding & Dispatching Policy):**
   - *Application:* Path calculation is abstracted via an `IRouteStrategy` interface with a deterministic `GridBreadthFirstSearchStrategy` implementation. The dispatching engine can swap routing algorithms without altering authorization or transaction logic.
5. **PAT-05: Command Pattern:**
   - *Application:* Autonomous robot actions are reified as discrete `Command` domain objects carrying allowlisted operation types (`MOVE_TO_STEP`, `PICK_AT_LOCATION`, `DROP_AT_PACKING`), monotonic sequence numbers, and expected prerequisite states.
6. **PAT-06: Dependency Injection & Secure Inversion of Control:**
   - *Application:* FastAPI's dependency injection container (`Depends(get_current_user)`, `Depends(get_db)`) injects validated security contexts, system clocks, and database sessions into request handlers, facilitating 100% mocked unit testing.

---

## 5. REST API Specifications & Error Envelope

All JSON error responses adhere to a consistent RFC-7807-compliant security envelope:
```json
{
  "error": {
    "code": "INSUFFICIENT_STOCK",
    "message": "Requested quantity exceeds available inventory for SKU-001",
    "request_id": "c1f7b889-4b6e-4e67-8898-d142475ec198",
    "timestamp": "2026-10-08T10:15:30Z"
  }
}
```
*Internal database tracebacks, file paths, and SQL queries are strictly suppressed.*
