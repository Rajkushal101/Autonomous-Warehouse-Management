"""
phase5_to_8.py
Builds Phase 5 to Phase 8 for the Final Examination Report.
Includes complete Refactoring Code linked to the Attack Tree in Phase 8.
"""

def get_markdown_phase5_to_8():
    return """# PHASE 5: SOFTWARE ARCHITECTURE AND DESIGN ENGINEERING [7 MARKS]

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
3. **Finite State Machine Pattern (AGV Navigation & Lifecycle):** Formally models robotic state transitions (`IDLE` $\rightarrow$ `ASSIGNED` $\rightarrow$ `MOVING_TO_PICK` $\rightarrow$ `PICKING` $\rightarrow$ `MOVING_TO_BAY` $\rightarrow$ `UNLOADING` $\rightarrow$ `CHARGING`). Ensures fail-safe latching upon `EMERGENCY_STOP`.
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
In compliance with the examination mapping (*Screen 1: Login*, *Screen 2: Student Exam Screen $\rightarrow$ Customer Orders & Inventory*, *Screen 3: Faculty Exam Management $\rightarrow$ Fleet Operations & 10×10 Grid*, *Screen 4: Results $\rightarrow$ Order Fulfillment & Audit Ledger*), six responsive web interfaces were implemented on `http://127.0.0.1:8080`:

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

### Screen 2: Student Exam Screen $\rightarrow$ Customer Orders & Inventory (`/web/inventory`, `/web/orders`)
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

### Screen 3: Faculty Exam Management $\rightarrow$ Fleet Operations & 10×10 Grid (`/web/operations`)
- **User:** Warehouse Operator and Warehouse Manager.
- **Goal:** Monitor real-time AGV telemetry, visualize 10×10 floor grid, execute emergency overrides.
- **Navigation:** Direct access from top bar; restricted from Customer role.
- **Inputs:** Robot dispatch triggers, grid waypoint inspections, Hardware Emergency Stop (E-Stop) button.
- **Feedback:** Real-time AGV position updates `(x, y)`, live battery gauges, flashing amber warning on obstruction, bright red on E-Stop.
- **Error Handling:** Grid bounds clamping ($0 \le x \le 9, 0 \le y \le 9$), collision interlock alerts.
- **Security Considerations:** Centralized `AccessPolicy.require_role([OPERATOR, MANAGER])`, immediate motor power cutoff.

![Live UI: Robot Operations & Floor Grid](graphs/Screenshot 2026-10-08 132142.png)
*Figure 6.4: Live Production Screenshot of Robot Operations (`/web/operations`) featuring the 10×10 visual grid and Hardware E-Stop.*

### Screen 4: Results $\rightarrow$ Order Fulfillment & Cryptographic Audit Ledger (`/web/results`, `/web/audit`)
- **User:** Customer (view fulfillment result), Security Auditor & Manager (inspect audit trail).
- **Goal:** Track multi-step order delivery progress and cryptographically verify ledger integrity.
- **Navigation:** Direct navigation tabs from sidebar.
- **Inputs:** Barcode scanner simulation trigger, "Verify Chain Integrity" audit button.
- **Feedback:** 4-step fulfillment progress stepper (Order Placed $\rightarrow$ Reserved $\rightarrow$ Transport $\rightarrow$ Staged), green verification confirmation banner.
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
1. **Asset 1: User Passwords & Session Tokens:** Traverses from Browser $\rightarrow$ TLS 1.3 Envelope $\rightarrow$ API Gateway $\rightarrow$ `AuthService` (Bcrypt Hash Verification) $\rightarrow$ In-memory Context. Plaintext passwords never reach disk or logs.
2. **Asset 2: Inventory Allocation & Balances:** Traverses from Customer Order Request $\rightarrow$ Input Sanitizer $\rightarrow$ Transaction Manager $\rightarrow$ Database Row Lock (`SELECT FOR UPDATE`) $\rightarrow$ Immutable Ledger Commit.
3. **Asset 3: AGV Dispatch Waypoint Coordinates:** Traverses from `TaskAssignmentService` $\rightarrow$ BFS Grid Pathfinder $\rightarrow$ Sequenced `Command` $\rightarrow$ Authenticated Robot Wireless Channel $\rightarrow$ Robot Embedded Controller.

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
In compliance with the examination instruction mapping (*"modifying another student's marks / accessing question papers"* $\rightarrow$ *"unauthorized stock adjustment or unauthorized robot command manipulation"*), the root attacker goal is selected as:

$$\mathbf{AT-00}: \text{Cause an unauthorized or conflicting robot movement that corrupts warehouse fulfillment or enables stock theft}$$

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
- **Path 1: Credential Brute-Force & Session Hijack (AT-00 $\rightarrow$ AT-01 $\rightarrow$ AT-11 $\rightarrow$ AT-111 $\rightarrow$ AT-12):** Throttled by Bcrypt work factor 12 and IP rate limiting (max 5 failed attempts per 5 minutes); detected via automated `LOGIN_FAILED` audit events.
- **Path 2: Broken Object-Level & Role Authorization (AT-00 $\rightarrow$ AT-02 $\rightarrow$ AT-21 $\rightarrow$ AT-22):** Prevented by centralized `AccessPolicy.require_role([OPERATOR, MANAGER])`; detected by HTTP 403 audit logging.
- **Path 3: Concurrent Assignment Race Condition (AT-00 $\rightarrow$ AT-03 $\rightarrow$ AT-31 $\rightarrow$ AT-32):** Prevented by database row locks (`SELECT FOR UPDATE`) and database partial unique constraint; detected by conflict monitoring.
- **Path 4: Rogue Device Telemetry Injection (AT-00 $\rightarrow$ AT-04 $\rightarrow$ AT-41 $\rightarrow$ AT-412 $\rightarrow$ AT-42):** Prevented by high-entropy device tokens stored as SHA-256 digests and monotonic command sequence checking; detected by replay rejection.

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

### Refactoring Linked to Attack Path 2 (AT-02: Direct Authorization Bypass $\rightarrow$ RF-01)
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

### Refactoring Linked to Attack Path 3 (AT-03: Concurrency Race Condition $\rightarrow$ RF-02)
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
"""

