# Autonomous Warehouse Secure Management System (System 23)
**24CYS401 Secure Software Engineering — End Semester Laboratory Examination**  
*Full 16-Phase Solution — Formally Verified, Rootless Containerized, Defense-in-Depth Modular Monolith*

---

## 1. Project Overview & Scope
The **Autonomous Warehouse Management System** is a mission-critical logistics and robotic fulfillment engine designed for automated material handling within a 2D discrete coordinate warehouse grid. The system manages autonomous guided vehicles (AGVs) carrying physical stock from storage shelving bays to designated packing areas under strict cryptographic integrity, zero-trust device authentication, and multi-tenant isolation.

### Key Architectural Invariants
* **Strict Conservation of Stock:** $\text{on\_hand} \ge \text{reserved} \ge 0$. Stock deductions at pick source and additions at drop destination are recorded in an append-only inventory movement ledger.
* **Idempotent Atomic Reservation:** Order intake prevents double-allocation or race condition overselling across concurrent checkout transactions.
* **Mutual AGV Exclusion:** Exactly one active task per AGV; grid path planning enforces A*/BFS collision avoidance, preventing cell overlap or deadlocks.
* **Decoupled Autonomous Dispatcher:** Simulated AGVs authenticate using cryptographic bearer token digests (HMAC-SHA256) and execute allowlisted commands monotonically.
* **Human-in-the-Loop Web UI:** Accessible, WCAG 2.1 AA compliant server-side rendered interfaces for Customer order placement, Operator fleet dispatch/E-stop, Manager stock adjustments, and Auditor log inspection.

---

## 2. Quickstart & Verification in 60 Seconds

### Prerequisites
* Python 3.12+
* Docker & Docker Compose (Optional for container evaluation)

### Step 1: Install Locked Dependencies
```bash
python -m pip install -r requirements.txt
```

### Step 2: Seed the Database
```bash
python scripts/seed_demo.py
```
*Seeds warehouse layout, shelf bays, packing areas, 3 catalog items, 2 AGVs, and 6 role-based user accounts.*

### Step 3: Run Full Automated Test Suite (14 Tests)
```bash
pytest -v --tb=short tests/
```
*All 14 tests pass (Unit, Integration, System, and Hypothesis Boundary Fuzzing).*

### Step 4: Run Static Application Security Testing (SAST)
```bash
bandit -r app/ -c bandit.yaml
```
*Scans 1,808 lines of code with 0 High, 0 Medium, 0 Low vulnerabilities.*

