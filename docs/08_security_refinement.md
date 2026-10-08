# Phase 8: Security Architecture Refinement (Architecture v2)

**Course:** 24CYS401 – Secure Software Engineering  
**System:** 23. Autonomous Warehouse Management System  
**Document Ref:** `docs/08_security_refinement.md`  
**Marks:** 6 (part of Phase 8)  

---

## 1. Attack Tree Findings & High-Risk Threat Selection

Based on the attack tree analysis and the quantitative STRIDE scoring matrix in Phase 7, the three highest-risk threats requiring architectural refinement are:

1. **T13 / AT-02 (Risk Score: 20): Unauthorized Robot Command Execution**
   - *Attack:* Malicious user invoking internal robot dispatch or movement endpoints directly.
2. **T04 / AT-03 (Risk Score: 16): Assignment Race Condition & Double Allocation**
   - *Attack:* Simultaneous dispatch requests causing one robot to receive conflicting simultaneous tasks.
3. **T03 / AT-01 (Risk Score: 15): Inventory Manipulation & Balance Falsification**
   - *Attack:* Arbitrary balance changes bypassing transaction ledgers or leaving negative stock.

---

## 2. Before vs. After Architectural Comparison

| Architectural Aspect | Initial Design (Vulnerable Architecture v1) | Refined Design (Secure Architecture v2) |
|---|---|---|
| **API Authorization** | Ad-hoc checks scattered inside route controllers; some routes lack role decorators. | **Centralized Policy Enforcement (`AccessPolicy`):** Declarative, deny-by-default role & object-ownership guards executed prior to any service invocation. |
| **Concurrency & Assignment** | Naive read-then-write: `SELECT * FROM robots WHERE status='IDLE'` followed by `UPDATE robots SET status='BUSY'`. | **Deterministic Row Locks + Partial Unique Index:** `SELECT ... FOR UPDATE` + PostgreSQL partial unique constraint guaranteeing max 1 active task per robot. |
| **Request Idempotency** | Absent; network retries re-execute mutations and trigger duplicate tasks. | **Idempotency Filter (`idempotency_records`):** Enforces unique key per actor/endpoint with SHA-256 payload hash verification. |
| **Device Trust & Commands** | Generic API key or device serial passed in JSON body without cryptographic verification. | **Cryptographic Device Digests + State Verification:** Bearer tokens validated against SHA-256 hashes; allowlisted commands with monotonic sequence tracking. |
| **Inventory Accounting** | Balances updated directly without audit logging; negative balances possible. | **Immutable Movement Ledger (`inventory_movements`):** Atomic row-level locking with SQL `CHECK (on_hand >= 0)` constraints and mandatory reason codes. |
| **Audit Logging** | Optional console output via standard `print()` statements. | **Append-Only Forensic Trail (`audit_events`):** In-transaction immutable audit logging; database user barred from `UPDATE`/`DELETE`. |
| **Runtime Privileges** | Containers running as default `root` (UID 0) with writable root filesystems. | **Hardened Non-Root Container:** UID 10001, dropped Linux capabilities, read-only root filesystem with explicit `/tmp` volume mounts. |

---

## 3. Refined Architecture v2 Diagram & Controls Summary

Architecture v2 incorporates these mitigations as first-class architectural primitives, directly referenced in SRS (`SR-01` to `SR-13`), DFD (`TB1` to `TB5`), and the implementation test suite.
