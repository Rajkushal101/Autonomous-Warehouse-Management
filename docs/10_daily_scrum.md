# Phase 10: Daily Scrum Records & Board Execution

**Course:** 24CYS401 – Secure Software Engineering  
**System:** 23. Autonomous Warehouse Management System  
**Document Ref:** `docs/10_daily_scrum.md`  
**Marks:** 7  

---

## 1. Scrum Board Workflow Architecture

The board transitions follow the exact mandatory pipeline:
$$\mathbf{TO\ DO} \longrightarrow \mathbf{IN\ PROGRESS} \longrightarrow \mathbf{TESTING} \longrightarrow \mathbf{DONE}$$

### Definition of Transition Rules:
1. `TO DO` $\rightarrow$ `IN PROGRESS`: Developer assigns task to self, creates feature branch (`feature/AWMS-X`).
2. `IN PROGRESS` $\rightarrow$ `TESTING`: Implementation code complete; unit/integration tests written; pushed to review branch.
3. `TESTING` $\rightarrow$ `DONE`: Definition of Done verified: 100% test pass rate, Bandit static scan reports 0 High/Medium vulnerabilities, peer code review signed off, documentation updated.

---

## 2. Daily Scrum Log: Sprint 1 Execution

### Daily Scrum #1 (Sprint 1 - Day 3)
- **Attendees:** Backend Developer, Security Engineer, Product Owner, Scrum Master.
- **Yesterday's Progress:**
  - Completed `AWMS-1` (Bcrypt password hashing and session management).
  - Implemented `AWMS-2` (RBAC authorization policies in `AccessPolicy` engine).
- **Today's Plan:**
  - Implement `AWMS-5` (Atomic multi-item stock reservation with PostgreSQL `SELECT ... FOR UPDATE` row locks).
  - Build `AWMS-3` (Catalog and Grid Location registry).
- **Blockers & Impediments:**
  - *Identified Blocker:* Initial reservation prototype attempted sequential un-ordered locking on `inventory_balances`, which posed a potential deadlock risk under concurrent multi-item orders.
  - *Resolution:* Enforced deterministic ordering by sorting balance IDs (`ORDER BY balance.id ASC`) prior to locking.

### Daily Scrum #2 (Sprint 1 - Day 7)
- **Yesterday's Progress:**
  - Verified `AWMS-5` under parallel test loads (`IT-02`). Zero inventory overselling observed.
  - Completed `AWMS-7` (Append-only security audit event logger).
- **Today's Plan:**
  - Finalize `AWMS-8` (Owner-filtered order receipt view with IDOR defense).
  - Configure Bandit static security scanner (`AWMS-9`).
- **Blockers:** None.

---

## 3. Daily Scrum Log: Sprint 2 Execution

### Daily Scrum #3 (Sprint 2 - Day 3)
- **Yesterday's Progress:**
  - Implemented `AWMS-10` (Atomic robot task assignment with partial unique index).
  - Created isolated reproduction fixture for race condition refactoring (`RF-02`).
- **Today's Plan:**
  - Implement `AWMS-11` (Discrete 2D movement simulator with BFS pathfinding and mutual cell exclusion).
  - Implement `AWMS-13` (Manager-only stock adjustments with mandatory audit reasons).
- **Blockers & Impediments:**
  - *Identified Blocker:* Robot A and Robot B attempting simultaneous swap across adjacent coordinates `(2,3) <-> (2,4)`.
  - *Resolution:* Added strict intermediate occupancy verification: a robot cannot enter cell `C` unless cell `C` is completely vacated and committed in the current transaction.

### Daily Scrum #4 (Sprint 2 - Day 8)
- **Yesterday's Progress:**
  - Completed `AWMS-14` (Emergency pause locking all movement loops).
  - Packaged application container with non-root UID 10001 (`AWMS-16`).
- **Today's Plan:**
  - Run Hypothesis property-based fuzzing suite (`AWMS-17`).
  - Deploy manifests to Minikube test namespace and verify service health.
- **Blockers:** None.
