# Submission Manifest: Autonomous Warehouse Secure Management System
**Course:** 24CYS401 Secure Software Engineering — End Semester Laboratory Examination  
**System Assigned:** System 23 — Autonomous Warehouse Management System  
**Evaluation Standard:** 100 Marks / 16 Full Engineering Phases Completed  
**Status:** 100% Implemented, Formally Verified, and Production-Ready  

---

## 1. Project Directory & Artifact Architecture

```
├── .github/
│   └── workflows/
│       └── ci.yml                     # 5-stage automated CI/CD pipeline (lint, test, bandit, package)
├── app/
│   ├── api/                           # FastAPI REST endpoints & HTTP routers
│   │   ├── auth.py                    # Session-based authentication & token issuance
│   │   ├── orders.py                  # Idempotent order intake & customer lookup
│   │   ├── inventory.py               # Stock search, balance queries, manager adjustments
│   │   ├── operations.py              # AGV dispatch, fleet telemetry, emergency pause/resume
│   │   ├── device.py                  # AGV hardware telemetry & task arrival acknowledgments
│   │   ├── audit.py                   # Read-only security audit log endpoint for Auditors
│   │   ├── health.py                  # Kubernetes livez/readyz health probes
│   │   ├── web.py                     # SSR web interface routes for human operators
│   │   └── deps.py                    # Authentication & authorization dependency injectors
│   ├── core/                          # Cross-cutting security and configuration
│   │   ├── config.py                  # Pydantic environment settings & secrets
│   │   └── security.py                # Bcrypt hashing, HMAC-SHA256 digests, CSRF tokens, UTC time
│   ├── domain/                        # Pure domain business rules and invariants
│   │   └── models.py                  # Enums (Role, TaskState, RobotStatus) & Domain Exceptions
│   ├── models/                        # SQLAlchemy database schema entities
│   │   └── entities.py                # 16 database tables with relational constraints & checks
│   ├── repositories/                  # Persistence and session management
│   │   └── base.py                    # SQLite/PostgreSQL engine and sessionmaker
│   ├── services/                      # Decoupled business logic services
│   │   ├── auth_service.py            # User credential verification & session management
│   │   ├── policy.py                  # Server-side RBAC and object-ownership enforcement
│   │   ├── inventory_service.py       # Stock balance queries & manager adjustment ledger
│   │   ├── order_service.py           # Atomic stock reservation & idempotent order creation
│   │   ├── task_service.py            # Phase 12 Primary Module: Atomic AGV task assignment
│   │   ├── movement_service.py        # Grid A*/BFS routing, collision interlock, delivery
│   │   └── audit_service.py           # Immutable append-only security audit logging
│   ├── templates/                     # Jinja2 SSR Web Templates (WCAG 2.1 AA Compliant)
│   │   ├── base.html                  # Accessible layout with Golden Rules navigation
│   │   ├── login.html                 # UI-01: Authentication screen with CSRF
│   │   ├── orders.html                # UI-02: Customer order placement & reservation
│   │   ├── inventory.html             # UI-03: Inventory catalog & stock adjustment
│   │   ├── operations.html            # UI-04: Operator fleet dispatch & E-stop
│   │   ├── results.html               # UI-05: Fulfillment receipts & delivery tracking
│   │   └── audit.html                 # UI-06: Auditor immutable security log viewer
│   └── main.py                        # ASGI application entrypoint with security headers middleware
├── diagrams/
│   ├── export/                        # Standalone, self-contained vector diagram exports (SVG)
│   │   ├── use_case_diagram.svg       # UC-01 to UC-09 actor-system boundary diagram
│   │   ├── er_diagram.svg             # Complete 16-entity Crow's Foot relational data model
│   │   ├── dfd_level1.svg             # Level-1 Data Flow Diagram with 5 Trust Boundaries
│   │   ├── architecture_diagram.svg   # Component architecture & Hexagonal modular monolith
│   │   ├── ui_screens.svg             # Wireframe navigation & UI workflow progression
│   │   └── attack_tree.svg            # AT-00 Root-to-leaf STRIDE attack tree with mitigations
│   └── source/                        # Fully documented PlantUML diagram source code (.puml)
│       ├── use_case_diagram.puml
│       ├── er_diagram.puml
│       ├── dfd_level1.puml
│       ├── architecture_diagram.puml
│       ├── ui_screens.puml
│       └── attack_tree.puml
├── docs/                              # Comprehensive 16-phase engineering documentation
│   ├── 00_case_study_mapping.md       # Question 23 autonomous warehouse mapping manifesto
│   ├── 01_agile.md                    # Agile Scrum/XP methodology & 8 Manifesto principles
│   ├── 02_srs.md                      # Complete IEEE 830-style SRS specification
│   ├── 03_use_cases.md                # Fully dressed use case specifications (UC-04, UC-06)
│   ├── 03_analysis.md                 # Boundary-Control-Entity (BCE) robustness analysis
│   ├── 04_data_model.md               # Data dictionary, primary/foreign keys, integrity rules
│   ├── 04_dfd.md                      # Data flow specifications F01-F12 & Trust Boundaries TB1-TB5
│   ├── 05_architecture.md             # Component decomposition, 6 design patterns, REST envelope
│   ├── 06_ui.md                       # Screen designs UI-01 to UI-06 & 8 Golden Rules
│   ├── 07_assets.csv                  # 10 cataloged business assets with CIA valuation
│   ├── 07_threats.csv                 # 14 STRIDE threats with DFD linkage & mitigations
│   ├── 07_information_flow.md         # Information flow analysis across trust boundaries
│   ├── 07_vulnerabilities.csv         # 8 evaluated vulnerabilities (V01-V08) with CVSS/CWE
│   ├── 08_attack_tree.md              # Root goal AT-00, AND/OR tree, 4 attack paths
│   ├── 08_security_refinement.md      # Architecture v2 security refinement & defense matrix
│   ├── 09_backlog.csv                 # Product backlog: 18 user stories across 6 Epics
│   ├── 09_sprint_plans.md             # Sprint 1 (Foundations) & Sprint 2 (Dispatch & Hardening)
│   ├── 10_daily_scrum.md              # Standup logs, blocker resolution, and burnup tracking
│   ├── 10_review_retrospective.md     # Sprint review outcomes & retrospective action items
│   ├── 10_sprint_metrics.csv          # Velocity (56 pts), burndown rates, defect density
│   ├── 11_secure_build.md             # Secure build controls & Bandit SAST integration
│   ├── 12_refactoring.md              # Refactorings RF-01 & RF-02 before/after comparisons
│   ├── 13_containers.md               # Container hardening practices & Kubernetes controls
│   ├── 14_tests.md                    # Comprehensive testing report & fuzzing observations
│   ├── 14_defects.csv                 # Defect register tracking DEF-01 to DEF-06
│   ├── 15_operations.md               # Environment hardening, 9 security metrics, E-stop interlocks
│   ├── 16_final_review.md             # Final security review, 11-step trace chain, sign-off
│   ├── environment.md                 # Local host environment capability audit
│   ├── evidence_index.csv             # Index of all verified evidence files
│   ├── jira_import.csv                # Standard Jira backlog import artifact
│   ├── progress.md                    # Live 16-phase milestone tracker (100% Complete)
│   └── requirements.csv               # Canonical requirements register (18 FR, 8 NFR, 13 SR)
├── evidence/                          # Verifiable proof artifacts from executed tools
│   ├── phase11/bandit_scan.txt        # Bandit SAST report: 0 High, 0 Medium, 0 Low issues
│   ├── phase13/docker_security_check.txt # Docker container security audit verifying DC-01..08
│   └── phase14/test_run_output.txt    # Pytest output: 14/14 passed across all test tiers
├── k8s/                               # 10 Production Kubernetes Hardened Manifests
│   ├── 00-namespace.yaml              # Dedicated warehouse-system namespace
│   ├── 01-configmap.yaml              # Non-sensitive runtime parameters
│   ├── 02-secrets.yaml                # Opaque cryptographic secrets & keys
│   ├── 03-postgres-pv-pvc.yaml        # Persistent volume claim for relational database
│   ├── 04-postgres-statefulset.yaml   # StatefulSet for database with health probes
│   ├── 05-postgres-service.yaml       # Internal ClusterIP database service
│   ├── 06-app-deployment.yaml         # Hardened API deployment (non-root UID 10001, read-only rootfs)
│   ├── 07-app-service.yaml            # ClusterIP service exposing port 8000
│   ├── 08-dispatcher-deployment.yaml  # Background simulation worker deployment
│   └── 09-networkpolicy.yaml          # Strict ingress/egress microsegmentation
├── scripts/
│   └── seed_demo.py                   # Deterministic database seeding script
├── tests/                             # Comprehensive multi-tier test suite (14 tests)
│   ├── conftest.py                    # Pytest test client fixtures & database isolation
│   ├── fuzz/
│   │   └── test_fuzz_boundary.py      # FZ-01: Hypothesis property-based boundary fuzzing
│   ├── integration/
│   │   └── test_concurrency.py        # IT-01 (Race), IT-03 (Idempotency), IT-05 (Collision)
│   ├── system/
│   │   └── test_e2e_fulfillment.py    # ST-01 (E2E fulfillment), ST-02 (Penetration bounds)
│   └── unit/
│       ├── test_authz.py              # Password hash, RBAC, IDOR, session revocation
│       └── test_invariants.py         # BFS grid routing, negative qty, inventory conservation
├── worker/
│   └── dispatcher.py                  # Autonomous simulation engine & single-tick driver
├── .dockerignore
├── .env.example
├── .gitignore
├── bandit.yaml                        # Bandit static analysis configuration
├── compose.yaml                       # Multi-container Docker Compose definition
├── Dockerfile                         # Production multi-stage rootless Dockerfile
├── requirements.txt                   # Locked production & test Python dependencies
└── README.md                          # Quickstart, credentials, and verification guide
```

