# Phase 1: Agile Process & Development Approach

**Course:** 24CYS401 – Secure Software Engineering  
**System:** 23. Autonomous Warehouse Management System  
**Document Ref:** `docs/01_agile.md`  
**Marks:** 6  

---

## 1. Selected Agile Methodology & Justification

### Selected Approach: Scrum augmented with Extreme Programming (XP) Practices
For developing the Autonomous Warehouse Management System, a hybrid framework combining **Scrum management rituals** with **Extreme Programming (XP) technical engineering practices** was selected.

### Justification
1. **Iterative Increment Delivery:** The system encompasses multiple distinct domains: user authentication, physical inventory management, robot device control, and fulfillment dispatch. Dividing the project into two distinct 2-week iterations (Sprint 1: Core Catalog, Orders, & Atomic Stock Reservation; Sprint 2: Autonomous Robot Dispatch, Collision-Safe Movement, & Hardened Deployment) provides early feedback on critical transactional invariants.
2. **XP Technical Practices for Security:** Standard Scrum focuses on project delivery velocity, which can inadvertently cause developers to bypass non-functional security constraints under deadline pressure. Incorporating XP disciplines:
   - **Test-Driven Development (TDD):** Writing automated unit/integration tests before writing business logic ensures state machine transitions and authorization predicates cannot be bypassed.
   - **Continuous Integration (CI):** Mandatory automated static analysis (Bandit) and automated test execution on every branch merge catches security defects early.
   - **Refactoring:** Systematic identification and remediation of security weaknesses (e.g., removing race-prone read-modify-write patterns) without altering observable business behavior.
   - **Collective Code Ownership & Clear Role Definitions:** Explicit permissions and separation of concerns enforce defense-in-depth across the entire codebase.

---

## 2. Mapping of Agile Manifesto Principles

The 12 Agile Manifesto principles are applied specifically to this security-critical warehouse platform as follows:

| # | Agile Manifesto Principle | Concrete Warehouse Project Application |
|---|---|---|
| **1** | *Our highest priority is to satisfy the customer through early and continuous delivery of valuable software.* | Delivering a functioning, authenticated order reservation loop in Sprint 1 allows warehouse operators to validate stock integrity before robot dispatching is connected in Sprint 2. |
| **2** | *Welcome changing requirements, even late in development. Agile processes harness change for the customer's competitive advantage.* | When warehouse shelving layouts or robot collision tolerances change, data models and collision validators are updated in isolated modules without breaking the core fulfillment pipeline. |
| **3** | *Deliver working software frequently, from a couple of weeks to a couple of months, with a preference to the shorter timescale.* | Delivering two working software increments: Increment 1 proves transactional reservation and tamper-evident audit; Increment 2 delivers automated robot task orchestration and Kubernetes manifests. |
| **4** | *Business people and developers must work together daily throughout the project.* | Fulfillment managers (specifying picking rules) and software engineers (implementing atomic database locks) continuously review business constraints to prevent inventory overselling. |
| **5** | *Build projects around motivated individuals. Give them the environment and support they need, and trust them to get the job done.* | Security responsibilities (auditor, developer, ops maintainer) are clearly defined, giving team members ownership over isolated domains (e.g., identity policy, robot path planning). |
| **6** | *The most efficient and effective method of conveying information to and within a development team is face-to-face conversation.* | Conducted daily scrums to synchronously address blockers, race conditions, and API contract dependencies between the web portal and the robot dispatch worker. |
| **7** | *Working software is the primary measure of progress.* | Progress is measured strictly by functional, passing automated tests (e.g., `IT-01` verifying concurrency locks, `ST-01` end-to-end fulfillment) rather than merely documented design diagrams. |
| **8** | *Continuous attention to technical excellence and good design enhances agility.* | Employing strict architectural patterns (Layered Monolith, Unit of Work, Command Pattern) and enforcing automated static security gates prevents technical debt and vulnerability accumulation. |

---

## 3. Planned Refactoring Opportunities (RF-01 & RF-02)

To address the examination requirement for demonstrating code refactoring, two specific opportunities were planned, with full code before/after evidenced in Phase 12:

### Refactoring 1: Centralized Authorization & Strong Input Validation (RF-01)
- **Problem (Initial Weak Structure):** Route handler functions directly parse raw user JSON and execute database updates without role verification or ownership predicates. A malicious customer can manipulate task assignments or inject unexpected parameters.
- **Planned Target Structure:** Decouple HTTP routing from business authorization. Introduce Pydantic v2 schemas for strict input sanitization, a centralized `AccessPolicy` service for deny-by-default role checks, and dedicated domain services (`TaskAssignmentService`).
- **Success Criteria:** Any unauthenticated or unauthorized role invocation (e.g., `CUSTOMER` attempting to assign a robot) yields an immediate HTTP 403 Forbidden with zero database side-effects.

### Refactoring 2: Atomic Transactional Locking & Concurrency Protection (RF-02)
- **Problem (Initial Weak Structure):** Naive read-then-update logic (`SELECT robot ... UPDATE robot SET status='BUSY'`) where competing requests read the same idle robot before either commits, creating duplicate task assignments and conflicting physical robot routes (Race Condition).
- **Planned Target Structure:** Enforce PostgreSQL row-level locks (`SELECT ... FOR UPDATE`), partial unique database index (`CREATE UNIQUE INDEX idx_one_active_task_per_robot ON tasks(robot_id) WHERE state IN ('ASSIGNED', 'TO_PICKUP', 'PICKING', 'TO_DROP', 'DROPPING')`), and an actor-scoped Idempotency Record.
- **Success Criteria:** Automated concurrency test (`IT-01`) simultaneously launches two competing assignment requests for the same robot; exactly one succeeds with HTTP 200/201 and the second is safely rejected with HTTP 409 Conflict.

---

## 4. Limitations and Risks of Agile for Security-Critical Systems & Mitigations

| # | Agile Risk / Limitation | Potential Negative Impact | Project Mitigation Strategy |
|---|---|---|---|
| **R1** | **Velocity Pressure Compromising Security Controls** | Agile teams under sprint deadline pressure frequently defer non-functional requirements (cryptographic salt rotation, rate limiting, least-privilege RBAC) to later backlog items, leaving critical vulnerabilities in production. | **Security-Baked Definition of Done (DoD):** A user story cannot transition to `DONE` unless it passes automated static analysis (`bandit`), achieves 100% pass rate on negative authorization unit tests, and satisfies CIA acceptance criteria. |
| **R2** | **Incremental Design Drifts Causing Architectural Flaws** | Frequent emergent changes to data models or API routes can introduce trust boundary violations, inconsistent validation, or state synchronization bugs between the web portal and robot controllers. | **Formal Threat Modeling & Traceability Register:** STRIDE threat analysis and DFD trust boundary models are maintained as version-controlled engineering assets. Any schema modification triggers a review of the threat register (`docs/07_threats.csv`). |
| **R3** | **Single Developer / Lab Timebox Constraints** | In a 3-hour laboratory timebox, distributed multi-person sprint simulation can lead to fabricated metrics or lost focus. | **Standardized ID Convention & Lean Modular Architecture:** Utilizing clear canonical IDs (`FR`, `SR`, `UC`, `T`, `US`, `TK`, `DEF`) and a clean modular architecture allows rapid, verifiable implementation and transparent metric tracking. |

---

## 5. Definition of Ready (DoR) and Definition of Done (DoD)

### Definition of Ready (DoR)
A User Story is ready for sprint backlog inclusion only if:
1. User story format conforms to: *"As a [role], I want [capability] so that [business value]"*.
2. Explicit MoSCoW priority and estimated story points are assigned.
3. Testable acceptance criteria with both positive and negative security assertions are documented.
4. Data model dependencies and trust boundary impacts are identified.

### Definition of Done (DoD)
A User Story is accepted as `DONE` only if:
1. Business logic implemented in appropriate service layer according to coding standards.
2. Automated unit and integration tests written and passing.
3. Negative authorization tests (unauthorized role rejection) passing.
4. Zero high/medium findings from automated security scan (`bandit`).
5. No hard-coded credentials or secrets present in code or commit diff.
6. Documentation, user story status, and traceability matrix updated.