def add_docx_phase5_to_8(doc):
    doc.add_page_break()
    add_heading_styled(doc, "PHASE 5: SOFTWARE ARCHITECTURE AND DESIGN ENGINEERING [7 MARKS]", level=1)
    doc.add_paragraph(
        "AWMS implements a four-tiered Clean Architecture enforcing strict separation of concerns: Domain Layer (pure business rules), "
        "Application Layer (workflow orchestration), Repository Layer (SQLAlchemy persistence with row-level locks), and Presentation Layer "
        "(FastAPI REST controllers and Jinja2 responsive templates). Four core design patterns are applied: Repository Pattern, "
        "Unit of Work, Finite State Machine, and Command Pattern."
    )
    
    add_image_safe(doc, "06_architecture.jpg", "Figure 5.1: AWMS Layered Clean Architecture enforcing unidirectional dependency rules.", 5.4)
    add_image_safe(doc, "14_components.jpg", "Figure 5.2: AWMS Component Architecture depicting modular service boundaries.", 5.4)
    add_image_safe(doc, "15_state_machine.jpg", "Figure 5.3: AGV Robot Finite State Machine Diagram.", 5.2)

    doc.add_page_break()
    add_heading_styled(doc, "PHASE 6: USER INTERFACE DESIGN [5 MARKS]", level=1)
    doc.add_paragraph(
        "In compliance with the examination mapping, four primary screens were implemented adhering to Shneiderman's Golden Rules: "
        "Screen 1 (Login), Screen 2 (Student Exam Screen -> Customer Orders & Inventory), Screen 3 (Faculty Exam Management -> Fleet Operations & 10x10 Grid), "
        "and Screen 4 (Results -> Order Fulfillment & Cryptographic Audit Ledger)."
    )
    
    add_image_safe(doc, "Screenshot 2026-10-08 132134.png", "Figure 6.1: Live Screenshot of Secure Login (/web/login).", 5.4)
    add_image_safe(doc, "Screenshot 2026-10-08 132127.png", "Figure 6.2: Live Screenshot of Inventory Balances (/web/inventory).", 5.4)
    add_image_safe(doc, "Screenshot 2026-10-08 132157.png", "Figure 6.3: Live Screenshot of Customer Orders Portal (/web/orders).", 5.4)
    add_image_safe(doc, "Screenshot 2026-10-08 132142.png", "Figure 6.4: Live Screenshot of Robot Operations & 10x10 Grid (/web/operations).", 5.4)
    add_image_safe(doc, "Screenshot 2026-10-08 132150.png", "Figure 6.5: Live Screenshot of Order Fulfillment Workflow (/web/results).", 5.4)
    add_image_safe(doc, "Screenshot 2026-10-08 132205.png", "Figure 6.6: Live Screenshot of Cryptographic Audit Trail (/web/audit).", 5.4)

    doc.add_page_break()
    add_heading_styled(doc, "PHASE 7: THREAT MODELING AND SECURITY ANALYSIS [10 MARKS]", level=1)
    doc.add_paragraph(
        "Threat modeling evaluated 10 cataloged system assets (A01 to A10) against STRIDE categories across Level-1 DFD boundaries. "
        "Fourteen concrete threats (T01 to T14) and eight vulnerabilities (V01 to V08) were analyzed, and Information Flow Analysis was "
        "conducted for passwords, inventory allocations, and robot dispatch waypoints."
    )
    
    add_image_safe(doc, "23_stride.jpg", "Figure 7.1: STRIDE Threat Model Matrix and Risk Treatment Classification.", 5.4)
    add_image_safe(doc, "16_sensitive_flow.jpg", "Figure 7.2: Sensitive Data Flow Boundaries illustrating cryptographic envelopes.", 5.4)

    doc.add_page_break()
    add_heading_styled(doc, "PHASE 8: ATTACK TREE AND SECURITY ARCHITECTURE REFINEMENT [6 MARKS]", level=1)
    doc.add_paragraph(
        "The critical root attacker goal AT-00 ('Cause unauthorized or conflicting robot movement / stock theft') was analyzed using AND/OR relationships. "
        "Four root-to-leaf attack paths were identified and mitigated. The security architecture was refined from Architecture v1 to Architecture v2."
    )
    
    add_image_safe(doc, "11_attack_tree.jpg", "Figure 8.1: Attack Tree Diagram for AGV Fleet Compromise and Inventory Race Condition Theft.", 5.4)
    add_image_safe(doc, "12_secure_architecture.jpg", "Figure 8.2: AWMS Secure Zero-Trust Defense-in-Depth Architecture (Architecture v2).", 5.4)
    
    add_heading_styled(doc, "8.1 Refactoring Code Linked to Attack Tree Paths", level=2)
    doc.add_paragraph(
        "To sever Attack Path 2 (AT-02: Direct Authorization Bypass) and Attack Path 3 (AT-03: Concurrent Assignment Race Condition), "
        "two concrete code refactorings were implemented in the codebase:"
    )
    
    add_heading_styled(doc, "Refactoring RF-01 (Severing AT-02 via AccessPolicy)", level=3)
    add_code_block(doc, 
        "# BEFORE (Vulnerable): Route directly assigned tasks without role check\n"
        "def assign_task_vulnerable(payload, db):\n"
        "    robot.status = 'BUSY'; task.state = 'ASSIGNED'; db.commit()\n\n"
        "# AFTER (Secure): Centralized AccessPolicy enforces deny-by-default\n"
        "AccessPolicy.require_role(current_user, [Role.OPERATOR, Role.MANAGER], db=db)\n"
        "return TaskAssignmentService.assign_robot_to_task(db, current_user, ...)"
    )
    
    add_heading_styled(doc, "Refactoring RF-02 (Severing AT-03 via with_for_update Row Locking)", level=3)
    add_code_block(doc,
        "# BEFORE (Vulnerable): Unlocked read-then-write creates TOCTOU race window\n"
        "robot = db.query(Robot).filter_by(id=robot_id).first()\n"
        "if robot.status == 'IDLE': robot.status = 'BUSY'; db.commit()\n\n"
        "# AFTER (Secure): Exclusive row lock and partial unique index\n"
        "robot = db.query(Robot).filter(Robot.id == robot_id).with_for_update().first()\n"
        "if robot.status != 'IDLE': raise WarehouseSecurityException(status_code=409)\n"
        "task.robot_id = robot.id; robot.status = 'BUSY'; db.commit()"
    )
