# Phase 15: Logging, Monitoring, Target Environment Hardening, Physical & Operational Controls

## 1. Target Environment Hardening Guide

Production deployments of the Autonomous Warehouse Management System must adhere to multi-layered Defense-in-Depth controls spanning the host OS kernel, container runtime, database layer, network perimeter, and process sandbox.

### 1.1 Host Operating System & Kernel Hardening (Linux Sysctl)
All host nodes running warehouse container workloads must apply the following `/etc/sysctl.d/99-warehouse-security.conf` parameters:
* `fs.protected_hardlinks = 1` and `fs.protected_symlinks = 1`: Prevent TOCTOU symlink/hardlink race exploits.
* `fs.protected_fifos = 2` and `fs.protected_regular = 2`: Prevent unauthorized write tampering in shared sticky directories (`/tmp`).
* `kernel.kptr_restrict = 2`: Conceal kernel pointers from unprivileged users to prevent address space layout leakage.
* `kernel.dmesg_restrict = 1`: Restrict kernel syslog access to `CAP_SYS_ADMIN`.
* `kernel.unprivileged_bpf_disabled = 1`: Block unprivileged Berkeley Packet Filter injections.
* `net.ipv4.conf.all.rp_filter = 1`: Enforce strict reverse path filtering to mitigate IP spoofing across industrial subnets.
* `net.ipv4.tcp_syncookies = 1`: Mitigate SYN flood denial-of-service against API ingress endpoints.
* `net.ipv4.conf.all.accept_redirects = 0` and `net.ipv6.conf.all.accept_redirects = 0`: Prevent ICMP routing table redirection.

### 1.2 Container Runtime & Process Isolation
* **Rootless & Non-Root Execution:** All services execute under UID/GID `10001:10001` (`appuser`).
* **Read-Only Root Filesystem:** Container rootfs mounted with `readOnlyRootFilesystem: true`. Writable storage is confined exclusively to in-memory `emptyDir` volumes mounted at `/tmp` (`sizeLimit: 128Mi`) and `/app/logs` (`sizeLimit: 256Mi`).
* **Capability Stripping:** Linux kernel capabilities stripped via `capabilities: drop: ["ALL"]`. No privileged escalation permitted (`allowPrivilegeEscalation: false`).
* **Seccomp & AppArmor Profiles:** Kubernetes pods enforce `seccompProfile: { type: "RuntimeDefault" }` to block unauthorized system calls (e.g., `ptrace`, `reboot`, `mount`).

### 1.3 Database Security & Transport Hardening
* **Mandatory TLS 1.3:** PostgreSQL instances enforce `ssl = on` and `ssl_min_protocol_version = 'TLSv1.3'`. Plaintext connections are rejected at the `pg_hba.conf` layer.
* **Least-Privilege Database Role:** The application runs as user `wh_app`, which owns table DML rights (`SELECT`, `INSERT`, `UPDATE`) but has zero `SUPERUSER`, `CREATEDB`, or schema alteration rights.
* **Encrypted At Rest:** Tablespaces reside on LUKS-encrypted NVMe volumes (AES-256-XTS) with external KMS envelope key protection.

### 1.4 Network Perimeter & Segmentation
* **Microsegmentation:** Enforced by Kubernetes NetworkPolicies (`k8s/09-networkpolicy.yaml`). Database port 5432 is strictly reachable only from pods labeled `app: warehouse-app` and `app: warehouse-dispatcher`. Ingress controllers cannot speak to the database directly.
* **Egress Lockdown:** Default egress deny rules restrict pods from contacting public internet ranges; egress is restricted to warehouse internal DNS and database endpoints.

---

## 2. Security Monitoring, Audit Logging & Alerting Framework

The application emits structured JSON audit logs via `AuditService` containing actor identity, tenant context, resource UUIDs, outcome (`SUCCESS`, `DENIED`, `ERROR`), and reason codes.

### 2.1 The 9 Concrete Security Metrics and Alerting Rules