### Step 5: Start Application Server
```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
* **Web UI URL:** [http://127.0.0.1:8000/web/login](http://127.0.0.1:8000/web/login)
* **Interactive API Docs (Swagger):** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
* **Health Endpoint:** [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

### Step 6: Start Autonomous AGV Dispatcher (Separate Terminal)
```bash
python -m worker.dispatcher
```
*Runs the discrete simulation tick loop advancing assigned AGVs along the warehouse grid.*

---

## 3. Seed User Credentials

All test accounts are pre-configured in `scripts/seed_demo.py` with Bcrypt hashed passwords:

| Username | Password | Role | System Permissions |
| :--- | :--- | :--- | :--- |
| `customer_bob` | `CustomerPass123!` | `CUSTOMER` | Place orders, reserve inventory, inspect personal order receipts. |
| `customer_charlie` | `CustomerPass123!` | `CUSTOMER` | Place orders (used in multi-tenant IDOR access isolation tests). |
| `operator_alice` | `OperatorPass123!` | `OPERATOR` | Inspect fleet telemetry, dispatch AGVs to tasks, trigger emergency pause/stop. |
| `manager_carol` | `ManagerPass123!` | `MANAGER` | Catalog management, stock level adjustments, view all warehouse orders. |
| `admin_dave` | `AdminPass123!` | `ADMIN` | User administration, AGV device registration, warehouse settings. |
| `auditor_eve` | `AuditorPass123!` | `AUDITOR` | Read-only inspection of immutable security audit trail. |

---

## 4. Engineering Deliverables & Documentation Index

| Phase | Category | Key File References | Summary of Contents |
| :---: | :--- | :--- | :--- |
| **00** | Mapping & Environment | `docs/00_case_study_mapping.md`, `docs/environment.md` | Question 23 mapping & host capability audit. |
| **01** | Agile Methodology | `docs/01_agile.md` | Scrum + XP hybrid, 8 Manifesto principles, RF-01/02 plan. |
| **02** | Requirements Engineering | `docs/02_srs.md`, `docs/requirements.csv` | 18 FR, 8 NFR, 13 SR items with CIA classification. |
| **03** | Use Cases & Analysis | `docs/03_use_cases.md`, `docs/03_analysis.md`, `diagrams/export/use_case_diagram.svg` | Fully dressed UC-04/06 and BCE robustness analysis. |
| **04** | Data Modeling & DFD | `docs/04_data_model.md`, `docs/04_dfd.md`, `diagrams/export/er_diagram.svg`, `dfd_level1.svg` | 16-entity Crow's foot model, DFD Level-1 with 5 trust boundaries. |
| **05** | Architecture & Patterns | `docs/05_architecture.md`, `diagrams/export/architecture_diagram.svg` | Modular monolith architecture, 6 design patterns, REST error envelope. |
| **06** | UI & Golden Rules | `docs/06_ui.md`, `diagrams/export/ui_screens.svg`, `app/templates/` | UI-01 to UI-06 screens and Shneiderman's 8 Golden Rules. |
| **07** | Threat Modeling (STRIDE) | `docs/07_assets.csv`, `07_threats.csv`, `07_vulnerabilities.csv`, `07_information_flow.md` | 10 assets, 14 threats, 4 flows, 8 evaluated vulnerabilities. |
| **08** | Attack Trees & Refinement | `docs/08_attack_tree.md`, `08_security_refinement.md`, `diagrams/export/attack_tree.svg` | Root AT-00, AND/OR tree, 4 attack paths, Architecture v2. |
| **09** | Agile Backlog & Sprints | `docs/09_backlog.csv`, `docs/09_sprint_plans.md`, `docs/jira_import.csv` | 18 stories across 6 epics, Sprint 1 & Sprint 2 plans. |
| **10** | Scrum Execution & Metrics | `docs/10_daily_scrum.md`, `docs/10_sprint_metrics.csv`, `docs/10_review_retrospective.md` | Daily standups, velocity (56 pts), burndown and retrospectives. |
| **11** | Secure Build & SAST | `docs/11_secure_build.md`, `evidence/phase11/bandit_scan.txt` | 7 build controls, Bandit scan (0 High/Medium/Low issues). |
| **12** | Refactoring & Coding | `docs/12_refactoring.md`, `app/services/task_service.py` | Primary assessed module: Atomic task assignment, RF-01 & RF-02. |
| **13** | Containers & Kubernetes | `docs/13_containers.md`, `Dockerfile`, `compose.yaml`, `k8s/`, `evidence/phase13/` | Multi-stage rootless Dockerfile (UID 10001), 10 K8s manifests. |
| **14** | Testing & Defects | `docs/14_tests.md`, `docs/14_defects.csv`, `evidence/phase14/test_run_output.txt` | 14 automated tests (100% pass), DEF-01 to DEF-06 resolved. |
| **15** | Operations & Monitoring | `docs/15_operations.md` | 9 security metrics/alerts, host sysctl hardening, physical E-stop. |
| **16** | Final Review & Traceability | `docs/16_final_review.md`, `docs/traceability.csv`, `submission/manifest.md` | Complete 11-step trace chain demonstration and final sign-off. |

---

## 5. Container & Kubernetes Deployment

### Launch Multi-Container Stack with Docker Compose
```bash
docker compose up -d
docker compose ps
docker compose logs app
```

### Validate Kubernetes Manifests
```bash
kubectl apply -f k8s/ --dry-run=client
```
*Validates 10 manifests: namespace, configmap, secrets, postgres statefulset, app deployment, dispatcher deployment, and microsegmented network policies.*

---

## 6. Security Assurance & Compliance
* **Static Application Security Testing (SAST):** 0 High, 0 Medium, 0 Low findings via Bandit.
* **Authentication & Authorization:** Bcrypt password hashing (`cost=12`), opaque session tokens stored as SHA-256 digests, deny-by-default role and object-level authorization (IDOR defense).
* **Cryptographic Bearer Device Tokens:** AGVs authenticate with SHA-256 digests salted with an environment pepper key.
* **Container Hardening:** Non-root execution (UID `10001`), read-only rootfs (`readOnlyRootFilesystem: true`), dropped Linux capabilities (`ALL`), unprivileged port 8000.
* **Audit Immutability:** Write-Once-Read-Many (WORM) append-only logging for all authentication, order, dispatch, and movement events.