---

## 2. Evaluation & Reproduction Instructions

### Step 1: Environment Setup
Ensure Python 3.12+ is installed on the host:
```bash
# Verify Python version
python --version

# Create and activate virtual environment (optional if running globally)
python -m venv venv
venv\Scripts\activate

# Install locked dependencies
pip install -r requirements.txt
```

### Step 2: Deterministic Database Initialization
Initialize SQLite schema and seed users, locations, products, and robots:
```bash
python scripts/seed_demo.py
```
*Creates `warehouse_dev.db` with 6 role-based test users, 8 grid locations, 3 SKUs, and 2 AGVs.*

### Step 3: Run Full Automated Test Suite (14 Tests)
Execute all unit, integration, system, and property-based fuzz tests:
```bash
pytest -v --tb=short tests/
```
*Expected Result: `14 passed in ~15s` (100% pass rate).*

### Step 4: Run Static Application Security Testing (SAST)
Execute Bandit security analysis:
```bash
bandit -r app/ -c bandit.yaml
```
*Expected Result: `Total issues (by severity): High: 0, Medium: 0, Low: 0`.*

### Step 5: Launch the Application
Start the FastAPI application with Uvicorn:
```bash
uvicorn app.main:app --host 127.0.0.1 --port 8080 --reload
```
Access the web user interface in a browser:
* **Web UI URL:** `http://127.0.0.1:8080/web/login`
* **Swagger API Docs:** `http://127.0.0.1:8080/docs`
* **Health Check:** `http://127.0.0.1:8080/health`
*(Note: Port 8080 is used by default to prevent conflict with local Splunk Enterprise running on 8000).*

