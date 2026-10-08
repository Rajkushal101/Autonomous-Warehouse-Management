"""
phase1_to_4.py
Builds Phase 1 to Phase 4 for the Final Examination Report.
"""

def get_markdown_phase1_to_4():
    return """# 24CYS401: SECURE SOFTWARE ENGINEERING LABORATORY END SEMESTER EXAMINATION
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
In alignment with the laboratory examination mapping instruction (*Student $\rightarrow$ Customer*, *Faculty $\rightarrow$ Warehouse Manager / Operator*, *Administrator $\rightarrow$ System Administrator*), the following actors interact with the Autonomous Warehouse Management System:

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
  4. System transitions task state: `QUEUED` $\rightarrow$ `ASSIGNED`, and robot status `IDLE` $\rightarrow$ `BUSY`.
  5. System computes collision-free waypoint path steps using grid BFS algorithm.
  6. Robot receives step-by-step navigation commands, transmitting telemetry heartbeats and location updates.
  7. Robot reaches storage shelf, executes pick maneuver, and transitions state to `PICKING` $\rightarrow$ `TO_DROP`.
  8. Robot navigates to packing bay and deposits tote.
  9. System confirms delivery, decrements stock at shelf, increments stock at packing bay, and appends to `inventory_movements`.
  10. Task transitions to `COMPLETED`; robot transitions to `IDLE`.
- **Alternative / Exception Flows:**
  - *2a. Robot Stale Heartbeat:* Robot heartbeat > 30s; marked `OFFLINE`; task remains `QUEUED` for alternative AGV.
  - *5a. Dynamic Obstacle Detected:* Peer robot blocks path; pathfinder recalculates alternate route; if deadlocked, state transitions to `BLOCKED`.
- **Postconditions:** Physical tote delivered to packing bay; inventory movement permanently ledgered; task completed.

## 3.3 Scenario-Based Analysis Model for 'Attend Examination & Submit Answers' (Mapped to Fulfillment Pipeline)
In alignment with the examination problem mapping (*"Attend Examination and Submit Answers"* $\rightarrow$ *"Place Order, Allocate Inventory & Execute Robotic Fulfillment"*), the scenario analysis model decomposes the behavioral lifecycle into boundary, controller, and entity interactions:
1. **Boundary Objects:** `OrderFormBoundary`, `BarcodeScannerBoundary`, `RobotTelemetryStream`.
2. **Controller Objects:** `OrderLifecycleController`, `InventoryAllocationController`, `RobotDispatchController`.
3. **Entity Objects:** `OrderEntity`, `InventoryBalanceEntity`, `RobotEntity`, `MovementLedgerEntity`, `AuditEventEntity`.
4. **Behavioral Sequence & Activity Modeling:**
   - Client authenticates $\rightarrow$ Submits order with idempotency token.
   - Controller locks inventory rows $\rightarrow$ Verifies available balance $\rightarrow$ Creates reservation.
   - Dispatcher assigns idle AGV $\rightarrow$ Robot executes waypoint steps $\rightarrow$ Deposits tote at packing bay.
   - Packing bay verifies barcode $\rightarrow$ Double-entry physical movement recorded $\rightarrow$ Order marked `FULFILLED`.

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
"""

