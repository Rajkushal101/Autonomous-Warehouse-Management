# Phase 10: Sprint Review, Metrics & Retrospective

**Course:** 24CYS401 – Secure Software Engineering  
**System:** 23. Autonomous Warehouse Management System  
**Document Ref:** `docs/10_review_retrospective.md`  
**Marks:** 7 (part of Phase 10)  

---

## 1. Measured Scrum Metrics & Velocity

### Velocity Summary:
- **Sprint 1 Planned Commitment:** 27 Story Points
- **Sprint 1 Accepted Velocity:** **27 Story Points** (100% of committed scope met Definition of Done)
- **Sprint 2 Planned Commitment:** 29 Story Points
- **Sprint 2 Accepted Velocity:** **29 Story Points** (100% of committed scope met Definition of Done)
- **Total Project Velocity:** **56 Story Points** across 18 accepted user stories.

### Defect Tracking & Carry-Over:
- **Sprint 1 Defects Found:** 3 defects logged (`DEF-01` missing CSRF token in form, `DEF-02` unordered balance lock deadlock risk, `DEF-03` non-masked password in debug logs).
- **Sprint 1 Defects Resolved in Sprint:** 3 resolved.
- **Defects Carried Over from Sprint 1 to Sprint 2:** **0 Defects Carried Over**.
- **Sprint 2 Defects Found:** 3 defects logged (`DEF-04` race condition in concurrent assignment, `DEF-05` robot direct swap collision, `DEF-06` boundary fuzzing unhandled NoneType).
- **Sprint 2 Defects Resolved in Sprint:** 3 resolved.
- **Defects Carried Over from Sprint 2 to Final Release:** **0 Defects Carried Over**.

---

## 2. Sprint Burndown Trajectories

```
Sprint 1 Burndown:
Points |
  27   |* (Day 0)
  24   | \ * (Day 2)
  18   |   \ * (Day 4)
  11   |     \ * (Day 6)
   5   |       \ * (Day 8)
   0   |         \ * (Day 10)
       +----------------------
         0   2   4   6   8  10 Days

Sprint 2 Burndown:
Points |
  29   |* (Day 0)
  24   | \ * (Day 2)
  16   |   \ * (Day 4)
  10   |     \ * (Day 6)
   5   |       \ * (Day 8)
   0   |         \ * (Day 10)
       +----------------------
         0   2   4   6   8  10 Days
```

---

## 3. Sprint Review Outcomes

### Sprint 1 Review Demonstration:
- Demonstrated live human authentication across 5 distinct roles (`CUSTOMER`, `OPERATOR`, `MANAGER`, `ADMIN`, `AUDITOR`).
- Demonstrated customer placing multi-item order with instantaneous, atomic stock reservation in PostgreSQL.
- Demonstrated negative authorization test: customer attempting to view global inventory balances was rejected with HTTP 403.
- Stakeholder Feedback: *Accepted by Product Owner; reservation mechanics and audit trails approved for robot dispatch integration.*

### Sprint 2 Review Demonstration:
- Demonstrated autonomous robot dispatching with atomic row locking.
- Demonstrated multi-threaded race condition test (`IT-01`): two competing assignment calls yielded exactly 1 assignment and 1 clean 409 Conflict.
- Demonstrated 2D grid simulator step navigation from shelf to packing bay, verifying pickup and drop inventory movements committed to ledger.
- Demonstrated container security: non-root UID 10001, read-only rootfs, and clean Bandit scan.
- Stakeholder Feedback: *Full warehouse fulfillment workflow validated without defects.*

---

## 4. Sprint Retrospective & Actionable Improvements

The team conducted a formal Agile retrospective analyzing *What Went Well*, *What Could Be Improved*, and *Action Items*:

### What Went Well:
1. Adopting XP practices (TDD and automated CI security gates) caught concurrency and authorization bugs during development rather than in late-stage integration.
2. PostgreSQL row-level locks and partial unique constraints provided mathematically provable guarantees against race conditions.

### What Could Be Improved:
1. Initial unit tests focused heavily on positive happy paths before negative penetration assertions were added.
2. Simulating robot step movements initially caused tight CPU polling in tests before an event-driven tick clock was introduced.

### Mandatory Concrete Improvement Actions:
1. **Improvement Action 1 (Security-First TDD):**  
   *Action:* Mandate writing the negative security authorization test (e.g., asserting HTTP 403 Forbidden for unauthorized roles) *prior* to implementing the route handler for all future micro-endpoints.  
   *Owner:* Security Engineer & Backend Dev.  
   *Verified In:* Implemented during Sprint 2 for `AWMS-10` and `AWMS-13`.

2. **Improvement Action 2 (Automated Concurrency Barriers in Pre-Merge Gates):**  
   *Action:* Introduce automated multi-threaded synchronization barrier tests (`threading.Barrier`) directly into the pre-commit test runner to catch read-modify-write race conditions before pull request approval.  
   *Owner:* QA & DevSecOps.  
   *Verified In:* Implemented as integration test suite `tests/integration/test_concurrency.py`.
