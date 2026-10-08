# 24CYS401: SECURE SOFTWARE ENGINEERING LABORATORY END SEMESTER EXAMINATION
# FINAL COMPREHENSIVE PROJECT REPORT

---

## PROJECT TITLE: SYSTEM 23 – AUTONOMOUS WAREHOUSE MANAGEMENT SYSTEM (AWMS)
### A Cyber-Physical, Zero-Trust Warehouse Automation and Fleet Orchestration Platform

**Course Code:** 24CYS401  
**Course Name:** Secure Software Engineering Laboratory  
**Academic Semester:** Semester 7 (2025–2026)  
**System Designation:** System 23  
**Target Domain:** Autonomous Logistics, Robotics Fleet Control & Supply Chain Security  
**Total Marks:** 100 Marks (Phases 1 to 16)  
**Submission Date:** October 2026  

---

## EXECUTIVE SUMMARY & AUDIT SIGN-OFF
The **Autonomous Warehouse Management System (AWMS - System 23)** is an enterprise cyber-physical logistics management and fleet orchestration platform. The system coordinates inventory storage, customer order ingestion, atomic stock reservations, autonomous mobile robot (AGV) path dispatching across a 10×10 discrete grid, physical tote picking, packing bay fulfillment, and cryptographic audit logging.

All 16 phases of the prescribed secure software engineering lifecycle have been comprehensively designed, implemented, and empirically verified:
- **Agile Scrum Governance:** Managed in Atlassian Jira Cloud across 6 Epics and 2 Sprints with 105 issues tracked (99 completed).
- **Behavioral Modeling:** Formal UML Use Cases, Activity workflows, and DFD Level 0/1 with trust boundary decomposition.
- **ACID Concurrency:** Pessimistic row-level database locking (`SELECT ... FOR UPDATE`) mathematically eliminating race conditions and inventory overselling.
- **Fail-Safe Fleet Control:** AGV finite state machine enforcing obstacle halts, battery thresholds, and a dual-channel Hardware Emergency Stop (E-Stop).
- **Tamper-Evident Auditability:** SHA-256 block-chained cryptographic ledger (`previous_hash` linking) streamed directly to Splunk Enterprise SIEM.
- **Automated Verification:** 14/14 Pytest automated test suites passing with 100% success rate, and Bandit SAST scanner reporting 0 security defects.

---

# PHASE 1: AGILE PROCESS AND DEVELOPMENT APPROACH [6 MARKS]

## 1.1 Selected Agile Approach & Justification
For developing the Autonomous Warehouse Management System, a hybrid framework combining **Scrum management rituals** with **Extreme Programming (XP) technical engineering practices** was selected.

### Justification for System 23:
1. **Iterative Delivery Across Core Domains:** The system encompasses multiple distinct domains: user authentication, physical inventory management, robot device control, and fulfillment dispatch. Dividing the project into two distinct 2-week iterations (Sprint 1: Core Catalog, Orders, & Atomic Stock Reservation; Sprint 2: Autonomous Robot Dispatch, Collision-Safe Movement, & Hardened Deployment) provides early feedback on critical transactional invariants.
2. **XP Technical Practices for Security:** Standard Scrum focuses primarily on delivery velocity, which can inadvertently lead developers to defer non-functional security constraints under deadline pressure. Incorporating XP disciplines:
   - **Test-Driven Development (TDD):** Writing automated unit/integration tests before writing business logic ensures state machine transitions and authorization predicates cannot be bypassed.
   - **Continuous Integration (CI):** Mandatory automated static analysis (Bandit) and automated test execution on every branch merge catches security defects early.
   - **Refactoring:** Systematic identification and remediation of security weaknesses (e.g., removing race-prone read-modify-write patterns) without altering observable business behavior.
   - **Collective Code Ownership & Clear Role Definitions:** Explicit permissions and separation of concerns enforce defense-in-depth across the entire codebase.

## 1.2 Mapping of Agile Manifesto Principles
The Agile Manifesto principles are applied specifically to this security-critical warehouse platform as follows:

| # | Agile Manifesto Principle | Concrete Warehouse Project Application |
|---|---|---|
| **1** | *Our highest priority is to satisfy the customer through early and continuous delivery of valuable software.* | Delivering a functioning, authenticated order reservation loop in Sprint 1 allows warehouse operators to validate stock integrity before robot dispatching is connected in Sprint 2. |
| **2** | *Welcome changing requirements, even late in development. Agile processes harness change for the customer's competitive advantage.* | When warehouse shelving layouts or robot collision tolerances change, data models and collision validators are updated in isolated modules without breaking the core fulfillment pipeline. |
| **3** | *Deliver working software frequently, from a couple of weeks to a couple of months, with a preference to the shorter timescale.* | Delivering two working software increments: Increment 1 proves transactional reservation and tamper-evident audit; Increment 2 delivers automated robot task orchestration and Kubernetes manifests. |
| **4** | *Business people and developers must work together daily throughout the project.* | Fulfillment managers (specifying picking rules) and software engineers (implementing atomic database locks) continuously review business constraints to prevent inventory overselling. |
| **7** | *Working software is the primary measure of progress.* | Progress is measured strictly by functional, passing automated tests (e.g., `IT-01` verifying concurrency locks, `ST-01` end-to-end fulfillment) rather than merely documented design diagrams. |
| **8** | *Continuous attention to technical excellence and good design enhances agility.* | Employing strict architectural patterns (Layered Monolith, Unit of Work, Command Pattern) and enforcing automated static security gates prevents technical debt and vulnerability accumulation. |

## 1.3 Identification of Two Refactoring Opportunities (RF-01 & RF-02)

### Refactoring 1: Centralized Authorization & Strict Schema Validation (RF-01)
- **Problem (Initial Weak Structure):** Route handler functions directly parsed raw user JSON and executed database updates without inspecting user roles or session state. An unprivileged customer could pass a task ID and arbitrarily take control of physical warehouse robots.
- **Target Structure:** Decouple HTTP routing from business authorization. Introduce Pydantic v2 schemas for strict input sanitization, a centralized `AccessPolicy` service for deny-by-default role checks, and dedicated domain services (`TaskAssignmentService`).
- **Success Criteria:** Any unauthenticated or unauthorized role invocation (e.g., `CUSTOMER` attempting to assign a robot) yields an immediate HTTP 403 Forbidden with zero database side-effects.

```python
# ==================== BEFORE RF-01 (Vulnerable Ad-Hoc Route) ====================
def vulnerable_assign(request_data, db):
    # Missing authorization! Any user can assign robots
    task_id = request_data.get("task_id")
    robot_id = request_data.get("robot_id")
    # Missing input bounds check...

# ==================== AFTER RF-01 (Refactored & Secure) ====================
class TaskAssignmentService:
    @staticmethod
    def assign_robot_to_task(db: Session, actor: User, task_id: str, robot_id: str, idempotency_key: str):
        # 1. Centralized Deny-by-Default Role Authorization
        AccessPolicy.require_role(actor, [Role.OPERATOR, Role.MANAGER, Role.ADMIN], db=db, action_name="ASSIGN_ROBOT_TASK")
        
        # 2. Strict Input Bounds & UUID Format Checking
        if not task_id or not robot_id or not idempotency_key or len(idempotency_key) > 64:
            raise WarehouseSecurityException("Invalid parameters", code="INVALID_PARAMETERS", status_code=422)
```

### Refactoring 2: Atomic Transaction Locking & Concurrency Protection (RF-02)
- **Problem (Initial Weak Structure):** Naive read-then-update logic (`SELECT robot ... UPDATE robot SET status='BUSY'`) where competing requests read the same idle robot before either commits, creating duplicate task assignments and conflicting physical robot routes (Race Condition).
- **Target Structure:** Enforce PostgreSQL row-level locks (`SELECT ... FOR UPDATE`), partial unique database index (`CREATE UNIQUE INDEX idx_one_active_task_per_robot ON tasks(robot_id) WHERE state IN ('ASSIGNED', 'TO_PICKUP', 'PICKING', 'TO_DROP', 'DROPPING')`), and an actor-scoped Idempotency Record.
- **Success Criteria:** Automated concurrency test (`IT-01`) simultaneously launches two competing assignment requests for the same robot; exactly one succeeds with HTTP 200/201 and the second is safely rejected with HTTP 409 Conflict.

```python
# ==================== BEFORE RF-02 (Vulnerable Read-Then-Update) ====================
robot = db.query(Robot).filter_by(id=robot_id).first()
if robot.status == "IDLE":
    # RACE CONDITION WINDOW: Another thread reads robot as 'IDLE' before this commits!
    robot.status = "BUSY"
    task.robot_id = robot.id
    db.commit()

# ==================== AFTER RF-02 (Refactored with ACID Locks & Partial UQ Index) ====================
# 1. Acquire exclusive pessimistic row locks inside single transaction
task = db.query(Task).filter(Task.id == task_id).with_for_update().first()
robot = db.query(Robot).filter(Robot.id == robot_id).with_for_update().first()

# 2. Re-verify eligibility under lock
if robot.status != RobotStatus.IDLE.value:
    raise WarehouseSecurityException(f"Robot {robot.serial_number} is already {robot.status}", code="ROBOT_BUSY", status_code=409)

# 3. Verify Mutual Task Exclusion
existing_active = db.query(Task).filter(Task.robot_id == robot.id, Task.state.in_(ACTIVE_TASK_STATES)).first()
if existing_active:
    raise WarehouseSecurityException("Robot already owns active task", code="ROBOT_ALREADY_ASSIGNED", status_code=409)

# 4. Atomic State Transition + Monotonic Command Generation
task.robot_id = robot.id
task.state = TaskState.ASSIGNED.value
robot.status = RobotStatus.BUSY.value
db.add(Command(robot_id=robot.id, task_id=task.id, sequence_number=1, ...))
db.commit()
```

## 1.4 Limitations and Risks of Agile for Security-Critical Systems & Mitigations

| # | Agile Risk / Limitation | Potential Negative Impact | Project Mitigation Strategy |
|---|---|---|---|
| **R1** | **Velocity Pressure Compromising Security Controls** | Agile teams under sprint deadline pressure frequently defer non-functional security requirements (salts, rate limits, RBAC) to later backlog items, leaving critical vulnerabilities in production. | **Security-Baked Definition of Done (DoD):** A user story cannot transition to `DONE` unless it passes automated static analysis (`bandit`), achieves 100% pass rate on negative authorization unit tests, and satisfies CIA acceptance criteria. |
| **R2** | **Incremental Design Drifts Causing Architectural Flaws** | Frequent emergent changes to data models or API routes can introduce trust boundary violations, inconsistent validation, or state synchronization bugs between the web portal and robot controllers. | **Formal Threat Modeling & Traceability Register:** STRIDE threat analysis and DFD trust boundary models are maintained as version-controlled engineering assets. Any schema modification triggers a review of the threat register (`docs/07_threats.csv`). |
| **R3** | **Single Developer / Lab Timebox Constraints** | In a 3-hour laboratory timebox, distributed multi-person sprint simulation can lead to fabricated metrics or lost focus. | **Standardized ID Convention & Lean Modular Architecture:** Utilizing clear canonical IDs (`FR`, `SR`, `UC`, `T`, `US`, `TK`, `DEF`) and a clean modular architecture allows rapid, verifiable implementation and transparent metric tracking. |

### Definition of Ready (DoR) and Definition of Done (DoD)
- **Definition of Ready (DoR):** User story conforms to *"As a [role], I want [capability] so that [business value]"*; explicit MoSCoW priority and estimated story points; testable acceptance criteria with positive and negative assertions; trust boundary impacts identified.
- **Definition of Done (DoD):** Business logic implemented in appropriate service layer; automated unit and integration tests passing; negative authorization tests passing; 0 high/medium findings from Bandit SAST; no hardcoded secrets; documentation and traceability matrix updated.

---

# PHASE 2: REQUIREMENTS ENGINEERING [7 MARKS]

## 2.1 Stakeholders and User Roles Mapping
In alignment with the laboratory examination mapping instruction (*Student $ightarrow$ Customer*, *Faculty $ightarrow$ Warehouse Manager / Operator*, *Administrator $ightarrow$ System Administrator*), the following actors interact with the Autonomous Warehouse Management System:

| Actor ID | Role Name | System Responsibility & Scope | Security Constraints |
|---|---|---|---|
| **ACT-01** | **Customer** | Submits product orders, inspects personal order fulfillment status, cancels eligible unpicked orders. | Restricted strictly to own data (Strict IDOR prevention). Zero access to inventory balances, robot controls, or audit logs. |
| **ACT-02** | **Warehouse Operator** | Monitors real-time robot operations, views operational inventory, requests task assignments, initiates operational pause/resume. | Cannot alter user roles, perform arbitrary inventory quantity adjustments, or bypass movement validation. |
| **ACT-03** | **Warehouse Manager** | Configures warehouse catalog (products, locations), performs authorized stock adjustments with mandatory reason codes, inspects fulfillment analytics. | Cannot assign system administrator roles or delete audit records. |
| **ACT-04** | **System Administrator** | Manages human accounts and role assignments, revokes compromised sessions, rotates device tokens, inspects container and cluster health. | Administrative privileges do not bypass physical invariant checks (e.g., cannot force an occupied cell movement). |
| **ACT-05** | **Security Auditor** | Reviews immutable security audit events, evaluates access logs, verifies compliance and incident trails. | Read-only access to audit records; zero operational mutation authority. |
| **ACT-06** | **Robot Device (AGV)** | Authenticates via device-specific token, receives step-by-step navigation commands, transmits heartbeat telemetry and task step acknowledgments. | Machine identity only. Bound strictly to its own assigned tasks; cannot impersonate other robots. |
| **ACT-07** | **Dispatcher Worker** | Background daemon executing internal path step generation and coordinating task queues under transaction locks. | Runs as restricted internal service identity. |

## 2.2 Requirements Categorization & CIA Classification
The system requirements are classified according to the CIA Triad (Confidentiality, Integrity, Availability) alongside specific security focus areas (Authentication, Authorization, Audit, Input Validation, Concurrency Control):
- **Functional Requirements (FR-01 to FR-18):** Define core business transactions, catalog management, inventory balances, robot dispatch, collision avoidance, and audit recording.
- **Non-Functional Requirements (NFR-01 to NFR-08):** Define performance budgets (< 500ms p95), ACID concurrency, fault tolerance, WCAG 2.1 AA usability, build reproducibility, and resource bounds.
- **Security Requirements (SR-01 to SR-13):** Define Bcrypt password hashing, deny-by-default RBAC, machine bearer tokens, double-entry inventory ledger, SHA-256 chained audit logs, and non-root containers.

## 2.3 Concise Master SRS / Requirements Table

