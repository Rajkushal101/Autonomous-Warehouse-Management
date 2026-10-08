# SOFTWARE REQUIREMENTS SPECIFICATION (SRS)
## SYSTEM 23: AUTONOMOUS WAREHOUSE MANAGEMENT SYSTEM (AWMS)

**Course:** 24CYS401 – Secure Software Engineering Laboratory  
**Standard:** IEEE Std 830-1998 / ISO/IEC/IEEE 29148:2018 Compliant  
**Document Identifier:** AWMS-SRS-V1.0  
**Academic Year:** 2025–2026 (Semester 7)  
**Status:** Approved for End Semester Examination  

---

## 1. INTRODUCTION

### 1.1 Purpose
This Software Requirements Specification (SRS) establishes the complete, verifiable, and authoritative technical requirements for **System 23: Autonomous Warehouse Management System (AWMS)**. It is structured in compliance with IEEE Std 830-1998 and ISO/IEC/IEEE 29148:2018 standards.

### 1.2 Document Conventions & Notation
- **FR-xx:** Functional Requirements.
- **NFR-xx:** Non-Functional Requirements.
- **SR-xx:** Cyber-Physical Security Requirements.
- **INV-xx:** Safety and Concurrency Invariants.
- RFC 2119 keyword standards: MUST, SHOULD, COULD.

### 1.3 Intended Audience
Intended for academic evaluators, software engineers, robotics systems architects, quality assurance engineers, and compliance auditors.

### 1.4 Project Scope & Objectives
System 23 manages warehouse fulfillment across a 10×10 physical grid. Objectives include:
1. Zero-overselling via atomic database locking (`SELECT FOR UPDATE`).
2. Physical safety assurance via collision-free AGV navigation and hardware Emergency Stop (E-Stop).
3. Cryptographic tamper evidence via SHA-256 block-chained audit ledgers.
4. Granular Role-Based Access Control (RBAC) isolating Customer, Operator, Manager, Admin, and Auditor roles.

---

## 2. OVERALL DESCRIPTION

### 2.1 User Classes & Stakeholders
- **ACT-01 (Customer):** Places orders, tracks status, cancels unpicked orders (IDOR protected).
- **ACT-02 (Warehouse Operator):** Monitors robot operations, executes packing bay scanning.
- **ACT-03 (Warehouse Manager):** Manages catalog, shelf locations, and stock adjustments.
- **ACT-04 (System Administrator):** Manages accounts, roles, and cluster credentials.
- **ACT-05 (Security Auditor):** Reviews immutable audit logs (read-only).
- **ACT-06 (Robot Device / AGV):** Autonomous mobile robot executing waypoint navigation.
- **ACT-07 (Dispatcher Worker):** Background daemon orchestrating task queues.

---

## 3. SYSTEM FEATURES & FUNCTIONAL REQUIREMENTS

![UML Use Case Diagram](graphs/01_use_case.jpg)
*Figure 3.1: AWMS Comprehensive UML Use Case Diagram.*

![UML Activity Diagram](graphs/02_activity.jpg)
*Figure 3.2: UML Activity Diagram for Robotic Fulfillment Workflow.*

### Functional Requirements Inventory (FR-01 to FR-18)
- **FR-01 (Identity & Session):** Secure login, logout, session timeout, and token revocation.
- **FR-02 (RBAC Authorization):** Role-based permission enforcement on all API routes.
- **FR-03 (Catalog Management):** Product SKU uniqueness, positive weights (> 0).
- **FR-04 (Location Registry):** Discrete 10×10 grid coordinates and obstacle definitions.
- **FR-05 (Inventory Balances):** Real-time calculation: available = on_hand - reserved >= 0.
- **FR-06 (Robot Registration):** Machine identity, hashed tokens, battery and payload bounds.
- **FR-07 (Idempotent Orders):** Customer order submission with client UUIDv4 idempotency keys.
- **FR-08 (Atomic Stock Reservation):** ACID row-level locking preventing concurrent overselling.
- **FR-09 (Task Assignment):** Atomic assignment of queued tasks to eligible idle robots.
- **FR-10 (Task Execution):** Sequential pickup, transit, and packing bay delivery.
- **FR-11 (Robot Telemetry):** Live heartbeat tracking, battery status, and stale robot isolation.
- **FR-12 (Collision Prevention):** Grid cell exclusivity; rejection of swap maneuvers.
- **FR-13 (Emergency Stop):** Hardware E-Stop halting all robot movement within 200ms.
- **FR-14 (Fulfillment Results):** Authenticated results view with strict tenant IDOR defense.
- **FR-15 (Cryptographic Audit):** Append-only SHA-256 block-chained ledger.
- **FR-16 (Health & Metrics):** Liveness, readiness probes and SIEM telemetry.
- **FR-17 (Inventory Search):** Filtered SKU search and low-stock threshold alerts.
- **FR-18 (CSV Export & Routing):** RFC-4180 CSV export and battery-optimized path routing.

