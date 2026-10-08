# Phase 4: Data Flow Diagram (DFD) & Trust Boundaries

**Course:** 24CYS401 – Secure Software Engineering  
**System:** 23. Autonomous Warehouse Management System  
**Document Ref:** `docs/04_dfd.md`  
**Marks:** 7  

---

## 1. DFD Model Architecture

The Data Flow architecture is structured into:
1. **Context Diagram (Level-0 Abstract):** System as a single black box surrounded by external entities.
2. **Level-0 Diagram:** Decomposition into 6 core processes, 5 persistent data stores, and 5 explicit trust boundaries.
3. **Level-1 Decomposition (P4 - Robot Task Orchestration):** Detailed breakdown of robotic dispatch, step validation, and physical movement.

---

## 2. DFD Element Inventory

### External Entities (E)
- **E1: Customer Browser:** Human end-user placing orders and checking delivery progress.
- **E2: Operator / Manager Browser:** Operational staff monitoring inventory, tasks, and robots.
- **E3: Administrator / Auditor Browser:** System admin managing accounts; auditor viewing security trails.
- **E4: Robot AGV Device (Simulator):** Autonomous mobile unit querying commands and transmitting step telemetry.
- **E5: CI/CD Pipeline & Deployer:** Build systems delivering code artifacts, configs, and containers.

### Processes (P)
- **P1: Authentication & Access Control Engine:** Validates sessions, hashes, and deny-by-default RBAC policies.
- **P2: Catalog & Inventory Management:** Enforces product bounds, locations, and manual stock corrections.
- **P3: Order Validation & Atomic Stock Reservation:** Validates item limits and locks rows to allocate reserved stock.
- **P4: Robot Task Orchestration & Command Dispatch:** Coordinates robot assignments, step navigation, and collision checks.
  - *P4.1: Authorize & Validate Robot Eligibility*
  - *P4.2: Atomic Task Binding & Command Generation*
  - *P4.3: Step Navigation & Collision Occupancy Verification*
  - *P4.4: Pickup & Packing Drop Ledger Commitment*
- **P5: Fulfillment Evaluation & Reporting:** Aggregates delivery outcomes and produces tenant-isolated order receipts.
- **P6: Audit Logging & Telemetry Monitor:** Ingests security-relevant events and operational health metrics.

### Data Stores (D)
- **D1: Users & Sessions (`users`, `sessions`):** Account credentials and active tokens.
- **D2: Catalog & Inventory Ledger (`products`, `locations`, `inventory_balances`, `inventory_movements`):** Physical inventory truth.
- **D3: Orders & Reservations (`orders`, `order_items`, `stock_reservations`, `idempotency_records`):** Transactional customer commitments.
- **D4: Robot Fleet & Commands (`robots`, `tasks`, `commands`, `warehouse_controls`):** Real-time fleet state and dispatch queues.
- **D5: Security Audit Trail (`audit_events`):** Append-only forensic records.

### Trust Boundaries (TB)
- **TB1: Untrusted Public Network to API Gateway:** Separates external browsers (E1, E2, E3) from internal backend application logic. Requires authentication, CSRF tokens, TLS, and input validation.
- **TB2: Application Services to Protected PostgreSQL Database:** Enforces database user least privilege, parameterized queries, and connection encryption.
- **TB3: Robot Machine Network to Command Ingress:** Separates robot hardware/simulators (E4) from backend services. Requires per-device bearer token digests and sequence verification.
- **TB4: Build & Deployment Plane to Production Runtime:** Separates development source control and CI/CD agents (E5) from live container runtime. Enforces signed commits, secret injection, and non-root containers.
- **TB5: Application Layer to Audit & Forensics Log Sink:** Protects security audit events from unauthorized tampering or deletion.

---

## 3. Data Flow Register (F01 to F12)

| Flow ID | Source | Destination | Data Content | Transport & Auth | Trust Boundary | Security Classification |
|---|---|---|---|---|---|---|
| **F01** | E1/E2/E3 | P1 | Login credentials, session cookie, CSRF token | HTTPS / TLS, POST body | Crosses **TB1** | Confidential |
| **F02** | E2 | P2 | Stock adjustment with reason code, catalog updates | HTTPS, Session + RBAC | Crosses **TB1** | Restricted |
| **F03** | E1 | P3 | Customer order items, quantities, idempotency key | HTTPS, Session (CUSTOMER) | Crosses **TB1** | Restricted |
| **F04** | P3 | D2, D3 | Row locks, reserved quantity increment, task queue | PostgreSQL TCP, Parameterized | Crosses **TB2** | High Integrity |
| **F05** | E2 | P4 | Task assignment request, target robot, idempotency key | HTTPS, Session (OPERATOR) | Crosses **TB1** | Restricted |
| **F06** | E4 | P4 | Command fetch request with Bearer Device Token | HTTPS / HTTP, Device Token | Crosses **TB3** | Confidential |
| **F07** | E4 | P4 | Step movement telemetry, pickup/drop ack, heartbeat | HTTPS / HTTP, Device Token | Crosses **TB3** | High Integrity |
| **F08** | P4 | D2, D4 | Atomic location update, movement ledger insert, task complete | PostgreSQL TCP, Row Lock | Crosses **TB2** | Critical Integrity |
| **F09** | E1/E2 | P5 | Fulfillment status query, order receipt request | HTTPS, Session (IDOR check) | Crosses **TB1** | Confidential |
| **F10** | P1-P5 | D5 | Security audit records, actor attribution, failure reasons | PostgreSQL TCP, Append-Only | Crosses **TB2** / **TB5** | Critical Integrity |
| **F11** | P1-P5 | E3 | System health metrics, error rates, stale robot alerts | HTTPS, Session (ADMIN/AUDITOR) | Crosses **TB1** / **TB5** | Internal Operational |
| **F12** | E5 | Runtime | Container image, locked manifests, env secrets | OCI Image Registry, K8s Secret | Crosses **TB4** | Critical Integrity |
