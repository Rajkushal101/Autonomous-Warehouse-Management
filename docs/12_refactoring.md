# Phase 12: Secure Coding & Refactoring Evidence

**Course:** 24CYS401 – Secure Software Engineering  
**System:** 23. Autonomous Warehouse Management System  
**Document Ref:** `docs/12_refactoring.md`  
**Marks:** 4  

---

## 1. Primary Module Identification

The assessed primary software module is **Secure Robot Task Assignment** implemented in:
$$\text{\texttt{app/services/task\_service.py}} \quad \longrightarrow \quad \text{\texttt{TaskAssignmentService.assign\_robot\_to\_task()}}$$
Supported by the centralized authorization engine in `app/services/policy.py` (`AccessPolicy`) and transactional concurrency row locking in `app/repositories/base.py`.

---

## 2. Refactoring Opportunity 1: Centralized Authorization & Strict Schema (RF-01)

### Problem in Initial Version:
The initial route handler accepted raw, unvalidated JSON payloads directly from untrusted clients and executed database updates without inspecting user roles or session state. An unprivileged customer could pass a task ID and arbitrarily take control of physical warehouse robots.

### Code Comparison:
```python
# ==================== BEFORE (Vulnerable) ====================
def vulnerable_assign(request_data, db):
    # Missing authorization! Any user can assign robots
    task_id = request_data.get("task_id")
    robot_id = request_data.get("robot_id")
    # Missing input bounds check...

# ==================== AFTER (Refactored & Secure) ====================
class TaskAssignmentService:
    @staticmethod
    def assign_robot_to_task(db: Session, actor: User, task_id: str, robot_id: str, idempotency_key: str):
        # 1. Centralized Deny-by-Default Role Authorization
        AccessPolicy.require_role(actor, [Role.OPERATOR, Role.MANAGER, Role.ADMIN], db=db, action_name="ASSIGN_ROBOT_TASK")
        
        # 2. Strict Input Bounds & UUID Format Checking
        if not task_id or not robot_id or not idempotency_key or len(idempotency_key) > 64:
            raise WarehouseSecurityException("Invalid parameters", code="INVALID_PARAMETERS", status_code=422)
```

### Security Justification:
- Enforces Principle of Least Privilege and Complete Mediation.
- Prevents Broken Object-Level Authorization (BOLA) and Broken Function-Level Authorization (BFLA).
- Verified via unit test: `tests/unit/test_authz.py::test_customer_cannot_assign_robot`.

---

## 3. Refactoring Opportunity 2: Atomic Transaction Locking & Concurrency Protection (RF-02)

### Problem in Initial Version:
The initial implementation performed an unlocked read followed by an update:
```python
robot = db.query(Robot).filter_by(id=robot_id).first()
if robot.status == "IDLE":
    # RACE CONDITION WINDOW: Another thread reads robot as 'IDLE' before this commits!
    robot.status = "BUSY"
    task.robot_id = robot.id
    db.commit()
```
Under concurrent load, two competing operators (or automated scripts) assign two distinct tasks to the same robot simultaneously, corrupting physical route planning and dispatching conflicting commands.

### Code Comparison:
```python
# ==================== AFTER (Refactored with ACID Locks & Partial UQ Index) ====================
# 1. Acquire exclusive pessimistic row locks inside single transaction
task = db.query(Task).filter(Task.id == task_id).with_for_update().first()
robot = db.query(Robot).filter(Robot.id == robot_id).with_for_update().first()

# 2. Re-verify eligibility under lock
if robot.status != RobotStatus.IDLE.value:
    raise WarehouseSecurityException(f"Robot {robot.serial_number} is already {robot.status}", code="ROBOT_BUSY", status_code=409)

# 3. Verify Mutual Task Exclusion
existing_active = db.query(Task).filter(Task.robot_id == robot.id, Task.state.in_(ACTIVE_TASK_STATES)).first()
if existing_active:
    raise WarehouseSecurityException("Robot already owns active task", code="ROBOT_ALREADY_ASSIGNED", status_code=409)

# 4. Atomic State Transition + Monotonic Command Generation
task.robot_id = robot.id
task.state = TaskState.ASSIGNED.value
robot.status = RobotStatus.BUSY.value
db.add(Command(robot_id=robot.id, task_id=task.id, sequence_number=1, ...))
db.commit()
```

### Security Justification:
- Eliminates race conditions and Time-of-Check to Time-of-Use (TOCTOU) flaws.
- In conjunction with PostgreSQL's partial unique index, provides absolute mathematical prevention against multi-task assignment.
- Verified via integration test: `tests/integration/test_concurrency.py::test_concurrent_robot_assignment`.

---

## 4. Verification Evidence & Test Summary

| Refactoring ID | Target Flaw | Verification Test Function | Observed Execution Result |
|---|---|---|---|
| **RF-01** | Missing Role Authorization | `tests/unit/test_authz.py::test_customer_cannot_assign_robot` | PASS (HTTP 403 Forbidden received; 0 DB state changes) |
| **RF-02** | Concurrency Race Condition | `tests/integration/test_concurrency.py::test_concurrent_robot_assignment` | PASS (Thread 1 succeeds 200 OK; Thread 2 rejected 409 Conflict) |
