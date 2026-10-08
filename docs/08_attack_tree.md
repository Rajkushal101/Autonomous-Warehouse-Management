# Phase 8: Attack Tree & Threat Vector Modeling

**Course:** 24CYS401 – Secure Software Engineering  
**System:** 23. Autonomous Warehouse Management System  
**Document Ref:** `docs/08_attack_tree.md`  
**Marks:** 6  

---

## 1. Selected Critical Attacker Goal

In compliance with the examination instruction mapping (*"modifying another student's marks / accessing question papers"* → *"unauthorized stock adjustment or unauthorized robot command manipulation"*), the root attacker goal is selected as:

$$\mathbf{AT-00}: \text{Cause an unauthorized or conflicting robot movement that corrupts warehouse fulfillment}$$

This goal encapsulates the core security challenges highlighted in the exam problem statement:
- Unauthorized robot commands
- Robot collision and command conflicts
- Race conditions during assignment
- Inventory manipulation

---

## 2. Attack Tree Structure & AND/OR Relationships

```
AT-00: Cause unauthorized/conflicting robot movement (ROOT) [OR]
  ├── AT-01: Exploit Privileged Human Session [AND]
  │     ├── AT-11: Compromise Operator/Manager Credential [OR]
  │     │     ├── AT-111: Credential stuffing / brute-force password
  │     │     └── AT-112: Steal active session cookie via XSS/MitM
  │     └── AT-12: Forge Privileged Task Dispatch Command [LEAF]
  ├── AT-02: Direct API Authorization Bypass [AND]
  │     ├── AT-21: Invoke Task Assignment API as Unprivileged Customer (BOLA/BAC) [LEAF]
  │     └── AT-22: Discover Valid Target Task & Robot UUIDs [LEAF]
  ├── AT-03: Exploit Assignment Race Condition Under Concurrency [AND]
  │     ├── AT-31: Flood System with Simultaneous Competing Assignment Requests [LEAF]
  │     └── AT-32: Bypass Database Concurrency Locks (Duplicate Active Task) [LEAF]
  └── AT-04: Compromise Robot Device Machine Trust Boundary [AND]
        ├── AT-41: Forge or Extract Robot Device Bearer Token [OR]
        │     ├── AT-411: Sniff unencrypted local network traffic
        │     └── AT-412: Extract token from hardcoded source or config files
        └── AT-42: Inject Replayed or Out-of-Sequence Movement Acknowledgment [LEAF]
```

---

## 3. Detailed Root-to-Leaf Attack Paths

### Path 1: Credential Brute-Force & Session Hijack (AT-00 → AT-01 → AT-11 → AT-111 → AT-12)
- **Attacker Prerequisites:** Network access to `/auth/login`; access to common dictionary passwords.
- **Attack Vector:** High-volume automated brute-force attack against operator usernames.
- **Preventive Controls:**
  - Password hashing via bcrypt with high work factor ($12$ rounds).
  - Centralized rate limiting throttling IP/username after 5 consecutive failures.
- **Detective Controls:**
  - Automated security audit event `LOGIN_FAILED` generated on every unsuccessful attempt.
  - Alert triggered when failure threshold exceeded.
- **Verification Test:** `tests/unit/test_authz.py::test_login_rate_limiting`.

### Path 2: Broken Object-Level & Role Authorization (AT-00 → AT-02 → AT-21 → AT-22)
- **Attacker Prerequisites:** Valid authenticated session with `CUSTOMER` role.
- **Attack Vector:** Customer intercepts order UUID and directly issues HTTP POST to `/api/tasks/{task_id}/assign` with a robot ID payload.
- **Preventive Controls:**
  - Centralized `AccessPolicy.require_role([Role.OPERATOR, Role.MANAGER])` executed before request reaches service layer.
- **Detective Controls:**
  - HTTP 403 Forbidden generated; immutable `audit_events` entry recorded attributing attempted privilege escalation to customer UUID.
- **Verification Test:** `tests/unit/test_authz.py::test_customer_cannot_assign_robot`.

### Path 3: Concurrent Assignment Race Condition (AT-00 → AT-03 → AT-31 → AT-32)
- **Attacker Prerequisites:** Two concurrent operator sessions (or scripted concurrent HTTP requests).
- **Attack Vector:** Transmitting two simultaneous assignment requests for the same idle robot within a 5-millisecond window.
- **Preventive Controls:**
  - Database row lock: `SELECT * FROM robots WHERE id = :id FOR UPDATE`.
  - Database partial unique index: `idx_single_active_task_per_robot` on `tasks(robot_id) WHERE state IN ('ASSIGNED', 'TO_PICKUP', 'PICKING', 'TO_DROP', 'DROPPING', 'BLOCKED')`.
- **Detective Controls:**
  - Database unique constraint violation caught; second request cleanly rejected with HTTP 409 Conflict.
- **Verification Test:** `tests/integration/test_concurrency.py::test_concurrent_robot_assignment`.

### Path 4: Rogue Device Telemetry & Command Injection (AT-00 → AT-04 → AT-41 → AT-412 → AT-42)
- **Attacker Prerequisites:** Network access to internal device subnet; attempt to discover hardcoded API keys.
- **Attack Vector:** Attacker scans code repository or network captures for device tokens, then transmits forged pickup/drop acknowledgments out-of-order.
- **Preventive Controls:**
  - Zero hardcoded secrets in source code (enforced by Bandit scanning).
  - High-entropy CSPRNG device tokens stored only as SHA-256 digests in `robots` table.
  - Command validation checks monotonic `sequence_number` and asserts robot is currently in expected state before accepting telemetry.
- **Detective Controls:**
  - Replayed commands rejected with HTTP 409 Conflict; anomaly event logged.
- **Verification Test:** `tests/integration/test_concurrency.py::test_replay_command_acknowledgment`.
