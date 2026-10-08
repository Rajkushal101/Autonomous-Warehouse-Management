# Phase 9: Product Backlog & Jira Scrum Planning

**Course:** 24CYS401 – Secure Software Engineering  
**System:** 23. Autonomous Warehouse Management System  
**Document Ref:** `docs/09_sprint_plans.md`  
**Marks:** 7  

---

## 1. Jira Project Setup & Configuration

- **Project Name:** Autonomous Warehouse Secure Management Platform
- **Project Key:** `AWMS`
- **Board Type:** Scrum Board (`AWMS Board`)
- **Workflow Columns:** `TO DO` $\longrightarrow$ `IN PROGRESS` $\longrightarrow$ `TESTING` $\longrightarrow$ `DONE`
- **Estimation Statistic:** Story Points (Fibonacci scale: 1, 2, 3, 5, 8)
- **Import Artifact:** Full RFC-4180 CSV import file generated at [`docs/jira_import.csv`](file:///c:/Users/rajku/Downloads/SEM%207/secure%20software%20engineering/end%20sem%20lab%20exam/docs/jira_import.csv).
- *Lab Environment Note:* In the absence of an active external Atlassian cloud license during laboratory execution, the full sprint data model, issue keys (`AWMS-1` to `AWMS-18`), sprint allocations, and burndown trajectories are tracked locally in structured files with exact fidelity.

---

## 2. Sprint 1 Plan: Identity, Catalog, & Atomic Stock Reservation

- **Sprint Name:** Sprint 1 – Core Identity & Transactional Reservation
- **Duration:** 2 Weeks (simulated compressed execution)
- **Sprint Goal:**
  > *"Establish a secure, authenticated multi-role platform enabling customers to place orders with guaranteed atomic stock reservation, protected by PostgreSQL row locks and immutable audit logging."*
- **Committed Scope:** 9 User Stories (27 Story Points total)

| Issue Key | Story ID | Summary | Story Points | Assignee | Priority |
|---|---|---|---|---|---|
| `AWMS-1` | US-01 | Secure User Login and Session Expiry | 3 | Backend Dev | High |
| `AWMS-2` | US-02 | Role Management & RBAC Enforcement | 3 | Security Dev | High |
| `AWMS-3` | US-03 | Product Catalog & Grid Location Registry | 3 | Backend Dev | High |
| `AWMS-4` | US-04 | Inventory Balance Visibility | 2 | Frontend Dev | Medium |
| `AWMS-5` | US-05 | Atomic Stock Reservation for Customer Orders | 5 | Senior Backend | Highest |
| `AWMS-6` | US-06 | Robot Device Registration & Hashed Tokens | 3 | Systems Dev | High |
| `AWMS-7` | US-07 | Attributable Security Audit Logging | 3 | Security Dev | High |
| `AWMS-8` | US-08 | Customer Order Status Tracking | 2 | Frontend Dev | Medium |
| `AWMS-9` | US-09 | Reproducible Build & Static Security Scanning | 3 | DevOps Engineer | High |

**Sprint 1 Commitment Total:** **27 Story Points**

---

## 3. Sprint 2 Plan: Autonomous Robot Dispatch & Secure Deployment

- **Sprint Name:** Sprint 2 – Autonomous Dispatch, Collision Safety & Hardened Ops
- **Duration:** 2 Weeks (simulated compressed execution)
- **Sprint Goal:**
  > *"Implement atomic, collision-free robot task assignment and movement to the packing bay, validated by property fuzzing, and package the platform in hardened non-root containers with Kubernetes manifests."*
- **Committed Scope:** 9 User Stories (29 Story Points total)

| Issue Key | Story ID | Summary | Story Points | Assignee | Priority |
|---|---|---|---|---|---|
| `AWMS-10` | US-10 | Atomic Robot Task Assignment (Partial Unique Index) | 5 | Senior Backend | Highest |
| `AWMS-11` | US-11 | Collision-Safe Robot Movement Simulator | 5 | Robotics Dev | Highest |
| `AWMS-12` | US-12 | Robot Heartbeat & Stale Fault Recovery | 3 | Systems Dev | High |
| `AWMS-13` | US-13 | Authorized Manager Stock Adjustments | 3 | Backend Dev | High |
| `AWMS-14` | US-14 | Emergency Operational Pause & Order Cancellation | 3 | Systems Dev | High |
| `AWMS-15` | US-15 | Fulfillment Delivery to Packing Verification | 2 | QA Engineer | Medium |
| `AWMS-16` | US-16 | Container Hardening (Docker & Kubernetes) | 3 | DevOps Engineer | High |
| `AWMS-17` | US-17 | Automated CI/CD Pipeline & Boundary Fuzzing | 3 | DevSecOps | High |
| `AWMS-18` | US-18 | Operational Health & Security Metric Telemetry | 2 | DevOps Engineer | Medium |

**Sprint 2 Commitment Total:** **29 Story Points**  
**Total Product Backlog Commitment:** **56 Story Points**