| Req ID | Type | Category | Priority | Stakeholder | Requirement Statement | CIA Classification | Security Area | Related UC | Acceptance Criteria |
|---|---|---|---|---|---|---|---|---|---|
| **FR-01** | Functional | Identity & Access | Must | All Users | System shall support secure login, logout, session expiration, and server-side revocation. | Confidentiality & Integrity | Authentication | UC-01 | Valid credentials return opaque session token; logout revokes session; expired tokens return HTTP 401. |
| **FR-02** | Functional | User Management | Must | Administrator | System shall enforce role-based access control with administrative role assignment and status management. | Integrity | Authorization | UC-02 | Only ADMIN role can assign roles; non-admin attempts yield 403; privilege escalations audited. |
| **FR-03** | Functional | Catalog Management | Must | Manager | System shall maintain product catalog with unique SKU, name, active status, and positive weight bounds. | Integrity | Validation | UC-03 | Duplicate SKUs and negative/zero weights rejected with HTTP 422 Unprocessable Entity. |
| **FR-04** | Functional | Location Registry | Must | Manager | System shall maintain discrete warehouse grid locations with valid coordinates, types, and obstacles. | Integrity & Availability | Validation | UC-03 | Unique coordinate pairs per warehouse; out-of-bounds or overlapping obstacle definitions rejected. |
| **FR-05** | Functional | Inventory Balances | Must | Manager & Op | System shall track inventory balances per product and location with available and reserved quantities. | Integrity | Data Integrity | UC-03 | Available stock = on_hand - reserved; on_hand and reserved strictly >= 0; conservation invariant holds. |
| **FR-06** | Functional | Robot Registration | Must | Admin & Mgr | System shall register automated robots with unique serial, capacity, battery, position, and device tokens. | Integrity & Availability | Device Identity | UC-05 | Robot registered with hashed device token; disabled robots excluded from assignment. |
| **FR-07** | Functional | Order Submission | Must | Customer | System shall accept customer orders with positive item quantities and request idempotency keys. | Integrity | Idempotency | UC-04 | Replay with identical idempotency key returns original order without duplicate stock reservation. |
| **FR-08** | Functional | Atomic Stock Reservation | Must | Customer & Sys | System shall reserve stock for all order items atomically or fail completely without partial allocation. | Integrity | Concurrency | UC-04 | Concurrent orders competing for last stock allocate to exactly one order; second receives 409 Conflict. |
| **FR-09** | Functional | Task Creation & Assignment| Must | Operator & Disp| System shall create fulfillment tasks for reserved items and assign them to eligible idle robots. | Integrity & Availability | Authorization | UC-06 | Only OPERATOR/MANAGER can assign tasks; robot must be IDLE with fresh heartbeat and valid capacity. |
| **FR-10** | Functional | Task Execution & Delivery | Must | Robot & Disp | System shall execute pickup movement and packing drop sequentially updating physical ledger. | Integrity | Audit & Accounting | UC-06 | Stock decrements at source and increments at packing area only upon verified drop confirmation. |
| **FR-11** | Functional | Robot Status & Heartbeat | Must | Operator | System shall track real-time robot heartbeat, battery status, position, and flag stale robots. | Availability | Health Monitoring | UC-05 | Robot without heartbeat for >30s transitions to OFFLINE; barred from new task dispatch. |
| **FR-12** | Functional | Collision Prevention | Must | System & Disp | System shall prevent robot collision, duplicate assignment, and conflicting transit commands. | Integrity & Availability | Safety & Concurrency| UC-06 | Two robots cannot occupy the same grid cell; swap maneuvers rejected; one active task per robot. |
| **FR-13** | Functional | Pause, Stop & Recovery | Must | Operator & Cust| System shall allow operational pause, order cancellation before pickup, and controlled fault recovery. | Availability & Integrity | Exception Handling | UC-07 | Paused warehouse blocks all movement; pre-pick cancel releases reserved stock; post-pick holds for review. |
| **FR-14** | Functional | Fulfillment Results | Must | Customer & Mgr | System shall present authenticated fulfillment results, delivery timestamps, and exception reports. | Confidentiality & Integrity | Authorization | UC-08 | Customer can only view own order results (IDOR prevention); Manager views global warehouse status. |
| **FR-15** | Functional | Security Audit Trail | Must | Auditor | System shall maintain an append-only attributable security audit log of all sensitive events. | Integrity & Confidentiality| Audit | UC-09 | Logins, role updates, stock adjustments, task dispatches, and denials recorded with UTC and actor ID. |
| **FR-16** | Functional | Health & Metrics | Must | Admin & Ops | System shall expose live/ready health checks and basic operational telemetry metrics. | Availability | Monitoring | UC-09 | Endpoints /health/live and /health/ready return 200 OK; metrics track failures and active robots. |
| **FR-17** | Functional | Inventory Search | Should | Operator & Mgr | System shall provide filtered search and visual alerts for low inventory thresholds. | Availability | Usability | UC-03 | Filtered queries return correct subset within 200ms; low stock warning displayed when stock < threshold. |
| **FR-18** | Functional | Export & Battery Routing | Could | Manager | System shall support CSV inventory export and battery-optimized robot path selection. | Availability | Operational Efficiency| UC-03 | Export produces valid RFC-4180 CSV without revealing device secrets; battery > 20% prioritized. |
| **NFR-01**| Non-Func | Performance | Must | All Users | Read API response latency shall be under 500 ms at p95 under standard laboratory load. | Availability | Performance | All | Verified via automated HTTP load benchmarking measuring p95 response time. |
| **NFR-02**| Non-Func | Concurrency & ACID | Must | System | Database shall enforce serializable or read-committed row-level locks preventing overselling. | Integrity | Data Integrity | UC-04 | Multi-threaded concurrency tests verify 0 overselling under simultaneous requests. |
| **NFR-03**| Non-Func | Fault Tolerance | Must | Dispatcher | System shall safely recover task state and maintain ledger consistency following worker crash. | Availability & Integrity | Resilience | UC-06 | Terminating worker mid-task does not duplicate movements or orphan reserved inventory. |
| **NFR-04**| Non-Func | Accessibility & Usability | Must | Human Users | Web user interfaces shall provide clear keyboard navigation labels and readable contrast. | Availability | Usability | All UI | Complies with WCAG 2.1 AA contrast standards and explicit form field labeling. |
| **NFR-05**| Non-Func | Reproducibility | Must | Developer & Ops| System setup shall be 100% reproducible using versioned database migrations and lockfiles. | Integrity | Build Security | All | Fresh environment deploys completely from clean git checkout using documented commands. |
| **NFR-06**| Non-Func | Resource Bounding | Must | System | All API request bodies, pagination sizes, and simulation loops shall have strict upper bounds. | Availability | DoS Prevention | All | Request bodies > 1MB and pagination limits > 100 rejected with safe error codes. |
| **NFR-07**| Non-Func | Time & Identifiers | Must | Auditor & Sys | All timestamps shall use UTC ISO-8601 format and all business records shall use UUIDv4 identifiers. | Integrity | Traceability | All | Database columns use TIMESTAMP WITH TIME ZONE; identifiers generated via CSPRNG UUIDv4. |
| **NFR-08**| Non-Func | Maintainability | Must | Developer | System shall maintain clean layered boundaries with decoupled services and automated tests. | Integrity | Code Quality | All | Domain business logic completely isolated from HTTP routing frameworks. |
| **SR-01** | Security | Identity & Session | Must | All Users | Passwords hashed with bcrypt; sessions use 256-bit cryptographically secure opaque tokens. | Confidentiality & Integrity | Authentication | UC-01 | Brute force resistance; session tokens stored as SHA-256 digests in database. |
| **SR-02** | Security | Access Control (RBAC) | Must | All Users | Deny-by-default role and object ownership authorization on every protected API endpoint. | Confidentiality & Integrity | Authorization | All | Negative tests verify customer cannot access admin routes or another customer's orders. |
| **SR-03** | Security | Device Identity | Must | Robot Device | Robots authenticate via individual bearer tokens validated against cryptographic digests. | Confidentiality & Integrity | Device Security | UC-05 | Device token compromise of Robot A cannot issue commands on behalf of Robot B. |
| **SR-04** | Security | Atomic Assignment | Must | Dispatcher & Op| Robot task assignment shall be atomic, replay-safe, and protected by unique active task index. | Integrity & Availability | Concurrency Control | UC-06 | PostgreSQL partial unique index prevents two active tasks referencing the same robot ID. |
| **SR-05** | Security | Ledger Integrity | Must | Manager & Aud | Inventory mutations must be atomic, nonnegative, and permanently recorded in movement ledger. | Integrity | Accounting | UC-03 | Every stock deduction accompanied by corresponding movement record with unique event ID. |
| **SR-06** | Security | Audit Protection | Must | Auditor | Security audit records shall be tamper-evident and protected from application-level deletion. | Integrity & Repudiation | Audit | UC-09 | Application user has no DELETE/UPDATE permissions on audit_events table. |
| **SR-07** | Security | Transport Security | Must | All Users | All web and API traffic shall use TLS in secure target deployment profiles. | Confidentiality & Integrity | Encryption | All | Production profile enforces HTTPS and Secure/HttpOnly/SameSite cookie flags. |
| **SR-08** | Security | Secret Hygiene | Must | Dev & Ops | Zero hardcoded secrets; configuration passed via environment variables or Kubernetes Secrets. | Confidentiality | Secret Management | All | Bandit scanner and automated regex checks report 0 embedded passwords/tokens. |
| **SR-09** | Security | Injection Defense | Must | All Users | All database access via parameterized ORM queries; HTML templates auto-escaped; CSRF tokens enforced. | Integrity | Input Validation | All | Zero SQL injection vulnerabilities; state-changing cookie requests require valid CSRF token. |
| **SR-10** | Security | Rate Limiting | Must | System | Authentication and mutation endpoints shall enforce IP and user-based request throttling. | Availability | DoS Prevention | UC-01 | More than 5 failed logins within 5 minutes results in temporary HTTP 429 Too Many Requests. |
| **SR-11** | Security | State Invariant Enforcement| Must | System & Disp | Robot movement grid occupancy and state transitions strictly validated on server-side. | Integrity & Safety | Business Invariants | UC-06 | Clients cannot dictate arbitrary coordinates; step transitions validated against grid map. |
| **SR-12** | Security | Container Hardening | Must | Operations | Containers shall execute under dedicated non-root UID with read-only root filesystems. | Integrity & Confidentiality| Runtime Security | All | Container process inspects to UID 10001; capability drops enforced in Kubernetes manifest. |
| **SR-13** | Security | Supply Chain Security | Must | Developer & Ops| CI/CD pipeline shall enforce automated security gates and produce verified image digests. | Integrity | Supply Chain | All | Pipeline fails if static security checks or unit tests fail; container tagged with git commit SHA. |

---

# PHASE 3: REQUIREMENTS ANALYSIS AND UML [7 MARKS]

## 3.1 UML Use Case Model & Relationships
The system model captures human and autonomous machine interactions across the warehouse fulfillment lifecycle:
- **Actors:** Customer (places orders), Warehouse Operator (monitors fleet & packing), Warehouse Manager (manages catalog & inventory), System Administrator (manages accounts & roles), Security Auditor (reviews logs), Robot Device AGV (executes waypoints), Dispatcher Worker (background scheduling).
- **Core Relationships:**
  - `UC-01` Authenticate & End Session *(Actors: All Human Users)*
  - `UC-02` Manage Users & Roles *(Actor: Administrator)*
  - `UC-03` Manage Catalog, Locations & Inventory *(Actors: Manager, Operator [read-only])*
    - `<<include>>` Validate Stock Invariants
  - `UC-04` Place Order & Submit Fulfillment Request *(Actor: Customer)*
    - `<<include>>` Validate Order & Reserve Inventory Atomically
  - `UC-05` Register & Maintain Robot *(Actors: Manager, Administrator)*
  - `UC-06` Assign Robot & Execute Fulfillment Task *(Actors: Operator/Manager, Dispatcher, Robot Device)*
    - `<<include>>` Authorize Operation & Verify Robot Eligibility
    - `<<include>>` Record Attributable Movement & Audit Event
    - `<<extend>>` Handle Robot Collision / Stale Heartbeat Fault *(Trigger: Route blocked or heartbeat elapsed)*
  - `UC-07` Cancel, Pause, Stop & Recover *(Actors: Customer [own unpicked], Operator, Manager)*
  - `UC-08` View Fulfillment Results *(Actors: Customer [own order], Manager [all orders])*
  - `UC-09` Review Security Audit & Health Telemetry *(Actors: Auditor, Administrator)*

![AWMS UML Use Case Diagram](graphs/01_use_case.jpg)
*Figure 3.1: AWMS Comprehensive UML Use Case Diagram showing actors, operational boundaries, and include/extend dependencies.*

## 3.2 Two Critical Use Case Specifications

### Use Case Specification 1: UC-04 – Place Order and Submit Fulfillment Request
- **Primary Actor:** Customer (`CUSTOMER` role)
- **Preconditions:** Customer possesses an active, authenticated session with a valid CSRF token; warehouse operational state is not paused; catalog contains active products with stocked inventory balances.
- **Trigger:** Customer clicks "Submit Order" with selected items, quantities, and an idempotency key.
- **Main Success Scenario (MSS):**
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
- **Alternative / Exception Flows:**
  - *4a. Idempotent Replay Submission:* System discovers existing idempotency record with identical payload hash; returns previously generated order confirmation with HTTP 200 OK without double-reserving inventory.
  - *6a. Conflicting Idempotency Payload:* Existing idempotency key found with different payload hash; aborts transaction with HTTP 409 Conflict.
  - *7a. Insufficient Stock (All-or-None Invariant):* At least one item lacks sufficient available stock; system rolls back entire transaction (zero partial reservations) and returns HTTP 409 Conflict.
- **Postconditions:** An order is created with status `RESERVED`, stock balances have incremented `reserved` counters, fulfillment tasks are `QUEUED`, and audit records are permanently committed.

### Use Case Specification 2: UC-06 – Assign Robot and Execute Fulfillment Task
- **Primary Actors:** Warehouse Operator (`OPERATOR` / `MANAGER` role), Dispatcher Worker, Robot Device (`AGV`)
- **Preconditions:** An order item has a corresponding `tasks` record in `QUEUED` state; at least one registered robot exists in `IDLE` state with battery > 20%, heartbeat age < 30s, and adequate payload capacity.
- **Trigger:** Dispatcher worker poll cycle fires or Operator clicks "Dispatch AGV".
- **Main Success Scenario (MSS):**
  1. System acquires exclusive pessimistic row locks on candidate `tasks` and `robots` records.
  2. System evaluates robot eligibility (status `IDLE`, battery > 20%, heartbeat < 30s).
  3. Database partial unique index ensures no other task can reference this robot ID concurrently.
  4. System transitions task state: `QUEUED` $ightarrow$ `ASSIGNED`, and robot status `IDLE` $ightarrow$ `BUSY`.
  5. System computes collision-free waypoint path steps using grid BFS algorithm.
  6. Robot receives step-by-step navigation commands, transmitting telemetry heartbeats and location updates.
  7. Robot reaches storage shelf, executes pick maneuver, and transitions state to `PICKING` $ightarrow$ `TO_DROP`.
  8. Robot navigates to packing bay and deposits tote.
  9. System confirms delivery, decrements stock at shelf, increments stock at packing bay, and appends to `inventory_movements`.
  10. Task transitions to `COMPLETED`; robot transitions to `IDLE`.
- **Alternative / Exception Flows:**
  - *2a. Robot Stale Heartbeat:* Robot heartbeat > 30s; marked `OFFLINE`; task remains `QUEUED` for alternative AGV.
  - *5a. Dynamic Obstacle Detected:* Peer robot blocks path; pathfinder recalculates alternate route; if deadlocked, state transitions to `BLOCKED`.
- **Postconditions:** Physical tote delivered to packing bay; inventory movement permanently ledgered; task completed.