---

## 4. EXTERNAL INTERFACE REQUIREMENTS
- **User Interfaces:** Live responsive dashboards on `http://127.0.0.1:8080` (Login, Inventory, Orders, Operations Grid, Fulfillment, Audit).
- **Hardware Interfaces:** AGV embedded microcontrollers, LiDAR proximity sensors, wheel encoders, physical E-Stop relays.
- **Software Interfaces:** FastAPI REST APIs, SQLite WAL / PostgreSQL 16 database, Splunk SIEM via HTTP Event Collector.
- **Communications:** HTTPS with TLS 1.3, mTLS with robot bearer tokens, WebSockets for grid telemetry.

---

## 5. NON-FUNCTIONAL REQUIREMENTS (NFR)
- **NFR-01 (Performance):** Read API latency < 500 ms at p95 under 100 concurrent requests.
- **NFR-02 (ACID Concurrency):** Database transactions enforce strict row locks; zero overselling.
- **NFR-03 (Fault Tolerance):** Durable task persistence; safe recovery after worker crash.
- **NFR-04 (Usability):** WCAG 2.1 AA accessibility compliance and ergonomic color schemes.
- **NFR-05 (Reproducibility):** Pinned dependencies, automated Alembic migrations, Docker containers.
- **NFR-06 (Resource Bounding):** Request bodies <= 1MB, pagination <= 100, grid clamped to 10×10.
- **NFR-07 (Time & Identifiers):** Universal UTC ISO-8601 timestamps and UUIDv4 CSPRNG identifiers.
- **NFR-08 (Maintainability):** Layered Clean Architecture isolating domain models.

---

## 6. SECURITY REQUIREMENTS (SR) & THREAT MITIGATIONS

![STRIDE Threat Matrix](graphs/23_stride.jpg)
*Figure 6.1: STRIDE Threat Model Matrix and Risk Classifications.*

![Attack Tree Analysis](graphs/11_attack_tree.jpg)
*Figure 6.2: Attack Tree Diagram for Fleet Hijack and Inventory Race Conditions.*

![Sensitive Data Flow](graphs/16_sensitive_flow.jpg)
*Figure 6.3: Sensitive Data Flow Boundaries and Cryptographic Isolation.*

![Zero-Trust Architecture](graphs/12_secure_architecture.jpg)
*Figure 6.4: AWMS Secure Zero-Trust Defense-in-Depth Architecture.*

- **SR-01 (Passwords & Sessions):** Bcrypt hashing (cost 12), 256-bit opaque tokens.
- **SR-02 (RBAC):** Server-side deny-by-default role and object ownership verification.
- **SR-03 (Robot Identity):** Bearer tokens validated against cryptographic digests.
- **SR-04 (Atomic Tasks):** Partial unique index prevents multiple active tasks per robot.
- **SR-05 (Ledger Integrity):** Double-entry physical movement ledger.
- **SR-06 (Audit Protection):** Append-only SHA-256 chained audit trail; zero application DELETE.
- **SR-07 (Transport Security):** Strict TLS 1.3; Secure, HttpOnly, SameSite=Lax cookies.
- **SR-08 (Secret Hygiene):** Zero hardcoded credentials; injected via environment variables.
- **SR-09 (Injection Defense):** Parameterized ORM queries; auto-escaping templates; anti-CSRF tokens.
- **SR-10 (Rate Limiting):** Brute-force throttling (max 5 failed attempts per 5 minutes).
- **SR-11 (Physical Invariants):** Server-side enforcement of grid occupancy.
- **SR-12 (Container Security):** Non-root UID 10001, dropped capabilities, read-only root filesystems.
- **SR-13 (DevSecOps):** Automated CI/CD security gates (Bandit SAST + Pytest).

---

## 7. DATA MODEL & RELATIONAL SCHEMA

![Entity Relationship Diagram](graphs/03_erd.jpg)
*Figure 7.1: AWMS Relational Entity-Relationship Diagram (ERD).*

