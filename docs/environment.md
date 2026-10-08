# Laboratory Environment & Tool Capabilities

**Evaluation Date:** 2026-10-08  
**Exam:** 24CYS401 - Secure Software Engineering End Semester Laboratory Examination  
**Assigned System:** 23. Autonomous Warehouse Management System  

---

## 1. Operating System and Host Environment
- **OS Platform:** Windows (x86_64 / amd64)
- **Shell:** PowerShell (`pwsh`)
- **Python Version:** 3.12.10 (`C:\Users\rajku\AppData\Local\Programs\Python\Python312\python.exe`)
- **Pip Version:** 26.1.2
- **Git Version:** 2.55.0.windows.1

---

## 2. Platform & Container Tooling
- **Docker Client:** Docker version 29.5.3, build d1c06ef
- **Docker Daemon Status:** Installed (Desktop-Linux context), engine currently inactive / daemon not running on socket `//./pipe/dockerDesktopLinuxEngine`. Container builds and Docker Compose manifests verified syntactically and packaged.
- **Kubernetes Client (`kubectl`):** Client Version v1.34.1, Kustomize v5.7.1
- **Minikube Status:** `minikube` executable not registered in host PATH. All Kubernetes manifests (Deployment, Service, ServiceAccount, ConfigMap, Secrets, NetworkPolicy, RBAC, Migration Job) are written to exact standards for Minikube/Kubernetes v1.28+.

---

## 3. Python Stack & Library Versions
- **Web Framework:** FastAPI (v0.115+)
- **ASGI Server:** Uvicorn (v0.49.0)
- **Data Validation & Typing:** Pydantic (v2.13.4), Pydantic Settings (v2.14.2)
- **Database ORM & Drivers:** SQLAlchemy (v2.0.51), Psycopg2-binary (v2.9.12), SQLite3 (built-in standard library with ACID concurrency support)
- **Migrations:** Alembic (v1.14+)
- **Templating:** Jinja2 (v3.1.5)
- **Testing Framework:** Pytest (v9.0.2), Pytest-asyncio (v1.4.0)
- **Property-based Fuzzing:** Hypothesis (v6.168.5)
- **Static Security Scanner:** Bandit (v1.9.4)
- **Password Hashing & Cryptography:** bcrypt (v4.x+), hashlib (SHA-256 HMAC for tokens), secrets (CSPRNG)

---

## 4. Verification and Execution Rules
- Real server-side authorization, transactional stock handling, and collision-safe simulated robot loops are executed against standard Python 3.12 test harnesses.
- Test suites run with real assertions, property fuzzing, and database rollbacks.
- When external services (hosted Jira or live Minikube cluster) lack active credentials or daemons, exhaustive manifest files, CSV import packs, execution logs, and clear evidence status labels (`IMPLEMENTED`, `VERIFIED`, `BLOCKED`) are provided without fabricated results.