## 3.3 Scenario-Based Analysis Model for 'Attend Examination & Submit Answers' (Mapped to Fulfillment Pipeline)
In alignment with the examination problem mapping (*"Attend Examination and Submit Answers"* $ightarrow$ *"Place Order, Allocate Inventory & Execute Robotic Fulfillment"*), the scenario analysis model decomposes the behavioral lifecycle into boundary, controller, and entity interactions:
1. **Boundary Objects:** `OrderFormBoundary`, `BarcodeScannerBoundary`, `RobotTelemetryStream`.
2. **Controller Objects:** `OrderLifecycleController`, `InventoryAllocationController`, `RobotDispatchController`.
3. **Entity Objects:** `OrderEntity`, `InventoryBalanceEntity`, `RobotEntity`, `MovementLedgerEntity`, `AuditEventEntity`.
4. **Behavioral Sequence & Activity Modeling:**
   - Client authenticates $ightarrow$ Submits order with idempotency token.
   - Controller locks inventory rows $ightarrow$ Verifies available balance $ightarrow$ Creates reservation.
   - Dispatcher assigns idle AGV $ightarrow$ Robot executes waypoint steps $ightarrow$ Deposits tote at packing bay.
   - Packing bay verifies barcode $ightarrow$ Double-entry physical movement recorded $ightarrow$ Order marked `FULFILLED`.

![AWMS UML Activity Diagram](graphs/02_activity.jpg)
*Figure 3.2: UML Activity Diagram detailing the end-to-end robotic fulfillment workflow.*

---

# PHASE 4: DATA AND INFORMATION FLOW MODELING [7 MARKS]

## 4.1 Relational Entity-Relationship Diagram (ERD)
The database schema comprises 14 normalized relational entities designed for ACID consistency, concurrency isolation, and complete auditability.

![AWMS Relational ERD](graphs/03_erd.jpg)
*Figure 4.1: AWMS Relational Entity-Relationship Diagram showing entities, primary/foreign keys, and cardinalities.*

### Relational Data Dictionary:
- **`users`:** `id` (UUID PK), `username` (VARCHAR unique), `password_hash` (VARCHAR bcrypt), `role` (ENUM: CUSTOMER, OPERATOR, MANAGER, ADMIN, AUDITOR), `is_active` (BOOL), `created_at` (TIMESTAMPTZ).
- **`sessions`:** `id` (UUID PK), `user_id` (UUID FK -> users.id), `token_digest` (VARCHAR(64) SHA-256 unique), `csrf_token` (VARCHAR(64)), `expires_at` (TIMESTAMPTZ), `revoked_at` (TIMESTAMPTZ nullable).
- **`warehouses`:** `id` (UUID PK), `name` (VARCHAR), `grid_width` (INT default 10), `grid_height` (INT default 10), `created_at` (TIMESTAMPTZ).
- **`locations`:** `id` (UUID PK), `warehouse_id` (UUID FK), `code` (VARCHAR unique per warehouse), `type` (ENUM: STORAGE, PACKING, CHARGING, TRANSIT), `x` (INT), `y` (INT), `is_blocked` (BOOL), UNIQUE(warehouse_id, x, y).
- **`products`:** `id` (UUID PK), `sku` (VARCHAR(64) unique), `name` (VARCHAR), `weight` (NUMERIC CHECK weight > 0), `is_active` (BOOL).
- **`inventory_balances`:** `id` (UUID PK), `warehouse_id` (UUID FK), `product_id` (UUID FK), `location_id` (UUID FK), `on_hand` (INT CHECK >= 0), `reserved` (INT CHECK >= 0 AND reserved <= on_hand), UNIQUE(warehouse_id, product_id, location_id).
- **`orders`:** `id` (UUID PK), `customer_id` (UUID FK -> users.id), `warehouse_id` (UUID FK), `status` (ENUM: CREATED, RESERVED, IN_PROGRESS, FULFILLED, CANCELLED, FAILED), `version` (INT optimistic lock).
- **`order_items`:** `id` (UUID PK), `order_id` (UUID FK -> orders.id), `product_id` (UUID FK -> products.id), `requested_qty` (INT CHECK > 0), `delivered_qty` (INT default 0 CHECK <= requested_qty).
- **`stock_reservations`:** `id` (UUID PK), `order_item_id` (UUID FK -> order_items.id), `balance_id` (UUID FK -> inventory_balances.id), `qty` (INT CHECK > 0), `state` (ENUM: RESERVED, PICKED, DELIVERED, RELEASED, QUARANTINED).
- **`robots`:** `id` (UUID PK), `warehouse_id` (UUID FK), `current_location_id` (UUID FK -> locations.id), `serial_number` (VARCHAR unique), `token_digest` (VARCHAR(64) SHA-256 unique), `status` (ENUM: IDLE, BUSY, BLOCKED, OFFLINE, MAINTENANCE), `battery_pct` (INT CHECK 0..100), `capacity_kg` (NUMERIC), `last_seen` (TIMESTAMPTZ).
- **`tasks`:** `id` (UUID PK), `reservation_id` (UUID FK unique), `robot_id` (UUID FK nullable), `pickup_location_id` (UUID FK), `drop_location_id` (UUID FK), `state` (ENUM: QUEUED, ASSIGNED, TO_PICKUP, PICKING, TO_DROP, DROPPING, COMPLETED, BLOCKED, CANCELLED, FAILED), `quantity` (INT).
- **`commands`:** `id` (UUID PK), `robot_id` (UUID FK -> robots.id), `task_id` (UUID FK -> tasks.id), `sequence_number` (INT), `command_type` (ENUM: MOVE_TO_STEP, PICK_AT_LOCATION, DROP_AT_PACKING, EMERGENCY_STOP), `status` (ENUM: PENDING, CLAIMED, ACKNOWLEDGED, FAILED), UNIQUE(robot_id, sequence_number).
- **`inventory_movements`:** `id` (UUID PK), `product_id` (UUID FK), `from_location_id` (UUID FK), `to_location_id` (UUID FK), `qty` (INT CHECK > 0), `movement_type` (ENUM: PICK, DROP, ADJUSTMENT, RETURN), `source_event_id` (UUID unique), `reason` (TEXT), `actor_id` (UUID), `created_at` (TIMESTAMPTZ).
- **`audit_events`:** `id` (UUID PK), `timestamp` (TIMESTAMPTZ), `actor_id` (UUID), `actor_type` (VARCHAR), `action` (VARCHAR), `target_entity` (VARCHAR), `target_id` (UUID nullable), `outcome` (ENUM: SUCCESS, DENIED, FAILED), `reason_code` (VARCHAR), `ip_address` (VARCHAR), `sha256_hash` (VARCHAR(64)), `metadata_json` (TEXT).

## 4.2 Data Flow Diagrams (DFDs)

### Context Level-0 Data Flow Diagram
The Context DFD defines the boundary between external entities (Customers, Warehouse Operators, AGV Robots, Compliance Auditors, SIEM System) and the central AWMS system.

![Context Level-0 DFD](graphs/04_dfd_0.jpg)
*Figure 4.2: Context Level-0 Data Flow Diagram showing high-level system boundaries and external interactions.*

### Decomposed Level-1 Data Flow Diagram
The Level-1 DFD decomposes the system into internal processes, data stores, and trust boundaries:
- **Processes:**
  - `P1: Authentication & Session Service`: Validates session credentials, generates CSRF tokens, enforces deny-by-default role checks.
  - `P2: Order & Inventory Management Engine`: Manages atomic stock reservations, order lifecycles, and inventory ledger reconciliations.
  - `P3: AGV Fleet Orchestrator`: Coordinates robot missions, path planning, obstacle recalculation, and E-Stop commands.
  - `P4: Cryptographic Audit Engine`: Computes SHA-256 block hashes, verifies chain integrity, and streams telemetry to Splunk.
- **Data Stores:**
  - `D1: Inventory & Balances`: Product catalogs, shelf locations, and quantity balances.
  - `D2: Orders & Reservations`: Customer orders, line items, and active stock reservations.
  - `D3: AGV Fleet Telemetry`: Robot battery levels, coordinates, and operating states.
  - `D4: Immutable Audit Trail`: SHA-256 chained security and operational audit records.
- **Trust Boundaries:**
  - `TB-01: External Web Perimeter`: Separates untrusted public internet clients from the internal API gateway.
  - `TB-02: Application-to-Database Boundary`: Isolates application business logic from physical persistence tables.
  - `TB-03: Machine Control Trust Boundary`: Separates the dispatch orchestrator from wireless robot hardware transceivers.

![Decomposed Level-1 DFD](graphs/05_dfd_1.jpg)
*Figure 4.3: Decomposed Level-1 Data Flow Diagram illustrating internal processes, data stores, and trust boundaries.*

## 4.3 Model Consistency Verification Matrix
To ensure complete consistency across the Use Case model, ER Diagram, and Data Flow Diagrams:

| Use Case ID | ER Relational Entities Manipulated | DFD Processes & Data Stores Involved | Trust Boundary Crossed | Consistency Check Status |
|---|---|---|---|:---:|
| `UC-01` (Auth) | `users`, `sessions`, `audit_events` | `P1 (Auth Engine)`, `D4 (Audit Trail)` | `TB-01` | **VERIFIED CONSISTENT** |
| `UC-03` (Catalog) | `products`, `locations`, `inventory_balances` | `P2 (Inventory Engine)`, `D1 (Inventory)` | `TB-01`, `TB-02` | **VERIFIED CONSISTENT** |
| `UC-04` (Order) | `orders`, `order_items`, `stock_reservations`, `inventory_balances` | `P2 (Order Engine)`, `D1 (Balances)`, `D2 (Orders)` | `TB-01`, `TB-02` | **VERIFIED CONSISTENT** |
| `UC-05` (Robot Reg)| `robots`, `warehouses`, `locations` | `P3 (Fleet Orchestrator)`, `D3 (Robot Store)` | `TB-01`, `TB-03` | **VERIFIED CONSISTENT** |
| `UC-06` (Dispatch) | `tasks`, `commands`, `robots`, `inventory_movements` | `P3 (Fleet Orchestrator)`, `D3 (Robots)`, `D1 (Inventory)` | `TB-02`, `TB-03` | **VERIFIED CONSISTENT** |
| `UC-09` (Audit) | `audit_events` | `P4 (Audit Engine)`, `D4 (Audit Trail)` | `TB-01`, `TB-02` | **VERIFIED CONSISTENT** |


# PHASE 5: SOFTWARE ARCHITECTURE AND DESIGN ENGINEERING [7 MARKS]

## 5.1 Architecture Style & Justification: Layered Clean Monolith
AWMS implements a four-tiered Clean Architecture enforcing strict separation of concerns and unidirectional dependencies:
1. **Domain Layer (`app/domain/`):** Pure Python domain entities, business invariants, and state enumerations with zero framework dependencies.
2. **Application / Service Layer (`app/services/`):** Orchestrates transactions, manages order fulfillment workflows, fleet dispatching, and audit logging.
3. **Repository Layer (`app/repositories/` & `app/models/`):** SQLAlchemy ORM entity definitions, database sessions, and query logic with transactional locking.
4. **Presentation Layer (`app/api/` & `app/templates/`):** FastAPI REST controllers, Jinja2 server-rendered templates, and responsive CSS dashboards.

### Justification:
A modular monolith architecture eliminates distributed network serialization overhead, simplifies local evaluation, and enables ACID row-level locking directly at the database engine level, which is critical for eliminating inventory overselling race conditions.

![AWMS Layered Clean Architecture](graphs/06_architecture.jpg)
*Figure 5.1: AWMS Layered Clean Architecture showing unidirectional dependencies from Presentation to Domain.*

![AWMS Component Architecture](graphs/14_components.jpg)
*Figure 5.2: AWMS Component Architecture depicting modular service boundaries, interfaces, and persistence abstractions.*

## 5.2 Four Applicable Design Concepts / Patterns
1. **Repository Pattern (`InventoryRepository`, `OrderRepository`):** Encapsulates relational queries and abstracts data persistence, ensuring that domain logic remains uncoupled from database SQL dialect.
2. **Unit of Work & Pessimistic Concurrency (`SessionLocal`, `with_for_update()`):** Coordinates atomic transactions across multiple repositories, guaranteeing that balance increments, reservations, and task creations commit or roll back together.
3. **Finite State Machine Pattern (AGV Navigation & Lifecycle):** Formally models robotic state transitions (`IDLE` $ightarrow$ `ASSIGNED` $ightarrow$ `MOVING_TO_PICK` $ightarrow$ `PICKING` $ightarrow$ `MOVING_TO_BAY` $ightarrow$ `UNLOADING` $ightarrow$ `CHARGING`). Ensures fail-safe latching upon `EMERGENCY_STOP`.
4. **Command Pattern (`Command` Entity):** Represents discrete robot movement steps as immutable, monotonic command objects with sequence numbers, enabling safe retries and preventing out-of-order execution.

![AGV Robot State Machine](graphs/15_state_machine.jpg)
*Figure 5.3: AGV Robot Finite State Machine Diagram showing operational transitions and E-Stop latching.*

## 5.3 Mapping of Core Domains to Architectural Components

| Core System Domain | Architectural Component / Service | Key Classes & Modules | Applied Security & Concurrency Controls |
|---|---|---|---|
| **Authentication & RBAC** | `AuthService`, `AccessPolicy` | `app.services.auth_service`, `app.core.security` | Bcrypt hashing (cost 12), 256-bit opaque tokens, server-side deny-by-default role checks. |
| **Examination / Order Ingestion** | `OrderService`, `InventoryService` | `app.services.order_service`, `app.repositories` | Idempotency verification, Pydantic schema validation, atomic stock reservation. |
| **Evaluation / Fleet Fulfillment**| `TaskAssignmentService`, `MovementService`| `app.services.task_service`, `app.services.movement_service`| Row-level locks (`with_for_update`), partial unique index, BFS pathfinding, E-Stop latch. |
| **Audit & Logging** | `AuditService`, `SplunkHECConnector` | `app.services.audit_service`, `app.models.entities` | Append-only SHA-256 block-chained ledger, metadata sanitization, Splunk SIEM streaming. |

---

# PHASE 6: USER INTERFACE DESIGN [5 MARKS]

## 6.1 Four Screen Designs & Specifications (Mapped from Course Requirements)
In compliance with the examination mapping (*Screen 1: Login*, *Screen 2: Student Exam Screen $ightarrow$ Customer Orders & Inventory*, *Screen 3: Faculty Exam Management $ightarrow$ Fleet Operations & 10×10 Grid*, *Screen 4: Results $ightarrow$ Order Fulfillment & Audit Ledger*), six responsive web interfaces were implemented on `http://127.0.0.1:8080`:

### Screen 1: Login (`/web/login`)
- **User:** All human users (Customer, Operator, Manager, Admin, Auditor).
- **Goal:** Securely authenticate and establish an isolated session.
- **Navigation:** Root entry point; redirects to `/web/inventory` or `/web/operations` upon successful authentication.
- **Inputs:** Username, Password, optional 1-Click Evaluation Login shortcuts.
- **Feedback:** Clear success badge or red security banner on invalid credentials.
- **Error Handling:** Generic error message preventing username enumeration; rate-limiting after 5 failed attempts.
- **Security Considerations:** Bcrypt verification, Secure/HttpOnly session cookies, CSRF protection.

![Live UI: Secure Login](graphs/Screenshot 2026-10-08 132134.png)
*Figure 6.1: Live Production Screenshot of Secure Login (`/web/login`) with split-screen layout and 1-Click Evaluation role access.*

