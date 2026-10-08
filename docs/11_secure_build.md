# Phase 11: Secure Development & Build Environment

**Course:** 24CYS401 – Secure Software Engineering  
**System:** 23. Autonomous Warehouse Management System  
**Document Ref:** `docs/11_secure_build.md`  
**Marks:** 6  

---

## 1. Secure Repository & Branching Strategy

The repository follows a hardened Git branching workflow:
- **`main`:** Production-grade, deployable trunk. Direct pushes are disabled; changes require a Pull Request (PR) with mandatory passing checks.
- **`feature/AWMS-X`:** Short-lived feature branches linked directly to Jira issue keys.
- **`fix/DEF-X`:** Bugfix branches remediating verified security or defect issues.
- **Merge Requirements:** Mandatory review, passing unit/integration tests, zero Bandit security vulnerabilities.

---

## 2. Seven Implemented Build & Development Security Controls

| # | Security Control | Practical Implementation & Enforcement | Verification Evidence |
|---|---|---|---|
| **1** | **Least Privilege Contributor Roles** | Repository permissions restricted: developers have branch creation rights; merge to `main` restricted to signed PRs. | Git commit log and branch access policy. |
| **2** | **Secret Hygiene & Zero Hardcoded Secrets** | Credentials, DB passwords, and private keys excluded via `.gitignore` and `.dockerignore`. Values injected strictly via runtime environment variables. | `evidence/phase11/bandit_scan.txt` & `.env.example` |
| **3** | **Exact Dependency Pinning** | Every direct and transitive dependency locked to exact version numbers (e.g., `fastapi==0.115.0`, `bcrypt==4.2.0`). | `requirements.lock` / `requirements.txt` |
| **4** | **Automated Static Security Gate (AST Scan)** | Bandit AST security scanner runs automatically on every build. Scans for weak crypto, hardcoded secrets, shell injection, and insecure bindings. | `evidence/phase11/bandit_scan.txt` (0 High / 0 Medium findings) |
| **5** | **Protected Main Branch Enforcement** | Direct push to `main` blocked by Git hook and CI branch protection rules. | Git branch tracking and CI workflow file. |
| **6** | **Reproducible Hermetic Builds** | Multi-stage Dockerfile ensures build environment isolation; container digest generated based on content addressability. | `Dockerfile` and build manifest. |
| **7** | **Artifact Integrity Linkage** | Container image tagged with git commit SHA (`awms:${GITHUB_SHA}`) ensuring strict traceability between source and running binary. | CI/CD pipeline manifest (`.github/workflows/ci.yml`). |

---

## 3. Automated Static Security Check & Verification Results

Bandit scanner was executed across the entire codebase (`app/` and `worker/`):
```bash
bandit -r app/ worker/ -ll -f txt -o evidence/phase11/bandit_scan.txt
```
The actual scan report confirms **zero high-severity** and **zero medium-severity** security vulnerabilities across all scanned lines of code. Full execution output is archived at [`evidence/phase11/bandit_scan.txt`](file:///c:/Users/rajku/Downloads/SEM%207/secure%20software%20engineering/end%20sem%20lab%20exam/evidence/phase11/bandit_scan.txt).
