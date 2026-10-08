# Phase 2: Requirements Engineering & SRS Document

**Course:** 24CYS401 – Secure Software Engineering  
**System:** 23. Autonomous Warehouse Management System  
**Document Ref:** `docs/02_srs.md`  
**Marks:** 7  

---

## 1. Stakeholders and User Roles

In alignment with the general instruction mapping (Student → Customer, Faculty → Warehouse Manager / Operator, Administrator → System Administrator), the following actors interact with the Autonomous Warehouse Management System:

| Actor ID | Role Name | System Responsibility & Scope | Security Constraints |
|---|---|---|---|
| **ACT-01** | **Customer** | Submits product orders, inspects personal order fulfillment status, cancels eligible unpicked orders. | Restricted to own data (Strict IDOR prevention). Zero access to inventory balances, robot controls, or audit logs. |
| **ACT-02** | **Warehouse Operator** | Monitors real-time robot operations, views operational inventory, requests task assignments, initiates operational pause/resume. | Cannot alter user roles, perform arbitrary inventory quantity adjustments, or bypass movement validation. |
| **ACT-03** | **Warehouse Manager** | Configures warehouse catalog (products, locations), performs authorized stock adjustments with mandatory reason codes, inspects fulfillment analytics. | Cannot assign system administrator roles or delete audit records. |
| **ACT-04** | **System Administrator** | Manages human accounts and role assignments, revokes compromised sessions, rotates device tokens, inspects container and cluster health. | Administrative privileges do not bypass physical invariant checks (e.g., cannot force an occupied cell movement). |
| **ACT-05** | **Security Auditor** | Reviews immutable security audit events, evaluates access logs, verifies compliance and incident trails. | Read-only access to audit records; zero operational mutation authority. |
| **ACT-06** | **Robot Device (AGV)** | Authenticates via device-specific token, receives step-by-step navigation commands, transmits heartbeat telemetry and task step acknowledgments. | Machine identity only. Bound strictly to its own assigned tasks; cannot impersonate other robots. |
| **ACT-07** | **Dispatcher Worker** | Background daemon executing internal path step generation and coordinating task queues under transaction locks. | Runs as restricted internal service identity. |

---

## 2. Requirements Categorization & CIA Classification

The system requirements are classified according to the CIA Triad (Confidentiality, Integrity, Availability) alongside specific security focus areas (Authentication, Authorization, Audit, Input Validation, Concurrency Control):

### 2.1 Functional Requirements (FR) Summary
- **FR-01 to FR-02 (Identity & Access):** Secure session lifecycle, password protection, and administrative role assignment. *(CIA: Confidentiality & Integrity)*
- **FR-03 to FR-05 (Catalog & Inventory):** Unique product SKUs, bounded grid locations, and real-time inventory balances with available vs. reserved calculations. *(CIA: Integrity)*
- **FR-06 to FR-08 (Robots & Orders):** Robot registration with hashed tokens, idempotent order creation, and all-or-none atomic stock reservation. *(CIA: Integrity & Availability)*
- **FR-09 to FR-12 (Orchestration & Movement):** Atomic task assignment, collision-safe step movements, heartbeat monitoring, and prevention of command conflicts. *(CIA: Integrity & Availability)*
- **FR-13 to FR-16 (Operations & Observability):** Operational pause/stop, customer fulfillment result visibility, append-only security audit trail, and health/readiness probes. *(CIA: All)*
- **FR-17 to FR-18 (Search & Export):** Inventory filtering and CSV export. *(CIA: Availability)*

### 2.2 Non-Functional Requirements (NFR) Summary
- **NFR-01 (Performance):** Read API latency < 500 ms at p95 under standard lab load conditions.
- **NFR-02 (ACID Concurrency):** Database transactions enforce strict row locks preventing double-allocation and overselling.
- **NFR-03 (Fault Tolerance):** Dispatcher worker crashes leave durable database state; task resume succeeds without stock loss.
- **NFR-04 (Usability):** Web console adheres to WCAG 2.1 AA contrast and full keyboard navigation.
- **NFR-05 (Reproducibility):** Zero configuration drift; setup automated via Alembic migrations and pinned dependencies.
- **NFR-06 (Resource Bounding):** Strict limits on payload sizes (<= 1MB), grid coordinates (10x10), and pagination (<= 100).
- **NFR-07 (Time & Identifiers):** Universal UTC ISO-8601 timestamps and CSPRNG UUIDv4 identifiers across all tables.
- **NFR-08 (Maintainability):** Layered modular monolithic architecture with strict separation of concerns.

### 2.3 Security Requirements (SR) Summary
- **SR-01 (Authentication):** Passwords hashed with bcrypt; opaque 256-bit session tokens stored as SHA-256 digests.
- **SR-02 (Authorization):** Server-side deny-by-default role and object ownership validation on every endpoint.
- **SR-03 (Device Security):** Individual robot tokens authenticated via cryptographic hashes; mutual task binding.
- **SR-04 (Concurrency & Race Prevention):** PostgreSQL partial unique index prevents multiple active tasks on a single robot.
- **SR-05 (Accounting Integrity):** Stock alterations must be accompanied by immutable movement ledger records.
- **SR-06 (Audit Protection):** Security audit log table is append-only with no application-level update/delete capability.
- **SR-07 (Transport Security):** Strict TLS encryption in target production profiles; Secure/HttpOnly cookies.
- **SR-08 (Secret Hygiene):** Zero hard-coded credentials; credentials passed strictly via environment variables.
- **SR-09 (Injection Defense):** Strict ORM parameterized queries; auto-escaping HTML templates; anti-CSRF token verification.
- **SR-10 (Rate Limiting):** Brute-force throttling on login endpoints (max 5 failed attempts per 5-minute window).
- **SR-11 (Physical Invariant Safety):** Server-side enforcement of grid occupancy; robots cannot occupy identical cells.
- **SR-12 (Container Security):** Non-root container UID (10001), dropped Linux capabilities, read-only root filesystem.
- **SR-13 (Supply Chain Security):** CI/CD security gate enforcement (Bandit + Pytest) before image packaging.

---

## 3. Requirements Traceability Register

The complete structured CSV register is maintained at [`docs/requirements.csv`](file:///c:/Users/rajku/Downloads/SEM%207/secure%20software%20engineering/end%20sem%20lab%20exam/docs/requirements.csv), containing 18 Functional, 8 Non-Functional, and 13 Security Requirements.