def add_docx_phase1_to_4(doc):
    add_heading_styled(doc, "PHASE 1: AGILE PROCESS AND DEVELOPMENT APPROACH [6 MARKS]", level=1)
    doc.add_paragraph(
        "For developing the Autonomous Warehouse Management System (AWMS - System 23), a hybrid framework combining Scrum management rituals "
        "with Extreme Programming (XP) technical engineering practices was selected. This approach pairs two-week iterative delivery "
        "with strict engineering disciplines: Test-Driven Development (TDD), Continuous Integration (CI), automated static security analysis (Bandit), "
        "and disciplined code refactoring."
    )
    
    add_heading_styled(doc, "1.1 Agile Manifesto Principles Mapping", level=2)
    manifesto_data = [
        ("1", "Early and continuous delivery of valuable software", "Delivering a functioning order reservation loop in Sprint 1 allows warehouse operators to validate stock integrity before robot dispatching is connected in Sprint 2."),
        ("2", "Welcome changing requirements, even late in development", "When warehouse shelving layouts or robot collision tolerances change, data models and collision validators are updated in isolated modules."),
        ("3", "Deliver working software frequently", "Delivering two working software increments: Increment 1 proves transactional reservation; Increment 2 delivers automated robot task orchestration."),
        ("4", "Business people and developers work together daily", "Fulfillment managers and software engineers continuously review business constraints to prevent inventory overselling."),
        ("7", "Working software is the primary measure of progress", "Progress is measured strictly by passing automated tests (IT-01 verifying concurrency locks, ST-01 end-to-end fulfillment) rather than merely documented design diagrams."),
        ("8", "Continuous attention to technical excellence enhances agility", "Employing Layered Monolithic architecture, Unit of Work, Command Pattern, and automated static security gates prevents technical debt.")
    ]
    add_table_styled(doc, ["#", "Agile Principle", "Concrete Project Application"], manifesto_data)
    
    add_heading_styled(doc, "1.2 Two Refactoring Opportunities (RF-01 & RF-02)", level=2)
    doc.add_paragraph(
        "Refactoring 1 (RF-01): Centralized Authorization & Strict Schema Validation. The initial route handler accepted raw unvalidated JSON "
        "and executed database updates without inspecting user roles, allowing unprivileged customers to command robots. "
        "The refactored code introduces Pydantic v2 schemas and centralized AccessPolicy.require_role() deny-by-default role checks."
    )
    doc.add_paragraph(
        "Refactoring 2 (RF-02): Atomic Transaction Locking & Concurrency Protection. The initial version executed an unlocked read-then-write "
        "window allowing two competing requests to assign the same idle robot to two tasks simultaneously. The refactored code enforces "
        "PostgreSQL/SQLite row-level locks (with_for_update()) and a database partial unique index guaranteeing exactly one active task per robot."
    )
    
    add_heading_styled(doc, "1.3 Limitations/Risks of Agile for Security-Critical Systems", level=2)
    risk_data = [
        ("R1", "Velocity pressure compromising security controls", "Security-baked Definition of Done (DoD) requiring 100% test pass rate and 0 Bandit findings before any story transitions to DONE."),
        ("R2", "Incremental design drift causing architectural flaws", "Version-controlled STRIDE threat modeling & DFD trust boundary models reviewed on every schema change."),
        ("R3", "Single developer / lab timebox constraints", "Standardized canonical IDs (FR, SR, UC, T, US, DEF) and clean modular architecture enabling rapid, verifiable implementation.")
    ]
    add_table_styled(doc, ["#", "Agile Risk", "Project Mitigation Strategy"], risk_data)

    doc.add_page_break()
    add_heading_styled(doc, "PHASE 2: REQUIREMENTS ENGINEERING [7 MARKS]", level=1)
    doc.add_paragraph(
        "In alignment with the laboratory examination mapping instruction (Student -> Customer, Faculty -> Warehouse Manager / Operator, "
        "Administrator -> System Administrator), system stakeholders and user types were formally specified. "
        "The system captures 18 Functional Requirements (FR-01 to FR-18), 8 Non-Functional Requirements (NFR-01 to NFR-08), "
        "and 13 Security Requirements (SR-01 to SR-13)."
    )
    
    srs_summary_data = [
        ("FR-01", "Identity & Session", "Must", "Confidentiality & Integrity", "Opaque session token; bcrypt password hashing; logout revokes session."),
        ("FR-02", "Role-Based Access Control", "Must", "Integrity", "Strict deny-by-default RBAC; non-admin role escalation blocked with HTTP 403."),
        ("FR-03", "Product Catalog Registry", "Must", "Integrity", "Unique SKU, positive weight bounds (> 0), active status validation."),
        ("FR-04", "Grid Location Registry", "Must", "Integrity & Availability", "Discrete 10x10 coordinate bounds; obstacle cell validation."),
        ("FR-05", "Inventory Balances", "Must", "Integrity", "Available stock = on_hand - reserved >= 0; conservation invariant holds."),
        ("FR-06", "Robot Device Registration", "Must", "Integrity & Availability", "Unique serial, payload capacity, battery status, hashed bearer token."),
        ("FR-07", "Idempotent Orders", "Must", "Integrity", "UUIDv4 idempotency key prevents duplicate orders and double reservation."),
        ("FR-08", "Atomic Stock Reservation", "Must", "Integrity", "ACID row locks (SELECT FOR UPDATE); all-or-none atomic reservation."),
        ("FR-09", "Task Creation & Dispatch", "Must", "Integrity & Availability", "Only Operator/Manager can assign tasks to eligible idle robots."),
        ("FR-10", "Task Execution & Delivery", "Must", "Integrity", "Sequential pickup, transit, and packing bay drop with movement ledgering."),
        ("FR-11", "Robot Telemetry & Heartbeat", "Must", "Availability", "Live heartbeat tracking; robots silent > 30s transition to OFFLINE."),
        ("FR-12", "Collision Prevention", "Must", "Integrity & Availability", "Mutual cell exclusion on 10x10 grid; swap maneuvers rejected."),
        ("FR-13", "Emergency Stop & Pause", "Must", "Availability & Integrity", "Hardware E-Stop halts all active robots within 200 milliseconds."),
        ("FR-14", "Fulfillment Results", "Must", "Confidentiality & Integrity", "Strict IDOR defense; customers view only own orders; managers view global."),
        ("FR-15", "Cryptographic Audit Trail", "Must", "Integrity & Repudiation", "Append-only SHA-256 block-chained ledger with previous_hash linking."),
        ("FR-16", "Health & Telemetry Metrics", "Must", "Availability", "Endpoints /health/live and /health/ready; SIEM telemetry streaming."),
        ("NFR-01", "Performance Latency", "Must", "Availability", "Read API latency under 500 ms at p95 under standard laboratory load."),
        ("NFR-02", "ACID Concurrency", "Must", "Integrity", "Strict row locks preventing overselling under concurrent requests."),
        ("SR-01", "Password & Session Security", "Must", "Confidentiality & Integrity", "Bcrypt hashing (cost 12); 256-bit opaque tokens stored as SHA-256 digests."),
        ("SR-04", "Atomic Task Assignment", "Must", "Integrity & Availability", "Database partial unique index prevents multi-task assignment to one robot."),
        ("SR-06", "Audit Ledger Protection", "Must", "Integrity & Repudiation", "Tamper-evident SHA-256 chaining; zero application-level DELETE privileges.")
    ]
    add_table_styled(doc, ["Req ID", "Requirement Name", "Priority", "CIA Classification", "Acceptance Criteria"], srs_summary_data)

    doc.add_page_break()
    add_heading_styled(doc, "PHASE 3: REQUIREMENTS ANALYSIS AND UML [7 MARKS]", level=1)
    doc.add_paragraph(
        "Behavioral modeling decomposes the system into actors, use cases, include/extend relationships, and activity flows. "
        "The system specifies 9 major use cases (UC-01 to UC-09) and formalizes two critical use cases: UC-04 (Order Placement & Stock Reservation) "
        "and UC-06 (Robot Dispatch & Fulfillment Task Execution)."
    )
    
    add_image_safe(doc, "01_use_case.jpg", "Figure 3.1: AWMS Comprehensive UML Use Case Diagram showing actors and operational boundaries.", 5.5)
    add_image_safe(doc, "02_activity.jpg", "Figure 3.2: UML Activity Diagram detailing the end-to-end robotic fulfillment workflow.", 5.5)

    doc.add_page_break()
    add_heading_styled(doc, "PHASE 4: DATA AND INFORMATION FLOW MODELING [7 MARKS]", level=1)
    doc.add_paragraph(
        "The data architecture was modeled using a normalized Entity-Relationship Diagram (14 entities) and decomposed into "
        "Context Level-0 and Level-1 Data Flow Diagrams with explicit Trust Boundaries (TB-01 External Web Perimeter, "
        "TB-02 Application-to-Database Boundary, TB-03 Machine Control Trust Boundary)."
    )
    
    add_image_safe(doc, "03_erd.jpg", "Figure 4.1: AWMS Relational Entity-Relationship Diagram (14 Entities).", 5.5)
    add_image_safe(doc, "04_dfd_0.jpg", "Figure 4.2: Context Level-0 Data Flow Diagram showing system perimeter.", 5.4)
    add_image_safe(doc, "05_dfd_1.jpg", "Figure 4.3: Decomposed Level-1 Data Flow Diagram illustrating processes, data stores, and trust boundaries.", 5.5)
