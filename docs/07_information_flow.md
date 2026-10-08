# Phase 7: Information Flow Analysis (IFA)

**Course:** 24CYS401 – Secure Software Engineering  
**System:** 23. Autonomous Warehouse Management System  
**Document Ref:** `docs/07_information_flow.md`  
**Marks:** 10 (part of Phase 7)  

---

## 1. Objectives & Methodology

Information Flow Analysis (IFA) traces the lifecycle of sensitive assets across system boundaries:
$$\text{Source Entity} \longrightarrow \text{Ingress Process} \longrightarrow \text{Internal Data Store} \longrightarrow \text{Egress Process} \longrightarrow \text{Sink Entity}$$
For each sensitive asset, we identify authorized readers/writers, cryptographic transformations, trust boundaries crossed, unintended covert leakage channels, and mandatory security controls.

---

## 2. Information Flow 1: Human & Robot Authentication Credentials (A01, A05)

### Path Trace:
$$\text{Browser (E1-E3) / Robot (E4)} \xrightarrow[\text{F01, F06}]{\text{TB1, TB3}} \text{P1 (IAM Engine)} \xrightarrow[\text{F01}]{\text{TB2}} \text{D1/D4 (Database)} \longrightarrow \text{Session Context} \longrightarrow \text{Response}$$

- **Data Classification:** Confidential / Restricted.
- **Authorized Writers:** Account owners (passwords), System Administrators (robot tokens).
- **Authorized Readers:** IAM Authentication Engine (`P1`) exclusively for verification.
- **Transformations:**
  1. Plaintext passwords received over TLS are immediately hashed using bcrypt / Argon2id with cryptographically random salts ($12$ rounds).
  2. Session tokens (256-bit entropy generated via `secrets.token_urlsafe(32)`) and robot device tokens are hashed via SHA-256 before storage in `sessions.token_digest` and `robots.token_digest`.
- **Potential Covert / Unintended Flows:**
  - Logging frameworks printing raw HTTP request headers or JSON request bodies to disk (`TB5`).
  - Database error messages echoing credentials in SQL constraint violation exceptions.
- **Mitigation & Enforcement Controls:**
  - Structured JSON logging logger filters out `password`, `token`, `authorization`, and `cookie` keys.
  - Plaintext tokens are returned once to the caller upon creation and never persisted in plaintext.

---

## 3. Information Flow 2: Inventory Balances & Physical Movement Ledger (A03, A06)

### Path Trace:
$$\text{Operator/Manager (E2)} \xrightarrow[\text{F02, F05}]{\text{TB1}} \text{P2/P4} \xrightarrow[\text{F04, F08}]{\text{TB2}} \text{D2/D4} \xrightarrow[\text{F06}]{\text{TB3}} \text{Robot AGV (E4)} \xrightarrow[\text{F07}]{\text{TB3}} \text{P4} \xrightarrow[\text{F08}]{\text{TB2}} \text{D2}$$

- **Data Classification:** High Integrity / Internal Operational.
- **Authorized Writers:** Warehouse Managers (manual adjustments), Dispatcher Worker (task allocations), Authenticated Robots (step acknowledgments).
- **Authorized Readers:** Warehouse Managers, Operators, Dispatcher Worker. Customers have zero read/write access.
- **Transformations:**
  1. Input adjustments validated: non-negative available quantity, valid SKU.
  2. Database locks `SELECT ... FOR UPDATE` serialize concurrent operations.
  3. Every physical deduction generates a cryptographically unique `source_event_id` in `inventory_movements`.
- **Potential Covert / Unintended Flows:**
  - Public order endpoints exposing global warehouse stock quantities to unauthorized customers (enabling competitor reconnaissance).
  - Unauthenticated robot endpoints allowing external actors to inject false pickup/drop acknowledgments.
- **Mitigation & Enforcement Controls:**
  - Customer API exposes only a boolean `in_stock` indicator rather than raw warehouse quantities.
  - Robot endpoints mandate valid bearer token authentication and verify expected state transitions before accepting step acknowledgments.

---

## 4. Information Flow 3: Customer Orders & Reservations (A04)

### Path Trace:
$$\text{Customer Browser (E1)} \xrightarrow[\text{F03}]{\text{TB1}} \text{P3 (Order Engine)} \xrightarrow[\text{F04}]{\text{TB2}} \text{D3 (Orders)} \xrightarrow[\text{F09}]{\text{TB2}} \text{P5 (Reporting)} \xrightarrow[\text{F09}]{\text{TB1}} \text{Customer Browser (E1)}$$

- **Data Classification:** Confidential / Tenant-Isolated.
- **Authorized Writers:** Authenticated Customer (order creator), Dispatcher (status progression).
- **Authorized Readers:** The specific Customer who placed the order (`owner_id == session.user_id`), Warehouse Manager.
- **Transformations:**
  1. Client-generated `Idempotency-Key` stored in `idempotency_records` alongside SHA-256 payload digest.
  2. Customer ID resolved directly from server session context, never accepted from request body.
- **Potential Covert / Unintended Flows:**
  - Insecure Direct Object Reference (IDOR): Customer A guessing or brute-forcing UUID of Customer B's order.
- **Mitigation & Enforcement Controls:**
  - Repository queries enforce strict SQL filter: `WHERE orders.id = :order_id AND orders.customer_id = :current_user_id`.
  - Non-existent or cross-tenant order queries return HTTP 404 Not Found to prevent resource existence enumeration.

---

## 5. Information Flow 4: Security Audit Trail & Forensics (A08)

### Path Trace:
$$\text{Application Processes (P1-P5)} \xrightarrow[\text{F10}]{\text{TB2, TB5}} \text{D5 (audit_events)} \xrightarrow[\text{F11}]{\text{TB5}} \text{P6} \xrightarrow[\text{F11}]{\text{TB1}} \text{Auditor Browser (E3)}$$

- **Data Classification:** Critical Integrity / Restricted Confidentiality.
- **Authorized Writers:** Core Application Domain Services (automated append-only inserts).
- **Authorized Readers:** Security Auditor (`AUDITOR`), System Administrator (`ADMIN`).
- **Transformations:** Structured JSON serialization, UTC ISO-8601 timestamping, actor attribution tagging.
- **Potential Covert / Unintended Flows:**
  - Malicious insiders modifying or deleting historical audit records following unauthorized stock manipulation.
  - Audit records storing sensitive plaintext passwords in metadata blobs.
- **Mitigation & Enforcement Controls:**
  - PostgreSQL database grants for application service user restrict operations to `INSERT` and `SELECT`; zero `UPDATE` or `DELETE` grants on `audit_events`.
  - Metadata sanitization function strips sensitive keys prior to serialization.