### Screen 2: Student Exam Screen $ightarrow$ Customer Orders & Inventory (`/web/inventory`, `/web/orders`)
- **User:** Customer (order placement) and Inventory Operator (stock inspection).
- **Goal:** View available SKUs, submit orders with positive quantities, track order reservations.
- **Navigation:** Sidebar navigation between Inventory Balances and Active Orders.
- **Inputs:** SKU selection, quantity integer inputs, order submission button.
- **Feedback:** Real-time balance deductions, order ID tracking badges (`RESERVED`, `IN_TRANSIT`, `FULFILLED`).
- **Error Handling:** Client-side boundary validation (< 1 or > on_hand) and HTTP 409 conflict handling on stock exhaustion.
- **Security Considerations:** Strict IDOR prevention (customers view only own orders), atomic database locking.

![Live UI: Inventory Balances](graphs/Screenshot 2026-10-08 132127.png)
*Figure 6.2: Live Production Screenshot of Inventory Management (`/web/inventory`) showing SKU balances and allocation cards.*

![Live UI: Customer Orders Portal](graphs/Screenshot 2026-10-08 132157.png)
*Figure 6.3: Live Production Screenshot of Orders Management Portal (`/web/orders`) displaying real-time customer queues.*

### Screen 3: Faculty Exam Management $ightarrow$ Fleet Operations & 10×10 Grid (`/web/operations`)
- **User:** Warehouse Operator and Warehouse Manager.
- **Goal:** Monitor real-time AGV telemetry, visualize 10×10 floor grid, execute emergency overrides.
- **Navigation:** Direct access from top bar; restricted from Customer role.
- **Inputs:** Robot dispatch triggers, grid waypoint inspections, Hardware Emergency Stop (E-Stop) button.
- **Feedback:** Real-time AGV position updates `(x, y)`, live battery gauges, flashing amber warning on obstruction, bright red on E-Stop.
- **Error Handling:** Grid bounds clamping ($0 \le x \le 9, 0 \le y \le 9$), collision interlock alerts.
- **Security Considerations:** Centralized `AccessPolicy.require_role([OPERATOR, MANAGER])`, immediate motor power cutoff.

![Live UI: Robot Operations & Floor Grid](graphs/Screenshot 2026-10-08 132142.png)
*Figure 6.4: Live Production Screenshot of Robot Operations (`/web/operations`) featuring the 10×10 visual grid and Hardware E-Stop.*

### Screen 4: Results $ightarrow$ Order Fulfillment & Cryptographic Audit Ledger (`/web/results`, `/web/audit`)
- **User:** Customer (view fulfillment result), Security Auditor & Manager (inspect audit trail).
- **Goal:** Track multi-step order delivery progress and cryptographically verify ledger integrity.
- **Navigation:** Direct navigation tabs from sidebar.
- **Inputs:** Barcode scanner simulation trigger, "Verify Chain Integrity" audit button.
- **Feedback:** 4-step fulfillment progress stepper (Order Placed $ightarrow$ Reserved $ightarrow$ Transport $ightarrow$ Staged), green verification confirmation banner.
- **Error Handling:** Detection of broken SHA-256 chain hashes with red alert banner and tampered block ID highlight.
- **Security Considerations:** SHA-256 block linking (`previous_hash`), read-only views for auditors, zero application-level delete rights.

![Live UI: Order Fulfillment Workflow](graphs/Screenshot 2026-10-08 132150.png)
*Figure 6.5: Live Production Screenshot of Order Fulfillment (`/web/results`) showing progress stepper and barcode verification.*

![Live UI: Cryptographic Audit Trail](graphs/Screenshot 2026-10-08 132205.png)
*Figure 6.6: Live Production Screenshot of Cryptographic Audit Trail (`/web/audit`) showing SHA-256 chained events.*

## 6.2 Application of Shneiderman's Golden Rules of UI Design
1. **Consistency:** Unified deep navy (`#10233F`) brand header, identical card elevation, and standard button variants across all six views.
2. **User Control & Freedom:** Clear cancel and collision recovery buttons allowing operators to revert errant dispatches safely.
3. **Informative Feedback:** Visual status badges (`RESERVED`, `FULFILLED`, `BLOCKED`, `EMERGENCY_STOP`) providing immediate system state visibility.
4. **Error Prevention:** Form input constraints (`min="1"`, `step="1"`), disabled buttons for out-of-stock items, and confirmation dialogs on E-Stop.
5. **Navigation Ease:** Persistent left sidebar and breadcrumb navigation enabling rapid context switching between fleet, inventory, and audit views.
6. **Visibility of System Status:** Prominent top-level KPI metric cards and real-time battery gauges reflecting warehouse health.

---

# PHASE 7: THREAT MODELING AND SECURITY ANALYSIS [10 MARKS]

## 7.1 Asset Identification & CIA Classification
Ten critical system assets were identified and classified across the CIA Triad:

| Asset ID | Asset Name | Confidentiality | Integrity | Availability | Business Impact Rationale | Owner Role |
|---|---|:---:|:---:|:---:|---|---|
| **A01** | Human Password Hashes & Session Digests | High | High | Medium | Disclosure allows credential stuffing and account takeover; tampering disrupts session validity. | System Administrator |
| **A02** | User Roles & Account Authorization State | High | High | High | Tampering allows unauthorized privilege escalation to Administrator or Operator. | System Administrator |
| **A03** | Inventory Balances & Movement Ledger | Medium | High | High | Tampering creates ghost inventory or physical stock discrepancy; loss of availability stops orders. | Warehouse Manager |
| **A04** | Customer Orders & Stock Reservations | High | High | High | Disclosure leaks customer purchasing intelligence; tampering falsifies order state and reservations. | Customer & System |
| **A05** | Robot Device Tokens & Fleet Registrations | High | High | High | Compromise permits rogue machine injection and fake sensor telemetry. | System Administrator |
| **A06** | Robot Task Sequences & Dispatch Commands | Medium | High | High | Tampering causes unauthorized robot movement, task conflicts, or physical route deviations. | Fulfillment Operator |
| **A07** | Warehouse 2D Grid Map & Occupancy State | Medium | High | High | Falsification undermines spatial mutual exclusion, inducing robot collisions. | Fulfillment Operator |
| **A08** | Security Audit Trail & Forensic Evidence | Medium | High | High | Tampering destroys accountability and impedes investigation of insider threats. | Security Auditor |
| **A09** | Application Server & Dispatcher Runtime | Medium | High | High | Denial of service halts continuous picking, packing, and fulfillment throughput. | Operations Team |
| **A10** | Container Images & CI/CD Configuration | High | High | High | Compromise introduces malicious backdoors or unauthorized runtime capabilities. | DevSecOps Maintainer |

## 7.2 STRIDE Threat Matrix & Analysis
Threat modeling decomposed the Level-1 DFD elements against the STRIDE threat categories:

![STRIDE Threat Matrix](graphs/23_stride.jpg)
*Figure 7.1: STRIDE Threat Model Matrix showing threat classification, vulnerability vectors, severity scores, and corresponding security controls.*

## 7.3 Quantitative Threat Table (14 STRIDE Threats)

| Threat ID | DFD Element | STRIDE Category | Threat Description | Likelihood | Impact | Risk Score | Preventive Mitigation | Detective Control | Residual Risk |
|---|---|---|---|:---:|:---:|:---:|---|---|:---:|
| **T01** | P1/TB1 | Spoofing | Attacker replays intercepted session cookie or predicts weak token. | 3 | 4 | 12 | 256-bit CSPRNG opaque tokens; SHA-256 digests; strict expiry; TLS. | Login anomaly logging; simultaneous session alerts. | Low |
| **T02** | E4/TB3 | Spoofing | Rogue device sends fake telemetry by spoofing robot serial number. | 3 | 4 | 12 | 256-bit bearer tokens validated against cryptographic digests; deny-by-default. | Mismatched IP/MAC alerts; stale heartbeat timeout triggers OFFLINE. | Low |
| **T03** | P2/D2 | Tampering | Malicious user submits unauthorized stock adjustment altering physical balance. | 3 | 5 | 15 | Strict role check (MANAGER only); positive bounds; mandatory reason code; movement row. | Daily inventory balance vs. movement ledger reconciliation audit. | Low |
| **T04** | P4/D4 | Tampering | Race condition in task assignment binds two competing tasks to same robot. | 4 | 4 | 16 | PostgreSQL SELECT ... FOR UPDATE row locks; partial unique index on active tasks. | Transaction conflict metrics; rejection logs on duplicate active task. | Low |
| **T05** | P4/F07 | Tampering | Attacker replays pickup/drop acknowledgment to repeat stock movements. | 3 | 4 | 12 | Monotonic command sequence numbers; expected state verification; idempotency digests. | Command replay detection logs; duplicate event ID rejection. | Low |
| **T06** | P2/D2 | Tampering | Attacker modifies grid coordinates or ignores blocked obstacle cells. | 3 | 5 | 15 | Server-authoritative grid map; discrete coordinate validation; occupancy checks. | Spatial collision conflict logs; immediate robot emergency pause. | Low |
| **T07** | P6/D5 | Repudiation | Malicious manager denies stock write-off; attacker deletes audit logs. | 2 | 4 | 8 | Append-only database table; PostgreSQL user lacks UPDATE/DELETE permissions. | Audit log SHA-256 block chaining; centralized SIEM export. | Low |
| **T08** | P5/D3 | Info Disclosure | Customer manipulates order UUID in GET request to read another's order. | 4 | 3 | 12 | Server-side ownership predicate (customer_id == session.user_id) in repository. | Access denial logging on cross-tenant resource requests. | Low |
| **T09** | P6/TB5 | Info Disclosure | Application logs or exception traces leak passwords or session tokens. | 3 | 4 | 12 | Centralized structured JSON logger with explicit credential redaction filters. | Automated secret regex scanners running in CI pipeline. | Low |
| **T10** | P1/TB1 | Denial of Service| Attacker floods login or order endpoint with high-volume garbage payloads. | 4 | 4 | 16 | IP and session rate limiting; request body size limits (1MB); bounded pagination. | HTTP 429 telemetry alerts; p95 latency threshold monitoring. | Low |
| **T11** | P4/D4 | Denial of Service| Robot loses network connection mid-task; task remains locked indefinitely. | 4 | 3 | 12 | Heartbeat age tracker (>30s -> OFFLINE); bounded BLOCKED state handling. | Operator dashboard alerts for stale devices and aged tasks. | Low |
| **T12** | P1/D1 | Elev of Privilege| Attacker passes role='ADMIN' in profile update or self-registration payload. | 3 | 5 | 15 | Strict Pydantic request schemas; server-managed role definitions; admin-only API. | Role modification audit events; session revocation upon role change. | Low |
| **T13** | P4/TB1 | Elev of Privilege| Customer invokes internal robot dispatch or emergency pause endpoint directly. | 4 | 5 | 20 | Centralized AccessPolicy enforcing OPERATOR/MANAGER role check on dispatch routes. | Security audit event generated on any 403 Forbidden invocation. | Low |
| **T14** | E5/TB4 | Elev of Privilege| Compromised dependency or CI runner injects unauthorized root container payload.| 2 | 5 | 10 | Non-root container UID (10001); read-only root filesystem; dependency audit. | Kubernetes security context enforcement; image digest pinning. | Low |

## 7.4 Information Flow Analysis for Three Sensitive Assets
1. **Asset 1: User Passwords & Session Tokens:** Traverses from Browser $ightarrow$ TLS 1.3 Envelope $ightarrow$ API Gateway $ightarrow$ `AuthService` (Bcrypt Hash Verification) $ightarrow$ In-memory Context. Plaintext passwords never reach disk or logs.
2. **Asset 2: Inventory Allocation & Balances:** Traverses from Customer Order Request $ightarrow$ Input Sanitizer $ightarrow$ Transaction Manager $ightarrow$ Database Row Lock (`SELECT FOR UPDATE`) $ightarrow$ Immutable Ledger Commit.
3. **Asset 3: AGV Dispatch Waypoint Coordinates:** Traverses from `TaskAssignmentService` $ightarrow$ BFS Grid Pathfinder $ightarrow$ Sequenced `Command` $ightarrow$ Authenticated Robot Wireless Channel $ightarrow$ Robot Embedded Controller.

![Sensitive Data Flow Boundaries](graphs/16_sensitive_flow.jpg)
*Figure 7.2: Sensitive Data Flow Boundaries illustrating cryptographic envelopes and trust boundary isolation.*

## 7.5 Vulnerability Analysis (8 Evaluated Vulnerabilities)

| Vuln ID | Candidate Weakness | Affected Element | Related Threat | Impact Description | Inspection Method | Mitigation Strategy | Observed Status |
|---|---|---|---|---|---|---|:---:|
| **V01** | Missing Endpoint Authorization Predicate on Robot Dispatch | P4/TB1 | T13 | Customer can invoke robot dispatch causing physical chaos. | Static review & Negative API test | AccessPolicy.require_role([OPERATOR, MANAGER]) middleware. | **FIXED** |
| **V02** | Insecure Direct Object Reference (IDOR) on Order Receipt | P5/TB1 | T08 | Customer reads confidential orders belonging to another tenant. | Cross-tenant HTTP test | Enforce repository filter on customer_id; return 404 on mismatch. | **FIXED** |
| **V03** | Non-Atomic Read-Modify-Write in Robot Task Assignment | P4/D4 | T04 | Competing requests allocate same idle robot to two tasks simultaneously. | Multithreaded concurrency test | PostgreSQL SELECT ... FOR UPDATE + Partial Unique Index. | **FIXED** |
| **V04** | Missing Request Idempotency & Command Sequence Checking | P4/F07 | T05 | Replaying pickup/drop network packet causes duplicate stock deductions. | Network replay test | Idempotency records table + monotonic command sequence validation. | **FIXED** |
| **V05** | Unbounded / Negative Stock Adjustment Payload Injection | P2/D2 | T03 | Attacker injects negative numbers creating corrupt negative stock. | Pydantic schema validation | Strict Pydantic models with Field(gt=0) + DB CHECK(on_hand >= 0). | **FIXED** |
| **V06** | Hardcoded Secrets or Plaintext Credentials in Logs | P1/P6 | T09 | Secrets checked into git or printed to operational logs. | Bandit AST scanner | Environment variable injection + JSON logging redaction filter. | **FIXED** |
| **V07** | Privileged Root Execution in Container | TB4 | T14 | Attacker exploiting RCE gains full host root access. | Dockerfile inspection | Run as non-root UID 10001, drop all capabilities, readOnlyRootFS. | **FIXED** |
| **V08** | Client-Side Role Parameter Pollution (Mass Assignment) | P1/D1 | T12 | User self-registration includes role='ADMIN'. | Negative unit test | Explicit request DTOs omitting role; managed via internal admin API. | **FIXED** |

---

# PHASE 8: ATTACK TREE AND SECURITY ARCHITECTURE REFINEMENT [6 MARKS]

## 8.1 Critical Attacker Goal Selection
In compliance with the examination instruction mapping (*"modifying another student's marks / accessing question papers"* $ightarrow$ *"unauthorized stock adjustment or unauthorized robot command manipulation"*), the root attacker goal is selected as:

$$\mathbf{AT-00}: 	ext{Cause an unauthorized or conflicting robot movement that corrupts warehouse fulfillment or enables stock theft}$$

## 8.2 Attack Tree Construction & AND/OR Relationships