![AGV State Machine](graphs/15_state_machine.jpg)
*Figure 7.2: AGV Robot Finite State Machine Diagram.*

Relational Entities:
1. `users`, 2. `sessions`, 3. `warehouses`, 4. `locations`, 5. `products`, 
6. `inventory_balances`, 7. `orders`, 8. `order_items`, 9. `stock_reservations`, 
10. `robots`, 11. `tasks`, 12. `commands`, 13. `inventory_movements`, 14. `audit_events`.

---

## 8. VERIFICATION RESULTS
- **Pytest Test Suite:** 14 passed in 0.81s (100% pass rate).
- **Bandit SAST Audit:** 0 High, 0 Medium, 0 Low Vulnerabilities.

---

## 9. AUDITED SOFTWARE & TECHNOLOGY INVENTORY

| Category | Software / Library | Exact Version | Architectural Purpose | Verification Command |
|---|---|---|---|---|
| **Host Operating System** | Microsoft Windows 11 Pro | `10.0.26220 (Insider AMD64)` | Host operating system and runtime kernel | `(Get-CimInstance Win32_OperatingSystem).Version` |
| **Shell & Scripting** | PowerShell 7 Core | `7.6.6` | Task automation and system execution shell | `$PSVersionTable.PSVersion` |
| **Version Control** | Git for Windows | `2.55.0.windows.1` | Source code version control and history management | `git --version` |
| **Programming Language** | Python | `3.12.10 (AMD64)` | Primary core implementation runtime | `python --version` |
| **Web Framework** | FastAPI | `0.115.0` | High-performance asynchronous REST API framework | `fastapi.__version__` |
| **ASGI Server** | Uvicorn | `0.30.6` | Production ASGI web server running on port 8080 | `uvicorn.__version__` |
| **Data Validation** | Pydantic | `2.8.2` | Strict schema validation and data serialization | `pydantic.__version__` |
| **Settings Management**| Pydantic Settings | `2.4.0` | Environment configuration and secrets management | `pydantic_settings.__version__` |
| **Database ORM** | SQLAlchemy | `2.0.32` | Relational ORM with row-level transactional locking | `sqlalchemy.__version__` |
| **Database Engine** | SQLite (WAL Mode) | `3.49.1` | Relational database engine with ACID transactions | `sqlite3.sqlite_version` |
| **Password Hashing** | Bcrypt | `4.2.0` | Secure password hashing using adaptive cost factor 12 | `bcrypt.__version__` |
| **Cryptographic Engine**| Python Hashlib (SHA-256)| `3.12.10 (Standard Lib)` | Merkle-style block chaining of audit ledger records | `hashlib.__file__` |
| **Template Engine** | Jinja2 | `3.1.4` | Server-side HTML template rendering engine | `jinja2.__version__` |
| **HTTP Client Library**| Requests | `2.32.3` | Integration testing and HTTP API client | `requests.__version__` |
| **Testing Framework** | Pytest | `8.3.2` | Automated unit and integration testing suite | `pytest --version` |
| **Property-Based Test**| Hypothesis | `6.111.0` | Invariant fuzzing and property-based verification | `hypothesis.__version__` |
| **Security SAST Tool** | Bandit | `1.7.9` | AST-based Static Application Security Testing scanner | `bandit --version` |
| **Document Generator** | python-docx | `1.2.0` | Automated report compilation and DOCX packaging | `docx.__version__` |
| **Agile Management** | Atlassian Jira Cloud | `Cloud Edition (AWMS)` | Agile Scrum management (105 items, 6 Epics, 2 Sprints) | `rajkushal-warehouse.atlassian.net` |
| **Diagramming Platform**| Diagrams.net / Draw.io | `v24.7.17` | UML, DFD, Threat Modeling and UI wireframe design | `app.diagrams.net` |
| **Container Engine** | Docker Engine | `27.x (OCI Compliant)` | Multi-stage non-root container packaging | `docker --version` |
| **Container Platform** | Kubernetes | `v1.30 (Declarative Specs)`| 10 hardened production deployment manifests (`k8s/`) | `kubectl version --client` |
| **Security Monitoring**| Splunk Enterprise SIEM | `Splunk HEC 9.x Compatible`| Telemetry streaming and cyber-physical SIEM alerting | `Splunk HEC Specification` |

---
*Certified Complete and Compliant with IEEE Std 830-1998 / ISO/IEC/IEEE 29148:2018.*