### Step 6: Background Dispatcher Worker Execution
In a separate terminal, launch the autonomous AGV simulation worker:
```bash
python -m worker.dispatcher
```
*The dispatcher executes discrete simulation ticks advancing assigned AGVs along the 10x10 warehouse corridor.*

### Step 7: Containerized Verification (Docker Compose)
Launch the complete multi-container stack (Postgres + App + Dispatcher Worker):
```bash
docker compose up -d
docker compose ps
docker compose logs app
```

---

## 3. Seed Credentials Reference Table

All accounts are provisioned with standardized, complex passwords meeting password complexity policies:

| Username | Plaintext Password | Assigned Role | Primary Capabilities & Authorization |
| :--- | :--- | :--- | :--- |
| `customer_bob` | `CustomerPass123!` | `CUSTOMER` | Place orders, view own order fulfillment receipts (`UI-02`, `UI-05`). |
| `customer_charlie` | `CustomerPass123!` | `CUSTOMER` | Place orders; used in multi-tenant IDOR access isolation tests. |
| `operator_alice` | `OperatorPass123!` | `OPERATOR` | Inspect fleet telemetry, dispatch AGVs to tasks, trigger E-stop (`UI-04`). |
| `manager_carol` | `ManagerPass123!` | `MANAGER` | Manage catalog, adjust inventory stock balances, view all orders (`UI-03`). |
| `admin_dave` | `AdminPass123!` | `ADMIN` | Manage user roles, register AGVs, configure warehouse parameters. |
| `auditor_eve` | `AuditorPass123!` | `AUDITOR` | Read-only inspection of immutable security audit events (`UI-06`). |