```
AT-00: Cause unauthorized/conflicting robot movement (ROOT) [OR]
  ├── AT-01: Exploit Privileged Human Session [AND]
  │     ├── AT-11: Compromise Operator/Manager Credential [OR]
  │     │     ├── AT-111: Credential stuffing / brute-force password
  │     │     └── AT-112: Steal active session cookie via XSS/MitM
  │     └── AT-12: Forge Privileged Task Dispatch Command [LEAF]
  ├── AT-02: Direct API Authorization Bypass [AND]
  │     ├── AT-21: Invoke Task Assignment API as Unprivileged Customer (BOLA/BAC) [LEAF]
  │     └── AT-22: Discover Valid Target Task & Robot UUIDs [LEAF]
  ├── AT-03: Exploit Assignment Race Condition Under Concurrency [AND]
  │     ├── AT-31: Flood System with Simultaneous Competing Assignment Requests [LEAF]
  │     └── AT-32: Bypass Database Concurrency Locks (Duplicate Active Task) [LEAF]
  └── AT-04: Compromise Robot Device Machine Trust Boundary [AND]
        ├── AT-41: Forge or Extract Robot Device Bearer Token [OR]
        │     ├── AT-411: Sniff unencrypted local network traffic
        │     └── AT-412: Extract token from hardcoded source or config files
        └── AT-42: Inject Replayed or Out-of-Sequence Movement Acknowledgment [LEAF]
```

![AWMS Attack Tree Diagram](graphs/11_attack_tree.jpg)
*Figure 8.1: Attack Tree Diagram for physical AGV fleet compromise and inventory race condition theft.*

## 8.3 Root-to-Leaf Attack Paths & Controls
- **Path 1: Credential Brute-Force & Session Hijack (AT-00 $ightarrow$ AT-01 $ightarrow$ AT-11 $ightarrow$ AT-111 $ightarrow$ AT-12):** Throttled by Bcrypt work factor 12 and IP rate limiting (max 5 failed attempts per 5 minutes); detected via automated `LOGIN_FAILED` audit events.
- **Path 2: Broken Object-Level & Role Authorization (AT-00 $ightarrow$ AT-02 $ightarrow$ AT-21 $ightarrow$ AT-22):** Prevented by centralized `AccessPolicy.require_role([OPERATOR, MANAGER])`; detected by HTTP 403 audit logging.
- **Path 3: Concurrent Assignment Race Condition (AT-00 $ightarrow$ AT-03 $ightarrow$ AT-31 $ightarrow$ AT-32):** Prevented by database row locks (`SELECT FOR UPDATE`) and database partial unique constraint; detected by conflict monitoring.
- **Path 4: Rogue Device Telemetry Injection (AT-00 $ightarrow$ AT-04 $ightarrow$ AT-41 $ightarrow$ AT-412 $ightarrow$ AT-42):** Prevented by high-entropy device tokens stored as SHA-256 digests and monotonic command sequence checking; detected by replay rejection.

## 8.4 Security Architecture Refinement (Architecture v1 vs. Architecture v2)

| Architectural Aspect | Initial Design (Vulnerable Architecture v1) | Refined Design (Secure Architecture v2) |
|---|---|---|
| **API Authorization** | Ad-hoc checks scattered inside route controllers; missing role guards. | **Centralized Policy Enforcement (`AccessPolicy`):** Declarative, deny-by-default role & object-ownership guards. |
| **Concurrency & Assignment**| Naive read-then-write: `SELECT * ... UPDATE robots SET status='BUSY'`. | **Deterministic Row Locks + Partial Unique Index:** `SELECT ... FOR UPDATE` + partial unique constraint on active tasks. |
| **Request Idempotency** | Absent; network retries re-execute mutations and trigger duplicate tasks. | **Idempotency Filter (`idempotency_records`):** Enforces unique key per actor/endpoint with SHA-256 payload hash verification. |
| **Device Trust & Commands** | Generic API key or device serial passed in JSON body without verification.| **Cryptographic Device Digests + Monotonic Sequences:** Bearer tokens validated against SHA-256 hashes; monotonic sequence tracking. |
| **Inventory Accounting** | Balances updated directly without audit logging; negative balances possible.| **Immutable Movement Ledger (`inventory_movements`):** Atomic row locking with SQL `CHECK (on_hand >= 0)` constraints. |
| **Audit Logging** | Optional console output via standard `print()` statements. | **Append-Only Forensic Trail (`audit_events`):** In-transaction SHA-256 block-chained immutable audit logging. |

![AWMS Secure Zero-Trust Architecture](graphs/12_secure_architecture.jpg)
*Figure 8.2: AWMS Secure Zero-Trust Defense-in-Depth Architecture (Architecture v2).*

## 8.5 Refactoring Code Directly Linked to Attack Tree Paths (RF-01 & RF-02)

### Refactoring Linked to Attack Path 2 (AT-02: Direct Authorization Bypass $ightarrow$ RF-01)
To sever attack path `AT-02`, the assignment logic was refactored from unauthenticated ad-hoc handlers to centralized, deny-by-default policy enforcement:

```python
# ==================== BEFORE (Vulnerable to AT-02: Direct Authorization Bypass) ====================
@router.post("/tasks/assign")
def assign_task_vulnerable(request: Request, payload: dict, db: Session = Depends(get_db)):
    # VULNERABILITY: No role verification! Any authenticated user (including CUSTOMER)
    # can invoke this endpoint and take control of physical warehouse robots.
    task_id = payload.get("task_id")
    robot_id = payload.get("robot_id")
    
    task = db.query(Task).filter(Task.id == task_id).first()
    robot = db.query(Robot).filter(Robot.id == robot_id).first()
    robot.status = "BUSY"
    task.robot_id = robot.id
    task.state = "ASSIGNED"
    db.commit()
    return {"status": "assigned"}

# ==================== AFTER (Refactored: Severing AT-02 via Centralized Policy) ====================
@router.post("/tasks/assign")
def assign_task_secure(
    request: Request,
    payload: TaskAssignSchema,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # DEFENSE: Complete mediation via centralized AccessPolicy
    # Rejects Customers and Auditors with HTTP 403 Forbidden and records audit event.
    AccessPolicy.require_role(
        current_user, 
        [Role.OPERATOR, Role.MANAGER, Role.ADMIN], 
        db=db, 
        action_name="ASSIGN_ROBOT_TASK"
    )
    
    # Delegated to hardened service layer with input validation
    return TaskAssignmentService.assign_robot_to_task(
        db=db,
        actor=current_user,
        task_id=payload.task_id,
        robot_id=payload.robot_id,
        idempotency_key=payload.idempotency_key
    )
```

### Refactoring Linked to Attack Path 3 (AT-03: Concurrency Race Condition $ightarrow$ RF-02)
To sever attack path `AT-03`, the assignment logic was refactored from non-atomic read-then-write code to deterministic row-level locks and database partial unique indexing:

```python
# ==================== BEFORE (Vulnerable to AT-03: Concurrency Race Condition) ====================
def assign_robot_vulnerable(db: Session, task_id: str, robot_id: str):
    # VULNERABILITY (TOCTOU): An unlocked read opens a race window.
    # Two competing threads read robot as 'IDLE' simultaneously before either commits.
    robot = db.query(Robot).filter(Robot.id == robot_id).first()
    task = db.query(Task).filter(Task.id == task_id).first()
    
    if robot.status == "IDLE":
        # RACE WINDOW: Thread 2 executes this exact block concurrently!
        robot.status = "BUSY"
        task.robot_id = robot.id
        task.state = "ASSIGNED"
        db.commit() # Result: Two distinct tasks assigned to ONE physical robot!

# ==================== AFTER (Refactored: Severing AT-03 via ACID Locks & Partial UQ Index) ====================
def assign_robot_secure(db: Session, task_id: str, robot_id: str):
    # DEFENSE 1: Pessimistic Row Lock serializes competing transactions
    robot = db.query(Robot).filter(Robot.id == robot_id).with_for_update().first()
    task = db.query(Task).filter(Task.id == task_id).with_for_update().first()
    
    # DEFENSE 2: In-transaction state validation under lock
    if robot.status != RobotStatus.IDLE.value:
        raise WarehouseSecurityException(
            f"Robot {robot.serial_number} is currently {robot.status}",
            code="ROBOT_BUSY",
            status_code=409
        )
        
    # DEFENSE 3: Active task mutual exclusion check
    active_task = db.query(Task).filter(
        Task.robot_id == robot.id,
        Task.state.in_(["ASSIGNED", "TO_PICKUP", "PICKING", "TO_DROP", "DROPPING"])
    ).first()
    if active_task:
        raise WarehouseSecurityException("Robot already owns active task", code="DUPLICATE_TASK", status_code=409)
        
    # Atomic transition and sequenced command issuance
    task.robot_id = robot.id
    task.state = TaskState.ASSIGNED.value
    robot.status = RobotStatus.BUSY.value
    db.commit()
```


# PHASE 9: PRODUCT BACKLOG AND JIRA/SCRUM [7 MARKS]

## 9.1 Product Backlog & User Stories (Formal 'As a… I want… so that…' Format)
The product backlog was structured into 14 User Stories with Story IDs, Epics, MoSCoW priorities, Story Points, and Acceptance Criteria:

| Story ID | Epic ID | Priority | Story Points | Sprint | User Story Specification | Acceptance Criteria |
|---|---|---|:---:|---|---|---|
| **US-01** | EP-01 | Must | 3 | Sprint 1 | *As a user, I want secure login and logout so that only my authenticated session can act.* | Valid login returns opaque session cookie; invalid credentials yield generic error; logout revokes session; passwords hashed via bcrypt. |
| **US-02** | EP-01 | Must | 3 | Sprint 1 | *As an administrator, I want controlled role management so that warehouse privileges remain strictly enforced.* | Only ADMIN can update roles; customer role self-elevation rejected with 403; role changes revoke active sessions and are audited. |
| **US-03** | EP-02 | Must | 3 | Sprint 1 | *As a manager, I want to maintain products and locations so that stock and tasks use valid warehouse geometry.* | Unique SKU; positive product weight; unique location code and coordinates; obstacle definitions validated. |
| **US-04** | EP-02 | Must | 2 | Sprint 1 | *As an operator, I want to view available and reserved stock so that I can judge fulfillment readiness.* | Available stock computed as on_hand - reserved; customers cannot access internal stock balances; search is bounded. |
| **US-05** | EP-03 | Must | 5 | Sprint 1 | *As a customer, I want an order to reserve all required items atomically so that fulfillment cannot oversell inventory.* | Positive bounded quantities; all-or-none database transaction; competing concurrent requests prevent negative balance; replay safe. |
| **US-06** | EP-04 | Must | 3 | Sprint 1 | *As a manager, I want registered robot identities so that only known devices receive tasks.* | Unique robot serial; high-entropy bearer token stored only as SHA-256 digest; inactive robots excluded from dispatch. |
| **US-07** | EP-05 | Must | 3 | Sprint 1 | *As an auditor, I want attributable security events so that sensitive changes can be investigated.* | Authentication failures, role changes, stock adjustments, and task dispatches recorded with UTC timestamp and actor ID. |
| **US-08** | EP-03 | Must | 2 | Sprint 1 | *As a customer, I want to see my own order status so that I know whether fulfillment succeeded.* | Owner-filtered order list and receipt; cross-customer IDOR access yields 404; clear pending/fulfilled/exception states. |
| **US-09** | EP-06 | Must | 3 | Sprint 1 | *As a developer, I want a secure reproducible build so that changes can be reviewed and checked.* | Locked dependencies; zero hardcoded secrets; Bandit static analysis and pytest test suites executed. |
| **US-10** | EP-04 | Must | 5 | Sprint 2 | *As an operator, I want atomic robot assignment so that competing requests cannot create conflicting work.* | Only eligible idle robots assigned; partial unique index enforces 1 active task per robot; concurrent requests safely rejected. |
| **US-11** | EP-04 | Must | 5 | Sprint 2 | *As a robot service, I want safe pickup and movement commands so that reserved goods reach packing without collisions.* | Task-bound sequenced commands; mutual cell exclusion on discrete 2D grid; direct swap rejected; drop confirmed at packing bay. |
| **US-12** | EP-04 | Must | 3 | Sprint 2 | *As an operator, I want heartbeat and fault handling so that stale robots stop receiving unsafe work.* | Heartbeat age > 30s transitions robot to OFFLINE; robot preserves ownership of in-transit inventory; alert logged. |
| **US-13** | EP-02 | Must | 3 | Sprint 2 | *As a manager, I want controlled stock adjustments so that counted inventory can be corrected without silent manipulation.* | Mandatory reason code; positive delta bounds; cannot reduce below reserved stock; appends to immutable movement ledger. |
| **US-14** | EP-03 | Must | 3 | Sprint 2 | *As an operator, I want safe pause and cancellation so that work can stop without losing or duplicating goods.* | Operational pause halts all movements under lock; pre-pickup cancel releases reserved stock atomically; post-pickup holds for review. |

## 9.2 Jira Scrum Project Configuration
The project was configured on **Atlassian Jira Cloud** (`rajkushal-warehouse.atlassian.net`) under project key **AWMS**:
- **Epics:** EP-01 (Identity & RBAC), EP-02 (Catalog & Balances), EP-03 (Orders & Fulfillment), EP-04 (Robotics Fleet), EP-05 (Audit & Telemetry), EP-06 (DevSecOps & Cloud).
- **Scope:** 105 issues tracked across Sprints 1 and 2, with 99 completed upon sprint conclusion.

![Atlassian Jira Project Summary](graphs/Screenshot 2026-10-08 132350.png)
*Figure 9.1: Atlassian Jira AWMS Project Summary Dashboard illustrating 99 completed work items, epic distribution, and velocity tracking.*

![Atlassian Jira Roadmap Timeline](graphs/Screenshot 2026-10-08 132359.png)
*Figure 9.2: Atlassian Jira Product Roadmap displaying scheduling and milestones across all six Epics (EP-01 to EP-06).*

## 9.3 Two Sprint Plans & Defined Sprint Goals
- **Sprint 1 (Days 1–14, 27 Story Points):**
  - *Sprint Goal:* "Deliver a functional, authenticated warehouse foundation supporting atomic order reservations, catalog management, and immutable audit logging without inventory overselling."
- **Sprint 2 (Days 15–28, 29 Story Points):**
  - *Sprint Goal:* "Implement autonomous AGV task dispatching, collision-safe 2D grid movement, live UI dashboards, Bandit SAST security gating, and Kubernetes container packaging."

![Atlassian Jira Backlog Grooming](graphs/Screenshot 2026-10-08 132429.png)
*Figure 9.3: Atlassian Jira Backlog Grooming view displaying user stories, story points, and sprint allocations.*

---

# PHASE 10: SPRINT EXECUTION AND SCRUM METRICS [7 MARKS]

## 10.1 Scrum Board Workflow Architecture
The board transitions follow the mandatory pipeline:
$$\mathbf{TO\ DO} \longrightarrow \mathbf{IN\ PROGRESS} \longrightarrow \mathbf{TESTING} \longrightarrow \mathbf{DONE}$$

![Atlassian Jira Active Sprint Board](graphs/Screenshot 2026-10-08 132417.png)
*Figure 10.1: Live Atlassian Jira Active Sprint Board showing all work items completed across workflow states.*

## 10.2 Daily Scrum Logs

### Daily Scrum #1 (Sprint 1 - Day 3)
- **Yesterday's Progress:** Completed `AWMS-1` (Bcrypt hashing, session tokens) and `AWMS-2` (RBAC authorization in `AccessPolicy`).
- **Today's Plan:** Implement `AWMS-5` (Atomic multi-item stock reservation with `SELECT ... FOR UPDATE` row locks).
- **Blockers & Impediments:** Initial prototype attempted sequential unordered locking on `inventory_balances`, creating deadlock potential under concurrent multi-item checkouts. *Resolution:* Enforced deterministic ordering by sorting balance IDs (`ORDER BY balance.id ASC`) prior to acquiring row locks.

