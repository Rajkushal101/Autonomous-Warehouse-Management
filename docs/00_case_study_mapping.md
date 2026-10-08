# Case Study Mapping & Problem Interpretation

**Course:** 24CYS401 – Secure Software Engineering End Semester Laboratory Examination  
**Assigned Question:** 23. Autonomous Warehouse Management System  
**Document Ref:** `docs/00_case_study_mapping.md`

---

## 1. Problem Source Analysis

The assigned problem statement consists of two consecutive source parts provided in the examination paper:
```
23. Autonomous Warehouse Management System
Develop a warehouse platform where automated robots move goods.
The system manages:
  • Inventory
  • Robot registration
  • Robot tasks
  • Pickup/drop locations
  • Order fulfillment
  • Robot status

Example Workflow:
  Customer Order 
       ↓ 
  Warehouse System 
       ↓ 
  Assign Robot 
       ↓ 
  Pick Item 
       ↓ 
  Move Item 
       ↓ 
  Packing Area

Security Challenges:
  • Unauthorized robot commands
  • Inventory manipulation
  • Race conditions
  • Robot collision / command conflicts
  • Privilege escalation
  • Availability
```

---

## 2. General Case-Study Instruction Compliance

The examination instruction sheet contains the explicit **General Case-Study Instruction**:
> *"The problem statement/system to be used for the examination will be provided separately by the examiner or assigned to the student/team. Students must apply every phase to that same system. No single domain (examination, banking, hospital, e-commerce, etc.) is prescribed in this question paper."*

Therefore, the activities, structure, rigor, and deliverable counts of all 16 phases are preserved in full, adapting academic exam domain examples into their direct Autonomous Warehouse counterparts as mapped below:

| Generic Example in Instructions | Warehouse System Domain Equivalent | Rationale |
|---|---|---|
| **Student** | **Customer** (Order Requester) | Submits orders, tracks personal fulfillment progress; has zero authority over stock or robot tasks. |
| **Faculty** | **Warehouse Manager / Fulfillment Operator** | Manages stock balances, registers items/locations/robots, oversees task assignments. |
| **Administrator** | **System Administrator** | Manages human user accounts, enforces RBAC, rotates system credentials, inspects health. |
| **Auditor** *(Additional justified actor)* | **Security Auditor** | Reviews append-only security logs, tracks compliance and anomalies without mutation power. |
| **Attend Examination and Submit Answers** | **Place Order and Submit Fulfillment Request** | Core transactional submission requiring atomic resource allocation and state progression. |
| **Examination Component** | **Order & Task Orchestration Engine** | Coordinates business requests, allocates reservations, and schedules dispatching. |
| **Evaluation and Results** | **Fulfillment Validation & Packing Delivery** | Validates final delivery at packing stations and calculates order completion. |
| **Student Exam Screen** | **Customer Order & Tracking Screen** | Order creation, item selection, real-time fulfillment status display. |
| **Faculty Examination Management** | **Warehouse Operations & Inventory Console** | Inventory balances, robot task dispatch, fault pause/resume, stock adjustment. |
| **Results Screen** | **Fulfillment Results & Packing Dispatch View** | Final delivery proof, ledger audit trail, exception reporting. |
| **Modifying another student's marks** | **Unauthorized stock adjustment or tampering with robot task commands** | High-impact integrity violation altering physical or ledger reality. |
| **Accessing a question paper early** | **Accessing another customer's restricted order or sniffing private robot credentials** | Confidentiality breach violating object-level ownership or device trust. |

---

## 3. Scope Boundaries and Implementation Decisions

1. **Autonomous Robot Movement Model:** A deterministic, bounded 2D warehouse grid with discrete coordinate steps (`(x,y)`), blocked static shelving obstacles, designated pickup bays, and off-corridor packing bays. Because physical robotics hardware (ROS2 nodes, LiDAR, emergency-stop contactors) is not part of the laboratory software stack, discrete software simulation is executed with ACID database-backed locks.
2. **Fulfillment Boundary:** Fulfillment completes upon successful transfer to the **Packing Area** with atomic inventory deduction and delivery ledger commitment. External parcel dispatch, carrier logistics, and customer billing are outside the problem statement scope.
3. **Architecture Style:** Layered Modular Monolith (FastAPI + SQLAlchemy + PostgreSQL transaction isolation) with an independent background simulator worker, balancing strict transactional concurrency guarantees with zero distributed-network split-brain vulnerabilities.