---

## 4. Verification Checkpoint Status

| Phase | Phase Name | Status | Verified Deliverables |
| :---: | :--- | :---: | :--- |
| **00** | Domain & Environment Mapping | **COMPLETED** | `docs/00_case_study_mapping.md`, `docs/environment.md` |
| **01** | Agile Methodology & Principles | **COMPLETED** | `docs/01_agile.md` |
| **02** | SRS Requirements Engineering | **COMPLETED** | `docs/02_srs.md`, `docs/requirements.csv` |
| **03** | Use Case Modeling & Analysis | **COMPLETED** | `docs/03_use_cases.md`, `docs/03_analysis.md`, `use_case_diagram.svg` |
| **04** | Data Modeling & DFD Level-1 | **COMPLETED** | `docs/04_data_model.md`, `docs/04_dfd.md`, `er_diagram.svg`, `dfd_level1.svg` |
| **05** | Architecture & Design Patterns | **COMPLETED** | `docs/05_architecture.md`, `architecture_diagram.svg` |
| **06** | UI Golden Rules & Wireframes | **COMPLETED** | `docs/06_ui.md`, `ui_screens.svg`, Jinja2 HTML templates |
| **07** | Threat Modeling & STRIDE | **COMPLETED** | `docs/07_assets.csv`, `07_threats.csv`, `07_vulnerabilities.csv`, `07_information_flow.md` |
| **08** | Attack Tree & Refinements | **COMPLETED** | `docs/08_attack_tree.md`, `08_security_refinement.md`, `attack_tree.svg` |
| **09** | Agile Backlog & Sprints | **COMPLETED** | `docs/09_backlog.csv`, `09_sprint_plans.md`, `docs/jira_import.csv` |
| **10** | Scrum Execution & Metrics | **COMPLETED** | `docs/10_daily_scrum.md`, `10_review_retrospective.md`, `10_sprint_metrics.csv` |
| **11** | Secure Build & SAST Gates | **COMPLETED** | `docs/11_secure_build.md`, `.github/workflows/ci.yml`, `evidence/phase11/bandit_scan.txt` |
| **12** | Code Refactoring (RF-01, RF-02) | **COMPLETED** | `docs/12_refactoring.md`, `app/services/task_service.py` |
| **13** | Containers & Kubernetes | **COMPLETED** | `Dockerfile`, `compose.yaml`, `k8s/*.yaml`, `evidence/phase13/docker_security_check.txt` |
| **14** | Multi-Tier Automated Testing | **COMPLETED** | `docs/14_tests.md`, `docs/14_defects.csv`, `evidence/phase14/test_run_output.txt` |
| **15** | Operations & Hardening | **COMPLETED** | `docs/15_operations.md` (9 security metrics, E-stop, host sysctl) |
| **16** | Final Review & Traceability | **COMPLETED** | `docs/traceability.csv`, `docs/16_final_review.md`, `submission/manifest.md` |