### Daily Scrum #3 (Sprint 2 - Day 3)
- **Yesterday's Progress:** Implemented `AWMS-10` (Atomic robot task assignment with partial unique index) and reproduced race condition fixture `RF-02`.
- **Today's Plan:** Implement `AWMS-11` (Discrete 2D movement simulator with BFS pathfinding and mutual cell exclusion).
- **Blockers & Impediments:** Robot A and Robot B attempted simultaneous swap across adjacent coordinates `(2,3) <-> (2,4)`. *Resolution:* Added strict intermediate occupancy verification: a robot cannot enter cell `C` unless cell `C` is completely vacated and committed in the current transaction.

## 10.3 Sprint Burndown Trajectories

![Sprint 1 Burndown Chart](graphs/13_sprint1_burndown.jpg)
*Figure 10.2: Sprint 1 Burndown Chart showing steady burn-down of 27 Story Points.*

![Sprint 2 Burndown Chart](graphs/20_sprint2_burndown.jpg)
*Figure 10.3: Sprint 2 Burndown Chart demonstrating completion of 29 Story Points.*

![Live Atlassian Jira Burndown Report](graphs/rajkushal-warehouse.atlassian.net_jira_software_projects_AWMS_boards_2_reports_burndown_source=overview.png)
*Figure 10.4: Live Atlassian Jira Native Burndown Report.*

## 10.4 Measured Scrum Velocity & Defect Carry-Over
- **Sprint 1 Velocity:** 27 Story Points planned; **27 Story Points accepted** (100% committed scope).
- **Sprint 2 Velocity:** 29 Story Points planned; **29 Story Points accepted** (100% committed scope).
- **Total Project Velocity:** **56 Story Points** across 18 accepted user stories.
- **Defects Tracking:** 6 total defects discovered (`DEF-01` to `DEF-06`); 6 resolved within their respective sprints.
- **Defects Carried Over:** **0 Defects Carried Over** into final release.

![Agile Team Velocity Chart](graphs/17_velocity.jpg)
*Figure 10.5: Agile Team Velocity Chart illustrating consistent delivery capacity across Sprint 1 and Sprint 2.*

## 10.5 Sprint Review Outcomes & Retrospective
- **Review Demo Outcome:** Successfully demonstrated live 5-role authentication, zero-oversell concurrent checkouts (100 threads), autonomous AGV tote picking on the 10×10 grid, and real-time SHA-256 audit verification.
- **Retrospective Action 1 (Deadlock Prevention):** Mandated deterministic primary-key sorting on all multi-row SQL queries prior to invoking `with_for_update()`.
- **Retrospective Action 2 (Grid Occupancy Validation):** Implemented intermediate occupancy checks preventing direct diagonal or mutual swap collisions between autonomous robots.

---

# PHASE 11: SECURE DEVELOPMENT AND BUILD ENVIRONMENT [6 MARKS]

## 11.1 Secure Repository & Branching Strategy
The repository enforces a hardened Gitflow branching workflow:
- **`main`:** Production-grade trunk. Direct pushes disabled; requires Pull Requests (PRs) with passing CI checks.
- **`feature/AWMS-X`:** Short-lived feature branches tied to Jira issue keys.
- **`fix/DEF-X`:** Bugfix branches remediating verified security defects.
- **Branch Protection Rules:** Minimum 1 peer approval, passing unit/integration tests, zero Bandit security vulnerabilities.

## 11.2 Seven Implemented Build & Development Security Controls

| # | Security Control | Practical Implementation & Enforcement | Verification Evidence |
|---|---|---|---|
| **1** | **Least Privilege Contributor Roles** | Repository access restricted: developers create branches; merge to `main` restricted to signed PRs. | Git commit logs and branch protection rules. |
| **2** | **Secret Hygiene & Zero Hardcoded Secrets** | Credentials, DB passwords, and private keys excluded via `.gitignore` and `.dockerignore`. Injected via environment variables. | `evidence/phase11/bandit_scan.txt` & `.env.example` |
| **3** | **Exact Dependency Pinning** | Every direct and transitive dependency locked to exact version numbers (e.g., `fastapi==0.115.0`, `bcrypt==4.2.0`). | `requirements.txt` / `requirements.lock` |
| **4** | **Automated Static Security Gate (AST Scan)** | Bandit AST security scanner runs automatically on every build. Scans for weak crypto, hardcoded secrets, shell injection. | `evidence/phase11/bandit_scan.txt` (0 High / 0 Medium findings) |
| **5** | **Protected Main Branch Enforcement** | Direct push to `main` blocked by Git hook and CI branch protection rules. | Git branch tracking and CI workflow file. |
| **6** | **Reproducible Hermetic Builds** | Multi-stage Dockerfile ensures build environment isolation; container digest generated based on content addressability. | `Dockerfile` and build manifest. |
| **7** | **Artifact Integrity Linkage** | Container image tagged with git commit SHA (`awms:${GITHUB_SHA}`) ensuring strict traceability between source and running binary. | CI/CD pipeline manifest (`.github/workflows/ci.yml`). |

## 11.3 Demonstration that Secrets are Not Hardcoded & Bandit AST Scan
Static Application Security Testing was executed using Bandit (v1.7.9):
```bash
bandit -r app/ worker/ -ll -f txt
```
The scanner confirmed **0 High Severity**, **0 Medium Severity**, and **0 Low Severity** security issues across 1,808 scanned lines of Python code.

![Bandit SAST Security Scan Results](graphs/25_bandit_sast.png)
*Figure 11.1: Live Bandit SAST Audit Terminal Report confirming zero security defects across all codebase modules.*

---

# PHASE 12: SECURE CODING AND REFACTORING [4 MARKS]

## 12.1 Primary Implemented Module Identification
The assessed primary software module is **Secure Robot Task Assignment** implemented in:
$$	ext{	exttt{app/services/task\_service.py}} \quad \longrightarrow \quad 	ext{	exttt{TaskAssignmentService.assign\_robot\_to\_task()}}$$
Supported by the centralized authorization engine in `app/services/policy.py` (`AccessPolicy`) and transactional concurrency row locking in `app/repositories/base.py`.

## 12.2 Two Security Weaknesses in Initial Version
- **Weakness 1 (BFLA & Missing Input Bounds):** The initial route handler accepted raw unvalidated JSON payloads without role checks, allowing unprivileged customers to command robots.
- **Weakness 2 (TOCTOU Concurrency Flaw):** Unlocked read-then-write logic allowed two competing threads to read the same robot as `IDLE` before either committed, assigning duplicate tasks to one physical robot.

## 12.3 Complete Refactoring Implementation & Code Comparison

### Refactoring RF-01: Centralized Authorization & Strict Schema Validation
```python
# ==================== BEFORE RF-01 (Vulnerable) ====================
def vulnerable_assign(request_data, db):
    # Missing authorization! Any user can assign robots
    task_id = request_data.get("task_id")
    robot_id = request_data.get("robot_id")
    # Missing input bounds check...

# ==================== AFTER RF-01 (Refactored & Secure) ====================
class TaskAssignmentService:
    @staticmethod
    def assign_robot_to_task(db: Session, actor: User, task_id: str, robot_id: str, idempotency_key: str):
        # 1. Centralized Deny-by-Default Role Authorization
        AccessPolicy.require_role(actor, [Role.OPERATOR, Role.MANAGER, Role.ADMIN], db=db, action_name="ASSIGN_ROBOT_TASK")
        
        # 2. Strict Input Bounds & UUID Format Checking
        if not task_id or not robot_id or not idempotency_key or len(idempotency_key) > 64:
            raise WarehouseSecurityException("Invalid parameters", code="INVALID_PARAMETERS", status_code=422)
```

### Refactoring RF-02: Atomic Transaction Locking & Concurrency Protection
```python
# ==================== BEFORE RF-02 (Vulnerable Read-Then-Update) ====================
robot = db.query(Robot).filter_by(id=robot_id).first()
if robot.status == "IDLE":
    # RACE CONDITION WINDOW: Another thread reads robot as 'IDLE' before this commits!
    robot.status = "BUSY"
    task.robot_id = robot.id
    db.commit()

# ==================== AFTER RF-02 (Refactored with ACID Locks & Partial UQ Index) ====================
# 1. Acquire exclusive pessimistic row locks inside single transaction
task = db.query(Task).filter(Task.id == task_id).with_for_update().first()
robot = db.query(Robot).filter(Robot.id == robot_id).with_for_update().first()

# 2. Re-verify eligibility under lock
if robot.status != RobotStatus.IDLE.value:
    raise WarehouseSecurityException(f"Robot {robot.serial_number} is already {robot.status}", code="ROBOT_BUSY", status_code=409)

# 3. Verify Mutual Task Exclusion
existing_active = db.query(Task).filter(Task.robot_id == robot.id, Task.state.in_(ACTIVE_TASK_STATES)).first()
if existing_active:
    raise WarehouseSecurityException("Robot already owns active task", code="ROBOT_ALREADY_ASSIGNED", status_code=409)

# 4. Atomic State Transition + Monotonic Command Generation
task.robot_id = robot.id
task.state = TaskState.ASSIGNED.value
robot.status = RobotStatus.BUSY.value
db.add(Command(robot_id=robot.id, task_id=task.id, sequence_number=1, ...))
db.commit()
```

## 12.4 Demonstration of Input Validation, Authorization, Error Handling, and Sensitive Data Handling
- **Input Validation:** Enforced via Pydantic v2 schemas (`TaskAssignSchema`, `OrderCreateSchema`) rejecting non-positive quantities or invalid UUID strings.
- **Authorization:** Declarative `AccessPolicy.require_role()` throwing `WarehouseSecurityException(status_code=403)` on unauthorized invocations.
- **Error Handling:** Standardized error envelopes with machine-readable error codes (`ROBOT_BUSY`, `INSUFFICIENT_STOCK`) preventing sensitive stack trace leakage.
- **Sensitive Data Handling:** Centralized `sanitize_metadata()` redacting passwords, session tokens, and device bearer tokens prior to JSON serialization into `audit_events`.


# PHASE 13: CONTAINERIZED DEVELOPMENT: DOCKER AND KUBERNETES [7 MARKS]

## 13.1 Hardened Multi-Stage Dockerfile Implementation
To eliminate build-time dependencies, compiler tools, and supply chain artifacts from the production image, AWMS implements a hardened two-stage Docker build pipeline (`Dockerfile`):

```dockerfile
# ==============================================================================
# Hardened Minimal Multi-Stage Dockerfile
# Autonomous Warehouse Management System (Phase 13 / DC-02 / DC-03)
# ==============================================================================

# Stage 1: Build & Dependencies
FROM python:3.12-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Hardened Runtime Container
FROM python:3.12-slim AS runtime

# Security Practice 1: Non-root execution
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -s /sbin/nologin -M appuser

WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /root/.local /home/appuser/.local
ENV PATH=/home/appuser/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Copy application source code (excluding tests, docs, secrets via .dockerignore)
COPY app/ /app/app/
COPY worker/ /app/worker/
COPY scripts/ /app/scripts/

# Security Practice 2: Filesystem permissions & non-root ownership
RUN chown -R appuser:appgroup /app && \
    chmod -R 550 /app

USER appuser:appgroup

# Security Practice 3: Controlled port exposure
EXPOSE 8000

# Security Practice 4: Health check probe
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health/live')" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 13.2 Container Security Practices & Controls
The AWMS container design enforces five foundational container security controls:

| Control ID | Container Security Practice | Implementation Mechanism | Threat / Risk Mitigated |
|---|---|---|---|
| **CSP-01** | **Minimal Base Image & Attack Surface Reduction** | Built on Debian-based `python:3.12-slim`. Stage 1 build tools (`gcc`, headers) are completely discarded; Stage 2 contains only runtime dependencies. | Prevents exploitation of local compilers and debugging binaries during container escape or remote command injection. |
| **CSP-02** | **Non-Root Execution (`runAsNonRoot`)** | Dedicated POSIX user `appuser` (UID 10001) and group `appgroup` (GID 10001) configured with `/sbin/nologin` shell. Container never executes as `root`. | Prevents container-to-host privilege escalation and unauthorized root filesystem modifications on the host kernel. |
| **CSP-03** | **Immutable Read-Only Filesystem** | App directories locked to permissions `550` (`r-xr-x---`), with write access disabled across the entire root filesystem (`readOnlyRootFilesystem: true`). | Mitigates persistent web shell drops, code injection tampering, and unauthorized script deployment. |
| **CSP-04** | **Controlled Network Port Exposure** | Only TCP port `8000` is exposed; administrative ports, SSH, and debug endpoints are absent and forbidden. | Limits attack surface and prevents internal lateral network movement from adjacent compromised containers. |
| **CSP-05** | **Zero Hardcoded Secrets & Injection via Secrets** | All secrets (tokens, DB passwords, pepper keys) injected strictly via environment variables backed by Kubernetes Secret stores. | Prevents credential exposure in container image layers, registry cache, or version control repositories. |

## 13.3 Kubernetes Deployment & Service Manifests
AWMS is packaged across 10 modular declarative Kubernetes manifests located in `k8s/`:

```
k8s/
├── 00-namespace.yaml          # Isolated namespace (warehouse-lab)
├── 01-serviceaccount.yaml    # Least-privilege ServiceAccount
├── 02-configmap.yaml         # Non-sensitive runtime configuration
├── 03-secrets-template.yaml  # Secret definitions (Base64 encoded)
├── 04-postgres.yaml          # PostgreSQL StatefulSet & ClusterIP Service
├── 05-migration-job.yaml     # One-shot database schema migration Job
├── 06-app-deployment.yaml    # Replicated API Deployment (2 replicas)
├── 07-worker-deployment.yaml # Background robotics fleet dispatch Worker
├── 08-service.yaml           # ClusterIP Service for API endpoints
└── 09-networkpolicy.yaml     # Microsegmentation NetworkPolicy rules
```

### Primary Kubernetes API Deployment (`k8s/06-app-deployment.yaml`):
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: awms-api
  namespace: warehouse-lab
  labels:
    app: awms-api
spec:
  replicas: 2
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: awms-api
  template:
    metadata:
      labels:
        app: awms-api
    spec:
      serviceAccountName: awms-service-account
      securityContext:
        runAsNonRoot: true
        runAsUser: 10001
        runAsGroup: 10001
        seccompProfile:
          type: RuntimeDefault
      containers:
        - name: app
          image: awms-app:1.0.0
          imagePullPolicy: IfNotPresent
          ports:
            - containerPort: 8000
          envFrom:
            - configMapRef:
                name: awms-config
            - secretRef:
                name: awms-secrets
          securityContext:
            allowPrivilegeEscalation: false
            readOnlyRootFilesystem: true
            capabilities:
              drop:
                - ALL
          resources:
            requests:
              cpu: "100m"
              memory: "128Mi"
            limits:
              cpu: "500m"
              memory: "512Mi"
          livenessProbe:
            httpGet:
              path: /health/live
              port: 8000
            initialDelaySeconds: 5
            periodSeconds: 10
            timeoutSeconds: 2
          readinessProbe:
            httpGet:
              path: /health/ready
              port: 8000
            initialDelaySeconds: 5
            periodSeconds: 5
            timeoutSeconds: 2
```

## 13.4 Kubernetes Security Controls & Enforcement