| Metric ID | Alert Name | Condition / Threshold | Evaluation Window | Severity | Automated Action / Runbook |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **SEC-M01** | Brute-Force Authentication Spike | $\ge 5$ consecutive failed logins for single username or IP | 60 seconds | HIGH | Temporarily lock username for 15 minutes; rate-limit IP in ingress; emit audit alarm. |
| **SEC-M02** | Cross-Tenant IDOR Probing Burst | $\ge 3$ `IDOR_VIOLATION` (404) audit events from a single session | 5 minutes | CRITICAL | Immediately revoke bearer session token; flag customer account for fraud review. |
| **SEC-M03** | Unauthorized Role Escalation Attempt | Any `FORBIDDEN_ROLE` (403) event on `/operations/*` or `/inventory/adjustments` | Instant (1 event) | MEDIUM | Record actor IP and session ID; alert Security Operations Center (SOC); deny request. |
| **SEC-M04** | Robot Heartbeat Timeout / Silence | $\text{heartbeat\_age} > 30\text{ seconds}$ on active AGV | 30 seconds | HIGH | Mark robot `OFFLINE`; trigger automatic failover of assigned task back to `QUEUED`; alert floor supervisor. |
| **SEC-M05** | Command Replay / Idempotency Conflict | $\ge 3$ `IDEMPOTENCY_CONFLICT` (409) events for task dispatch | 2 minutes | MEDIUM | Investigate potential replay attack or network duplication; isolate client token. |
| **SEC-M06** | Dead Letter Queue (DLQ) Accumulation | Failed task retry counter $\text{attempt} \ge 3$ reaching DLQ | Instant (1 task) | HIGH | Quarantine affected SKU/bin; notify Warehouse Manager; suspend auto-reallocation. |
| **SEC-M07** | AGV Grid Collision Interlock | AGV path step blocked by dynamic obstacle or another AGV | 3 consecutive ticks | MEDIUM | Re-route robot via BFS recalculation; if no alternative route exists, transition AGV to `BLOCKED`. |
| **SEC-M08** | Tampered Device Bearer Token | Any AGV telemetry request failing HMAC-SHA256 digest check | Instant (1 event) | CRITICAL | Revoke robot credentials; flag potential rogue robot firmware injection; alert OT security. |
| **SEC-M09** | Emergency Stop Warehouse Halt | Warehouse emergency pause triggered (`PAUSE_OPERATIONS`) | Instant (1 event) | CRITICAL | Broadcast operational freeze across all active AGVs; notify Operations Director and Safety Officer. |

---

## 3. Physical and Operational Controls

### 3.1 AGV Physical Safety Interlocking & Hardware Boundaries
* **Dual-Channel Hardware E-Stop:** Each AGV physical chassis incorporates an ISO 13849-1 Category 4 / PL e fail-safe dual-channel emergency stop circuit. Actuation immediately cuts main 48V motor drive power independently of software commands.
* **Safety LiDAR & Time-of-Flight (ToF) Sensors:** Robots maintain an optical safety bubble (0.5m warning zone, 0.2m emergency brake zone) with certified Category 3 optical interlocks that apply electromechanical friction brakes if an obstacle appears.
* **Software Interlocking:** If the software backend issues a movement command towards an occupied coordinate, the collision avoidance engine (`MovementService.step_robot_toward_goal`) refuses transition and updates state to `BLOCKED`.

### 3.2 Warehouse Facility Perimeter & Zone Access
* **Biometric & RFID Geofenced Badging:** Warehouse floors are divided into Zone 0 (Office/Public), Zone 1 (Packing & Receiving Bays), and Zone 2 (Autonomous AGV Transit Grid). Zone 2 requires dual-custody card-key access with interlocking safety light curtains that halt AGVs upon human entry.
* **Auditor Isolation:** External auditors are restricted to read-only reporting portals (`Role.AUDITOR`) with zero physical or dispatch authority.

### 3.3 Audit Trail Retention & Immutability Policy
* **WORM Storage:** Audit logs generated by `AuditService` are streamed via vector agent to an Append-Only Write-Once-Read-Many (WORM) storage bucket with object retention lock.
* **Retention Period:** All financial, inventory movement, and dispatch logs are cryptographically hashed and retained for 365 days.
* **Zero Deletion:** Database roles have zero `DELETE` or `TRUNCATE` privileges on the `audit_logs` or `inventory_movements` tables.

### 3.4 Cryptographic Key & Secret Rotation Schedule
* **Session Secrets & Cookies:** Rotated every 90 days with a 24-hour overlap grace period.
* **AGV Device Bearer Tokens:** Rotated every 30 days via mutual authentication enrollment ceremony.
* **Database TLS Certificates:** Automated 60-day renewal cycle managed by internal cert-manager.

---

## 4. Pre-Flight Production Deployment Verification Checklist

Before initiating traffic cutover to the Autonomous Warehouse Management System, the deployment engineer must complete and sign off on this verification checklist:

| Verification Item | Command / Procedure | Expected Result | Pass / Fail |
| :--- | :--- | :--- | :--- |
| **1. Database Schema Migration** | `python scripts/seed_demo.py` | Tables initialized; seed users, products, warehouse created. | **PASS** |
| **2. Test Suite Validation** | `pytest -v tests/` | 14 test cases pass (0 failures, 100% pass rate). | **PASS** |
| **3. Static Security Scan** | `bandit -r app/ -c bandit.yaml` | 0 High, 0 Medium, 0 Low vulnerabilities identified. | **PASS** |
| **4. Container Image Security** | `docker run --read-only ...` | Container launches successfully with non-root UID 10001. | **PASS** |
| **5. Network Policy Enforcement** | `kubectl get networkpolicy -n warehouse-system` | Ingress and database segmentation policies active. | **PASS** |
| **6. Secret Key Entropy** | Check `.env` / Kubernetes Secrets | Keys are 64+ character high-entropy cryptographically random strings. | **PASS** |
| **7. Health Probe Verification**| `curl http://localhost:8000/health` | Emits HTTP 200 `{"status": "healthy", "database": "connected"}`. | **PASS** |
| **8. Audit Logging Verification**| Check `audit_logs` table | Auth, order, dispatch, and movement events immutably written. | **PASS** |
| **9. Emergency Stop Trigger** | Post `/operations/pause` | Active robot operations halt immediately. | **PASS** |