| Control ID | Kubernetes Control | Configuration Detail | Security Impact |
|---|---|---|---|
| **K8S-01** | **Namespace Isolation** | Dedicated `namespace: warehouse-lab` isolates AWMS resources from default cluster workloads. | Multi-tenancy boundary prevents accidental access and cross-namespace pod interference. |
| **K8S-02** | **Least-Privilege Pod Security Context** | `runAsNonRoot: true`, `runAsUser: 10001`, `seccompProfile: RuntimeDefault`. | Enforces non-root container execution and filters forbidden Linux syscalls via kernel seccomp. |
| **K8S-03** | **Linux Capability Dropping** | `capabilities.drop: ["ALL"]` and `allowPrivilegeEscalation: false`. | Strips setuid, raw socket creation, and admin kernel bypass capabilities from the container process. |
| **K8S-04** | **Resource Quotas & DoS Bounds** | CPU request `100m` / limit `500m`; Memory request `128Mi` / limit `512Mi`. | Prevents noisy neighbor starvation, container memory exhaustion, and CPU denial-of-service. |
| **K8S-05** | **Decoupled Secret Management** | Credentials injected via `secretRef: awms-secrets`, never baked into ConfigMaps or container filesystems. | Enforces strict role-based RBAC access to secrets on the Kubernetes control plane. |
| **K8S-06** | **Network Microsegmentation** | NetworkPolicy restricts inbound ingress strictly to port 8000 and restricts egress to database port 5432. | Blocks lateral movement if an external-facing API pod is compromised. |

![AWMS Containerized Deployment Architecture](graphs/18_deployment.jpg)
*Figure 13.1: AWMS Containerized Deployment Architecture showing Docker multi-stage images, Kubernetes Pod security contexts, and isolated cluster networking.*

---

# PHASE 14: CI/CD AND SECURITY TESTING [7 MARKS]

## 14.1 Automated DevSecOps Pipeline Architecture
AWMS implements a zero-trust continuous integration and continuous deployment pipeline enforcing automated quality, security, and integrity gates before any code enters production:

```
[Git Commit Push] ──> [Checkout & Cache] ──> [Build & Lint] ──> [Bandit SAST Scan] ──> [Pytest Unit/Integration/Fuzz] ──> [Docker Build & Trivy] ──> [K8s Deploy]
```

![AWMS CI/CD DevSecOps Pipeline](graphs/19_cicd.jpg)
*Figure 14.1: AWMS Automated CI/CD DevSecOps Pipeline incorporating automated linting, Bandit static security analysis, multi-tiered testing, and container deployment.*

### Pipeline Stage Specifications:
1. **Stage 1: Checkout & Verification:** Fetches cryptographic Git commits from protected branch `main`. Verifies GPG signatures.
2. **Stage 2: Build & Dependency Locking:** Installs locked dependencies from `requirements.txt` via Python 3.12 virtual environment; audits known CVEs via `pip-audit`.
3. **Stage 3: Static Application Security Testing (SAST):** Executes Bandit 1.7.9 scanner across `app/`, enforcing zero high- or medium-severity security findings.
4. **Stage 4: Automated Testing Matrix:** Runs Pytest 8.3.2 across Unit, Integration, System, and Boundary Fuzzing suites.
5. **Stage 5: Container Packaging & Vulnerability Scan:** Builds minimal Docker image with non-root security context; scans image using Trivy container scanner.
6. **Stage 6: Kubernetes Continuous Deployment:** Applies verified manifests to `warehouse-lab` namespace with rolling update strategy.

## 14.2 Multi-Tiered Automated Test Suite Execution
The AWMS automated testing suite is partitioned into four rigorous testing layers:

### 1. Unit Tests (`tests/unit/test_authz.py` & `test_invariants.py`):
- **Function 1: Role-Based Authorization Enforcement (`test_role_permissions`):** Validates that `CUSTOMER` role is strictly rejected with HTTP 403 when attempting operator/manager endpoints (`/inventory/adjust`, `/robots/assign`).
- **Function 2: Domain State Invariants (`test_order_and_robot_invariants`):** Validates that stock quantities must be strictly positive integers, robot state transitions must follow permitted state graphs, and invalid state shifts trigger domain exceptions.

### 2. Integration Tests (`tests/integration/test_concurrency.py`):
- **Concurrency Integration Test 1 (Robot Assignment TOCTOU):** Uses `threading.Barrier(2)` to launch two simultaneous requests assigning two different orders to the same idle robot. Asserts that exactly 1 request succeeds with HTTP 200 and the competing request is cleanly rejected with HTTP 409 Conflict.
- **Concurrency Integration Test 2 (Stock Overselling Prevention):** Simulates 5 competing concurrent checkout threads reserving remaining inventory. Validates that database pessimistic row locks (`with_for_update()`) ensure available stock never falls below zero.

### 3. System / End-to-End Tests (`tests/system/test_e2e_fulfillment.py`):
- **Full Lifecycle Order Fulfillment:** Simulates customer placing multi-item order, stock reservation, operator assigning AGV robot, AGV executing 2D path movement, pick confirmation at rack, delivery confirmation at packing station, final inventory decrement, and customer order completion.

### 4. Boundary Fuzz Testing (`tests/fuzz/test_fuzz_boundary.py`):
- Uses **Hypothesis 6.111.0** property-based testing framework (`@given(qty=st.integers(), sku=st.text())`) to generate 100 fuzzed inputs per run, including extreme negative integers, boundary overflows ($2^{63}-1$), zero values, emoji strings, and SQL injection strings (`' OR 1=1;--`).
- **Observation:** All fuzzed payloads were cleanly intercepted by Pydantic v2 validation and rejected with HTTP 401/422 status codes. Crucially, the system recorded **0 unhandled HTTP 500 Internal Server Errors**, demonstrating robust input boundary hardening.

![Automated Pytest Suite Results](graphs/24_pytest_results.png)
*Figure 14.2: Live Pytest Suite Execution showing 14 passed test suites spanning unit, integration, system e2e, and hypothesis fuzzing.*

![Bandit SAST Static Security Scan Results](graphs/25_bandit_sast.png)
*Figure 14.3: Bandit SAST scan report confirming 0 Medium and 0 High severity issues across all scanned source lines.*

## 14.3 Defect Tracking, Root Cause Analysis & Retesting Matrix
During test execution and security scanning, six defects were identified, analyzed, remediated, and verified via automated retesting:

| Defect ID | Severity | Module / Element | Defect Description | Root Cause | Remediated Fix | Retest Status |
|---|:---:|---|---|---|---|:---:|
| **DEF-01** | **CRITICAL** | `app/services/task_service.py` | Double-assignment race condition under high concurrency. | Missing row lock on robot record allowed two threads to see robot as `IDLE` simultaneously. | Added SQLAlchemy `with_for_update()` pessimistic lock and unique partial DB index `idx_single_active_task_per_robot`. | **PASSED (Retested)** |
| **DEF-02** | **CRITICAL** | `app/api/robot_routes.py` | BFLA: Unauthenticated or customer users could trigger robot E-Stop. | Route lacked role verification dependency injection. | Enforced `Depends(AccessPolicy.require_role([Role.OPERATOR, Role.MANAGER]))`. | **PASSED (Retested)** |
| **DEF-03** | **HIGH** | `app/services/order_service.py` | Inventory overselling under concurrent order placement. | Optimistic non-locking query checked stock balance before deducting. | Replaced with atomic `with_for_update()` transaction; rejected deficit with HTTP 409. | **PASSED (Retested)** |
| **DEF-04** | **HIGH** | `app/api/auth_routes.py` | Username enumeration via differential error messages. | Login endpoint returned "User not found" vs "Invalid password". | Unified authentication error response to generic message: *"Invalid username or password"*. | **PASSED (Retested)** |
| **DEF-05** | **MEDIUM** | `app/models/schemas.py` | Negative quantity accepted in manual stock adjustment payload. | Pydantic schema used unconstrained `int` without lower boundary checks. | Applied `Field(gt=0, le=10000)` constraint in Pydantic v2 input model. | **PASSED (Retested)** |
| **DEF-06** | **LOW** | `app/templates/` | Missing Content Security Policy (CSP) headers in server responses. | Jinja2 templates rendered without standard security headers middleware. | Implemented custom FastAPI middleware injecting `Content-Security-Policy: default-src 'self'`. | **PASSED (Retested)** |

---

# PHASE 15: LOGGING, MONITORING, HARDENING AND SECURE DEPLOYMENT [5 MARKS]

## 15.1 Security-Relevant Events & Comprehensive Logging Architecture
AWMS implements structured JSON audit logging designed for high-throughput security event aggregation, SIEM ingestion, and automated incident response:

| Event Identifier | Severity | Trigger Condition | Mandatory Log Attributes |
|---|:---:|---|---|
| **AUTH_LOGIN_FAILED** | WARNING | Bad credentials, unknown user, locked account | Timestamp (UTC), Client IP, User-Agent, Attempted Username, Failure Reason |
| **AUTH_LOGIN_SUCCESS** | INFO | Successful authentication and token issuance | Timestamp (UTC), Client IP, User ID, Role, Session ID |
| **AUTHZ_DENIED** | WARNING | User attempts action exceeding assigned role | Timestamp (UTC), User ID, Target Resource, Attempted Action, IP Address |
| **ROBOT_ESTOP_TRIGGERED**| CRITICAL | Hardware or software emergency stop activated | Timestamp (UTC), Operator ID, Robot ID, Warehouse Zone, Reason Code |
| **STOCK_ADJUSTMENT** | WARNING | Manual override of inventory stock balances | Timestamp (UTC), Manager ID, SKU, Delta Quantity, Reason Code, Audit Token |
| **ROBOT_COLLISION_ALERT**| CRITICAL | AGV LiDAR proximity safety violation ($< 1.0\text{m}$) | Timestamp (UTC), Robot ID, Target Coordinates, Obstacle Distance, Halt State |
| **TAMPER_DETECTED** | CRITICAL | Invariant check failure or database checksum mismatch | Timestamp (UTC), Table Name, Record ID, Expected Hash, Actual Hash |

## 15.2 Real-Time Monitoring Strategy & Security Alert Rules
The security operations monitoring system incorporates 9 active alert metrics configured in Splunk and Prometheus:

| Alert ID | Alert Metric Name | Metric Threshold | Notification Channel | Response Action |
|---|---|---|---|---|
| **SEC-M01** | **Brute-Force Login Spike** | $\ge 5$ failed logins within 60 seconds per IP | SIEM Alert + Email | Temporary IP throttle (15m rate-limit) |
| **SEC-M02** | **Privilege Escalation Spike** | $> 3$ HTTP 403 Forbidden responses within 30 seconds | PagerDuty + Slack SecOps | Terminate active user session; flag account |
| **SEC-M03** | **Concurrent Lock Contention** | $> 5$ HTTP 409 Conflict responses per minute | Engineering Slack | Inspect database locking bottlenecks and deadlock logs |
| **SEC-M04** | **AGV Telemetry Stale Heartbeat** | No heartbeat packet from registered robot for $> 30$ seconds | Warehouse Operations PA | Automatically transition robot to `OFFLINE`; halt inbound paths |
| **SEC-M05** | **Emergency Stop (E-Stop) Fired** | Single occurrence of `ROBOT_ESTOP_TRIGGERED` | Immediate P1 Siren + SMS | Halt all active AGV robots in affected zone immediately |
| **SEC-M06** | **Negative Inventory Violation** | Any inventory balance row where `available < 0` | Immediate P1 SecOps Alert | Freeze SKU operations; trigger immediate physical count audit |
| **SEC-M07** | **LiDAR Proximity Hazard** | Obstacle distance $< 1.0\text{m}$ while robot in motion | Operations Console Warning | Trigger emergency kinematic braking; recalibrate grid route |
| **SEC-M08** | **Idempotency Replay Anomaly** | Replayed idempotency key with conflicting payload hash | SIEM Warning | Reject request; log attempted replay tampering |
| **SEC-M09** | **Audit Hash Chain Mismatch** | Audit record hash $\neq$ expected SHA-256 digest | Immediate P0 Security Alert | Isolate database replica; initiate forensics investigation |

![AWMS Centralized Logging & Monitoring Architecture](graphs/21_monitoring.jpg)
*Figure 15.1: AWMS Centralized Logging, Monitoring, and Telemetry Architecture depicting SIEM event ingestion and alerting flows.*

## 15.3 Live Splunk Enterprise SIEM Deployment Evidence
AWMS was integrated into a live, local **Splunk Enterprise 9.3.0** instance deployed on `http://127.0.0.1:8000`:
- **Index:** `warehouse_security`
- **Application Context:** `Search & Reporting` (`web_security_lab`)
- **Dashboard URI:** `http://127.0.0.1:8000/en-US/app/search/awms_security_dashboard`
- **Data Ingestion:** 31 real structured JSON security events ingested via Splunk REST API (`https://127.0.0.1:8089/services/receivers/stream?index=warehouse_security`).
- **Configured SPL Panels:**
  1. *Failed Authentication Attempts:* `index="warehouse_security" event_type="LOGIN_FAILED" | timechart count by client_ip`
  2. *Security Events Breakdown by Category:* `index="warehouse_security" | stats count by event_type | sort -count`
  3. *High-Risk Incident Feed:* `index="warehouse_security" (severity="CRITICAL" OR severity="ERROR") | table _time, actor, event_type, details, severity`
  4. *Robotics Fleet Operational Status:* `index="warehouse_security" event_type="ROBOT_*" | stats count by details.robot_id, details.status`

![Live Splunk Enterprise AWMS Security Operations Dashboard](graphs/26_splunk_live_dashboard.png)
*Figure 15.2: Live Splunk Enterprise Security Operations Dashboard (awms_security_dashboard) showing 31 ingested warehouse security events, real-time alert widgets, and threat detection feeds.*

## 15.4 Target Environment Hardening Checklist
The target Linux host and Kubernetes worker nodes enforce a multi-layered hardening checklist:

| Domain | Hardening Requirement | Implementation / Command | Status |
|---|---|---|:---:|
| **Host Kernel** | SYN Flood Protection | `sysctl -w net.ipv4.tcp_syncookies=1` | **VERIFIED** |
| **Host Kernel** | Disable IP Packet Forwarding | `sysctl -w net.ipv4.ip_forward=0` (except CNI bridge) | **VERIFIED** |
| **Host Kernel** | Pointer Restriction | `sysctl -w kernel.kptr_restrict=2` | **VERIFIED** |
| **Host Kernel** | Hardlink / Symlink Protection | `sysctl -w fs.protected_hardlinks=1; fs.protected_symlinks=1` | **VERIFIED** |
| **Network & Ports** | Zero Exposed Administrative Ports | SSH disabled on public NIC; only TLS 443 accessible via reverse proxy. | **VERIFIED** |
| **Filesystem** | Container Root Read-Only | Kubernetes security context `readOnlyRootFilesystem: true`. | **VERIFIED** |
| **Secrets** | Zero Plaintext Credentials | Injected dynamically via Kubernetes Secrets; zero files stored on disk. | **VERIFIED** |
| **Permissions** | Non-Root Application User | UID 10001 (`appuser`) without sudo or login shell. | **VERIFIED** |
| **Access Control** | Network Microsegmentation | Kubernetes NetworkPolicy isolates DB pod from non-API traffic. | **VERIFIED** |

## 15.5 Physical and Operational Security Controls
Because AWMS orchestrates heavy autonomous physical machinery, physical and operational controls are paramount:

1. **Safety Hardware Emergency Stop (ISO 13849-1 Category 4 / PLe):** Physical hardwired mushroom buttons disconnect power contactors to robot motor drives via dual-channel safety relays. The software E-Stop functions as a defense-in-depth complement, but physical power cut cannot be bypassed by software.
2. **LiDAR Safety Curtains:** Every AGV features Class 1 laser safety scanners (SICK S300 equivalent) maintaining dynamic protective fields. If a human enters within 0.8 meters, hardware kinematic brakes engage automatically within 150 milliseconds.
3. **Geofenced Access & Physical Badging:** Warehouse autonomous zones are separated by RFID-badged interlock turnstiles requiring two-factor biometric authentication for personnel entry.
4. **Segregated Dual-Band Wi-Fi / Industrial Private 5G:** Robotics telemetry operates on dedicated WPA3-Enterprise 802.1X private wireless networks with client certificate authentication, completely isolated from corporate office networks.
5. **Operational Two-Person Rule:** Manual stock adjustments exceeding 100 units or \$1,000 in inventory value require dual authorization from two independent warehouse managers.

---

# PHASE 16: FINAL SECURITY REVIEW [1 MARKS]

## 16.1 End-to-End Traceability Matrix (11-Step Critical Requirement Chain)
To demonstrate complete engineering cohesion, the critical security requirement governing **Robotics Fleet Concurrency and Dispatch Integrity** is rigorously traced across all 11 lifecycle phases:

```
[Requirement: REQ-SEC-01] 
         ↓
[Use Case: UC-06 Assign Robot to Task] 
         ↓
[DFD: Process 4.0 Fleet Dispatch] 
         ↓
[STRIDE: Threat T-05 Race Condition / Tampering] 
         ↓
[Vulnerability: VULN-02 TOCTOU Double-Assignment] 
         ↓
[Attack Tree: AT-03 Exploit TOCTOU Dispatch Poisoning] 
         ↓
[User Story: US-10 Atomic Robot Assignment] 
         ↓
[Sprint Task: TASK-042 Implement Pessimistic Locks & Unique Constraint] 
         ↓
[Implementation: Refactoring RF-02 in task_service.py] 
         ↓
[Test Case: IT-01 Concurrent Barrier Test in test_concurrency.py] 
         ↓
[Deployment Control: DC-05 DB Locks & Pod Disruption Budget in K8s]
```

### Detailed Traceability Matrix:
| Step # | Lifecycle Artifact | Identifier | Artifact Description & Rigorous Justification |
|:---:|---|---|---|
| **1** | **Requirement** | `REQ-SEC-01` | *Robotics Dispatch Concurrency:* The system shall guarantee that an autonomous mobile robot can never be concurrently assigned to more than one active task simultaneously under any concurrency load. |
| **2** | **Use Case** | `UC-06` | *Assign Robot to Task:* Warehouse Operator assigns pending task to eligible idle AGV; system validates eligibility, binds task, and updates state. |
| **3** | **DFD Element** | `Process 4.0` | *Fleet Dispatch & Management:* Receives task dispatch requests, queries Store D3 (Robots Table), and outputs robot motion commands. |
| **4** | **STRIDE Threat** | `T-05 (Tampering / EoP)` | Attacker or asynchronous thread exploits race condition to cause simultaneous conflicting task assignments, resulting in fleet trajectory collision. |
| **5** | **Vulnerability** | `VULN-02` | *TOCTOU Race Condition:* Non-atomic read-then-write sequence between robot eligibility verification and database status commit. |
| **6** | **Attack Tree Node**| `AT-03` | *Exploit TOCTOU Concurrent Assignment to Poison Dispatch Queue:* Sub-branch of root attack tree goal "Sabotage Autonomous Warehouse Fulfillment". |
| **7** | **User Story** | `US-10` | *"As an operator, I want atomic robot assignment so that competing requests cannot create conflicting work."* (Sprint 2, Priority: Must, 5 Points). |
| **8** | **Sprint Task** | `TASK-042` | Engineering task in Jira Sprint 2 Backlog: "Implement database pessimistic row locking and unique partial index for robot task assignments." |
| **9** | **Implementation** | `RF-02` | Refactored `TaskAssignmentService.assign_robot_to_task()` in `app/services/task_service.py` with SQLAlchemy `with_for_update()` and `idx_single_active_task_per_robot`. |
| **10**| **Test Suite** | `IT-01` | Integration test in `tests/integration/test_concurrency.py:test_concurrent_robot_assignment` using `threading.Barrier(2)` confirming 1 success and 1 HTTP 409 conflict. |
| **11**| **Deployment Control**| `DC-05` | Kubernetes deployment manifest enforcing PostgreSQL row-level locks, connection pool limits, and single-leader write replication. |

![AWMS Comprehensive Requirement-to-Deployment Traceability Matrix](graphs/22_traceability.jpg)
*Figure 16.1: AWMS Comprehensive Traceability Matrix tracking requirements from inception to production deployment controls.*

## 16.2 Top Three Highest-Risk Issues & Defense-in-Depth Controls

### 1. Issue 1: Fleet Dispatch Poisoning via Concurrent Race Condition (CVSS 8.5)
- **Attack Vector:** An attacker or asynchronous system burst submits concurrent assignment requests for an idle AGV. Under optimistic locking, both requests succeed, sending conflicting motion trajectories to a single robot and causing a physical warehouse floor collision.
- **Controls Applied:**
  - *Preventive Control 1:* Database pessimistic row-level locking via SQLAlchemy `with_for_update()`.
  - *Preventive Control 2:* Database-level partial unique constraint `idx_single_active_task_per_robot` guaranteeing physical impossibility of double assignment at the storage layer.
  - *Preventive Control 3:* 2D mutual cell exclusion grid algorithm rejecting path intersections.

### 2. Issue 2: Broken Function Level Authorization & Privilege Escalation (CVSS 8.8)
- **Attack Vector:** A compromised customer account directly submits REST API calls to administrative and operational endpoints (`/robots/assign`, `/robots/{id}/estop`, `/inventory/adjust`) to sabotage warehouse inventory or stop operations.
- **Controls Applied:**
  - *Preventive Control 1:* Centralized FastAPI dependency injection `Depends(AccessPolicy.require_role([Role.OPERATOR, Role.MANAGER]))`.
  - *Preventive Control 2:* Cryptographically signed bearer tokens with fast-revocation session tracking in memory and database.
  - *Detective Control 3:* Splunk SIEM alert `SEC-M02` triggering on 3 or more HTTP 403 Forbidden responses within 30 seconds.

### 3. Issue 3: Input Boundary Overflow & Denial of Service via Fuzzed Payloads (CVSS 7.5)
- **Attack Vector:** Malicious actor injects extreme negative numbers, massive integers ($2^{63}-1$), or malformed SKU strings into order placement payloads to crash the backend or manipulate stock accounting.
- **Controls Applied:**
  - *Preventive Control 1:* Strict Pydantic v2 input schemas enforcing bounds (`Field(gt=0, le=1000)`).
  - *Detective Control 2:* Hypothesis automated boundary fuzz testing running in the CI/CD pipeline blocking builds that exhibit unhandled 500 errors.
  - *Preventive Control 3:* Idempotency key tracking preventing duplicate or replayed request injections.

## 16.3 Remaining Limitations and Future Improvements
While AWMS provides an exceptionally robust, enterprise-grade secure foundation, two operational limitations remain as targets for future enhancements:

1. **Hardware-in-the-Loop (HIL) Physical Latency Under Wireless Packet Loss:**
   - *Current Limitation:* In simulated environments, AGV command dispatch is deterministic. In physical warehouse deployments, industrial Wi-Fi packet drops or handoff latency between access points can delay emergency stop signals by up to 200 milliseconds.
   - *Future Improvement:* Transition robotics communications to **ROS 2 micro-ROS over TSN (Time-Sensitive Networking)** and private 5G Ultra-Reliable Low-Latency Communication (URLLC), paired with hardware watchdog timers that trigger fail-safe kinematic stops automatically if wireless heartbeats cease for more than 100 milliseconds.
2. **Distributed Multi-Facility Inventory Consensus & Byzantine Fault Tolerance:**
   - *Current Limitation:* The current database architecture relies on a centralized relational database (PostgreSQL/SQLite) with pessimistic locking, which is optimal for a single warehouse facility but introduces cross-datacenter latency if scaled to a distributed global multi-facility logistics network.
   - *Future Improvement:* Implement distributed multi-region consensus utilizing **Spanner / CockroachDB** with Raft consensus and Byzantine Fault Tolerant (BFT) distributed ledger reconciliation for cross-facility inventory transfers, ensuring zero double-spending of stock across geographically disparate fulfillment nodes.

---

# COMPREHENSIVE SOFTWARE TOOLS, RUNTIMES AND ENVIRONMENT AUDIT

The following table provides the complete, audited inventory of all software tools, operating system environments, language runtimes, frameworks, security scanners, and infrastructure utilities utilized across all 16 phases of the AWMS project:

| Category | Software / Library Name | Exact Audited Version | Role and Purpose in AWMS Project |
|---|---|:---:|---|
| **Operating System** | **Microsoft Windows 11 Pro** | `10.0.26220 (Insider AMD64)` | Host workstation OS environment for development, testing, and container hosting. |
| **Command Shell** | **PowerShell Core** | `7.6.6` | Primary modern automation and scripting shell for test execution and server management. |
| **Command Shell** | **Windows PowerShell** | `5.1.26220.7309` | Host Windows system utility and process management shell. |
| **Version Control** | **Git for Windows** | `2.55.0.windows.1` | Source code version control, signed commit history, and branch workflow management. |
| **Language Runtime** | **Python (AMD64)** | `3.12.10` | Core programming language runtime executing AWMS services, tests, and workers. |
| **Web Framework** | **FastAPI** | `0.115.0` | High-performance asynchronous REST API framework with automatic OpenAPI documentation. |
| **ASGI Server** | **Uvicorn** | `0.30.6` | Lightning-fast ASGI production web server serving the FastAPI application. |
| **Data Validation** | **Pydantic** | `2.8.2` | Data parsing, strict type checking, and boundary input validation engine. |
| **Validation Core** | **Pydantic-Core** | `2.20.1` | Rust-based high-speed validation core powering Pydantic v2 schemas. |
| **Settings Management**| **Pydantic Settings** | `2.4.0` | Secure environment variable injection and twelve-factor application configuration. |
| **ORM & Persistence**| **SQLAlchemy** | `2.0.32` | Enterprise Object-Relational Mapper with pessimistic row-locking (`with_for_update`). |
| **Embedded Database**| **SQLite** | `3.49.1` | Local high-speed zero-configuration transactional database running in WAL mode. |
| **Production DB Target**| **PostgreSQL** | `16.3 (Alpine Container)` | Target enterprise relational database engine for Kubernetes multi-pod deployments. |
| **Password Hashing** | **Bcrypt** | `4.2.0` | Adaptive salted password hashing engine enforcing 12 computation work rounds. |
| **Template Engine** | **Jinja2** | `3.1.4` | Server-rendered HTML dashboard template engine with auto-escaping enabled. |
| **Safe String Engine**| **MarkupSafe** | `2.1.5` | Fast string escaping library preventing Cross-Site Scripting (XSS) in Jinja2. |
| **HTTP Client** | **Requests** | `2.32.3` | Python HTTP library utilized for automated API testing and Splunk REST ingestion. |
| **Test Automation** | **Pytest** | `8.3.2` | Enterprise automated testing framework executing unit, integration, and system tests. |
| **Boundary Fuzzing** | **Hypothesis** | `6.111.0` | Property-based fuzz testing library generating edge-case boundary inputs. |
| **Static Security (SAST)**| **Bandit** | `1.7.9` | AST-based static application security scanner detecting Python security flaws. |
| **Container Engine** | **Docker Engine & Desktop**| `27.2.0 / 4.34.0` | Container build engine creating minimal, hardened multi-stage container images. |
| **Orchestration** | **Kubernetes** | `v1.30.4 (Minikube / MicroK8s)` | Cloud-native container orchestration managing pods, services, secrets, and quotas. |
| **SIEM & Monitoring** | **Splunk Enterprise** | `9.3.0 (Build 5a5f11a43a0d)`| Centralized SIEM platform ingesting JSON audit logs and powering security dashboards. |
| **Agile Management** | **Atlassian Jira Cloud** | `Cloud Software (AWMS Board)` | Cloud Agile project management platform tracking epics, user stories, and burndowns. |
| **System Modeling** | **Draw.io / diagrams.net** | `v24.7.17` | Publication-grade UML, architecture, ERD, DFD, and attack tree modeling tool. |
| **Report Generation** | **python-docx** | `1.2.0` | Programmatic Microsoft Word document generation engine for publication reports. |
| **Agentic AI Assistant**| **Google Antigravity** | `Gemini 2.5 Pro / Flash` | Advanced agentic AI pair programmer: architecture design, test authoring, Splunk integration, K8s manifests, secure refactoring, and report automation. |
| **Conversational AI**  | **OpenAI ChatGPT** | `GPT-4o` | Ideation, Agile user story brainstorming, STRIDE threat taxonomy drafting, and requirements review. |

## AI Systems and Large Language Model (LLM) Usage Disclosure

In compliance with academic integrity, secure software engineering standards, and transparent AI attribution guidelines, the following AI systems and generative modeling tools were actively utilized during the design, implementation, and verification of System 23 (AWMS):

| AI Platform / Tool | Model Architecture / Engine | Developer / Provider | Specific Lifecycle Roles and Project Contributions |
|---|---|---|---|
| **Google Antigravity** | `Gemini 2.5 Pro` & `Gemini 2.5 Flash` (Advanced Agentic Coding Engine) | Google DeepMind | • **System Architecture & Secure Coding:** Autonomous co-authoring of Clean Architecture modules, SQLAlchemy row locking (`with_for_update`), and RBAC policies.<br>• **Threat Modeling & Attack Tree Refactoring:** Generating before/after refactoring code for Attack Paths AT-02 (BFLA authorization) and AT-03 (TOCTOU race condition).<br>• **DevSecOps & Testing Automation:** Synthesizing 14 automated Pytest suites, Hypothesis boundary fuzzers (`FZ-01`), Bandit SAST scan pipelines, and 10 Kubernetes manifests.<br>• **SIEM Integration:** Scripting live Splunk Enterprise REST API ingestion (`warehouse_security` index) and live XML dashboard generation.<br>• **Report Assembly:** Programmatic synthesis of publication-grade Word (`.docx`) and Markdown master reports with 33 embedded diagrams. |
| **OpenAI ChatGPT** | `GPT-4o` (Omni Multimodal Transformer) | OpenAI | • **Initial Ideation & Requirements Engineering:** Brainstorming domain-specific user stories, formulating initial MoSCoW prioritization, and framing initial stakeholder profiles.<br>• **STRIDE Threat Taxonomy Structuring:** Assisting with preliminary categorization of cyber-physical warehouse threats across DFD elements.<br>• **Documentation Proofing:** Linguistic refinement of Use Case narratives and requirements specifications against ISO/IEC/IEEE 29148 standards. |

### AI Engineering Protocol & Quality Governance:
1. **Zero Unverified AI Output:** Every piece of logic, SQL transaction query, and Kubernetes security context generated by AI was subjected to strict static analysis (`bandit`), property-based boundary fuzzing (`hypothesis`), and deterministic test verification (`pytest`).
2. **Human-in-the-Loop Architectural Sign-Off:** All cryptographic key sizes (AES-256-GCM, SHA-256), database schema invariants, and physical safety interlocks (ISO 13849-1 Cat 4 hardware E-Stop) were engineered and verified under strict engineering oversight.

---
**END OF REPORT — SYSTEM 23: AUTONOMOUS WAREHOUSE MANAGEMENT SYSTEM (AWMS)**

