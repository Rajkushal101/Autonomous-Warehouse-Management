"""
generate_srs_document.py
Generates the formal Software Requirements Specification (SRS) for:
System 23: Autonomous Warehouse Management System (AWMS)
In accordance with IEEE Std 830-1998 / ISO/IEC/IEEE 29148:2018 Standards.

Outputs:
1. SRS_DOCUMENT.docx (Professional Word Document with tables, callouts, and diagrams)
2. SRS_DOCUMENT.md (Complete Markdown Specification)
"""

import os
import sys
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GRAPHS_DIR = os.path.join(BASE_DIR, "graphs")
DOCX_OUTPUT = os.path.join(BASE_DIR, "SRS_DOCUMENT.docx")
MD_OUTPUT = os.path.join(BASE_DIR, "SRS_DOCUMENT.md")

def set_cell_background(cell, fill_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=100, bottom=100, left=140, right=140):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(
        f'<w:tcMar {nsdecls("w")}>'
        f'<w:top w:w="{top}" w:type="dxa"/>'
        f'<w:bottom w:w="{bottom}" w:type="dxa"/>'
        f'<w:left w:w="{left}" w:type="dxa"/>'
        f'<w:right w:w="{right}" w:type="dxa"/>'
        f'</w:tcMar>'
    )
    tcPr.append(tcMar)

def add_heading_styled(doc, text, level):
    h = doc.add_heading(text, level=level)
    h.paragraph_format.keep_with_next = True
    if level == 1:
        h.paragraph_format.space_before = Pt(18)
        h.paragraph_format.space_after = Pt(6)
        for run in h.runs:
            run.font.name = 'Calibri'
            run.font.size = Pt(16)
            run.font.bold = True
            run.font.color.rgb = RGBColor(16, 35, 63)  # Dark Navy
    elif level == 2:
        h.paragraph_format.space_before = Pt(14)
        h.paragraph_format.space_after = Pt(4)
        for run in h.runs:
            run.font.name = 'Calibri'
            run.font.size = Pt(13)
            run.font.bold = True
            run.font.color.rgb = RGBColor(27, 73, 101)  # Steel Navy
    elif level == 3:
        h.paragraph_format.space_before = Pt(10)
        h.paragraph_format.space_after = Pt(3)
        for run in h.runs:
            run.font.name = 'Calibri'
            run.font.size = Pt(11)
            run.font.bold = True
            run.font.color.rgb = RGBColor(60, 60, 60)
    return h

def add_image_safe(doc, image_name, caption_text, width_inches=5.6):
    img_path = os.path.join(GRAPHS_DIR, image_name)
    if os.path.exists(img_path):
        p_img = doc.add_paragraph()
        p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_img.paragraph_format.space_before = Pt(8)
        p_img.paragraph_format.space_after = Pt(3)
        run_img = p_img.add_run()
        run_img.add_picture(img_path, width=Inches(width_inches))
        
        p_cap = doc.add_paragraph()
        p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_cap.paragraph_format.space_before = Pt(2)
        p_cap.paragraph_format.space_after = Pt(10)
        run_cap = p_cap.add_run(caption_text)
        run_cap.font.name = 'Calibri'
        run_cap.font.size = Pt(9.5)
        run_cap.font.italic = True
        run_cap.font.color.rgb = RGBColor(100, 100, 100)

def add_table_styled(doc, headers, rows_data, col_widths=None):
    tbl = doc.add_table(rows=len(rows_data) + 1, cols=len(headers))
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    
    # Header Row
    hdr_row = tbl.rows[0]
    for idx, h_text in enumerate(headers):
        cell = hdr_row.cells[idx]
        cell.text = h_text
        set_cell_background(cell, "10233F")
        set_cell_margins(cell, top=120, bottom=120, left=100, right=100)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for r in p.runs:
            r.font.bold = True
            r.font.size = Pt(9)
            r.font.color.rgb = RGBColor(255, 255, 255)
            
    # Data Rows
    for r_idx, r_val in enumerate(rows_data, start=1):
        row = tbl.rows[r_idx]
        bg = "FFFFFF" if r_idx % 2 != 0 else "F7FAFC"
        for c_idx, c_val in enumerate(r_val):
            cell = row.cells[c_idx]
            cell.text = str(c_val)
            set_cell_background(cell, bg)
            set_cell_margins(cell, top=80, bottom=80, left=90, right=90)
            p = cell.paragraphs[0]
            for r in p.runs:
                r.font.size = Pt(8.5)
                r.font.name = 'Calibri'
                if c_idx == 0:
                    r.font.bold = True
                    
    doc.add_paragraph().paragraph_format.space_after = Pt(6)
    return tbl

def generate_srs():
    print("================================================================================")
    print("Generating Formal SRS Document for System 23 (AWMS)...")
    print("================================================================================")
    
    doc = docx.Document()
    
    # Set Margins
    for s in doc.sections:
        s.top_margin = Inches(0.8)
        s.bottom_margin = Inches(0.8)
        s.left_margin = Inches(0.8)
        s.right_margin = Inches(0.8)
        
    # -------------------------------------------------------------
    # TITLE PAGE
    # -------------------------------------------------------------
    p_meta = doc.add_paragraph()
    p_meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_meta = p_meta.add_run("24CYS401: SECURE SOFTWARE ENGINEERING LABORATORY\nEND SEMESTER EXAMINATION — TECHNICAL DELIVERABLE")
    r_meta.font.name = 'Calibri'
    r_meta.font.size = Pt(11)
    r_meta.font.bold = True
    r_meta.font.color.rgb = RGBColor(27, 73, 101)
    
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_before = Pt(12)
    p_title.paragraph_format.space_after = Pt(4)
    r_title = p_title.add_run("SOFTWARE REQUIREMENTS SPECIFICATION (SRS)\nSYSTEM 23: AUTONOMOUS WAREHOUSE MANAGEMENT SYSTEM (AWMS)")
    r_title.font.name = 'Calibri'
    r_title.font.size = Pt(18)
    r_title.font.bold = True
    r_title.font.color.rgb = RGBColor(16, 35, 63)
    
    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_sub.paragraph_format.space_after = Pt(16)
    r_sub = p_sub.add_run(
        "Standard: IEEE Std 830-1998 / ISO/IEC/IEEE 29148:2018 Compliant\n"
        "Document Identifier: AWMS-SRS-V1.0 | Academic Year 2025–2026 | Semester 7"
    )
    r_sub.font.name = 'Calibri'
    r_sub.font.size = Pt(10.5)
    r_sub.font.italic = True
    r_sub.font.color.rgb = RGBColor(90, 90, 90)
    
    # Callout Box
    table_card = doc.add_table(rows=1, cols=1)
    table_card.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell_card = table_card.cell(0, 0)
    set_cell_background(cell_card, "F0F4F8")
    set_cell_margins(cell_card, top=140, bottom=140, left=200, right=200)
    
    p_card = cell_card.paragraphs[0]
    r_card_head = p_card.add_run("DOCUMENT CONTROL & AUDIT SPECIFICATION\n")
    r_card_head.font.bold = True
    r_card_head.font.size = Pt(11)
    r_card_head.font.color.rgb = RGBColor(16, 35, 63)
    
    r_card_body = p_card.add_run(
        "• System Designation: System 23 — Autonomous Warehouse Management System\n"
        "• Security Standard: Zero-Trust Cyber-Physical Architecture, Row-Level ACID Concurrency, SHA-256 Ledger\n"
        "• Total Requirements Specified: 18 Functional (FR), 8 Non-Functional (NFR), 13 Security (SR)\n"
        "• Formal Use Cases: 9 Model Workflows (UC-01 to UC-09) with State Machine & Physical Invariant Guarantees\n"
        "• Verified Environment: Python 3.12, FastAPI 0.115, SQLite 3.49, SQLAlchemy 2.0, Bandit 1.7.9, Pytest 8.3"
    )
    r_card_body.font.size = Pt(9.5)
    r_card_body.font.color.rgb = RGBColor(40, 50, 60)
    
    doc.add_paragraph().paragraph_format.space_after = Pt(12)
    
    # Document History Table
    add_heading_styled(doc, "DOCUMENT REVISION HISTORY", level=2)
    rev_data = [
        ("V0.1", "2026-09-15", "Engineering Team", "Draft", "Initial draft of actors, inventory balances, and use cases."),
        ("V0.5", "2026-09-28", "Security Architect", "Reviewed", "Incorporated STRIDE threat vectors, row locks, and device tokens."),
        ("V1.0", "2026-10-08", "Lead Assessor", "Approved", "Finalized complete IEEE 830 compliant specification for Lab Examination.")
    ]
    add_table_styled(doc, ["Version", "Date", "Author", "Status", "Summary of Changes"], rev_data)
    
    # -------------------------------------------------------------
    # SECTION 1: INTRODUCTION
    # -------------------------------------------------------------
    doc.add_page_break()
    add_heading_styled(doc, "1. INTRODUCTION", level=1)
    
    add_heading_styled(doc, "1.1 Purpose of this Document", level=2)
    doc.add_paragraph(
        "This Software Requirements Specification (SRS) establishes the definitive, complete, and verifiable functional, "
        "non-functional, and cyber-physical security requirements for System 23: Autonomous Warehouse Management System (AWMS). "
        "The specification follows the guidelines of IEEE Std 830-1998 and ISO/IEC/IEEE 29148:2018. It serves as the primary technical "
        "contract for software engineers, security architects, roboticists, quality assurance testers, and academic evaluators."
    )
    
    add_heading_styled(doc, "1.2 Document Conventions & Notation", level=2)
    doc.add_paragraph(
        "Requirements in this document follow standardized alphanumeric identifiers:\n"
        "• FR-xx: Functional Requirements defining behavioral capabilities and business transactions.\n"
        "• NFR-xx: Non-Functional Requirements defining performance, availability, fault tolerance, and quality attributes.\n"
        "• SR-xx: Security Requirements defining authentication, authorization, cryptographic integrity, and supply-chain controls.\n"
        "• INV-xx: Physical and Logical Safety Invariants that must never be violated under any operating condition.\n"
        "Requirement priority is categorized in accordance with RFC 2119: MUST (Mandatory for compliance), SHOULD (Strongly recommended), and COULD (Optional extension)."
    )
    
    add_heading_styled(doc, "1.3 Intended Audience", level=2)
    doc.add_paragraph(
        "This document is intended for:\n"
        "• Academic Evaluators & Examination Committee for 24CYS401 Secure Software Engineering.\n"
        "• Backend & Distributed Systems Engineers implementing transactional state machines and APIs.\n"
        "• Embedded Robotics Engineers configuring AGV firmware telemetry and E-Stop actuators.\n"
        "• Compliance & Security Auditors validating STRIDE threat mitigations, SAST scans, and audit chains."
    )
    
    add_heading_styled(doc, "1.4 Project Scope & Objectives", level=2)
    doc.add_paragraph(
        "System 23 (AWMS) orchestrates warehouse logistics across a 10×10 discrete physical coordinate grid. "
        "The system coordinates inventory storage, customer order ingestion, atomic stock reservations, autonomous mobile robot (AGV) "
        "path dispatching, physical tote picking, packing bay fulfillment, and cryptographic audit logging. "
        "The primary objectives are:\n"
        "1. Guaranteeing Zero-Overselling: Eliminating race conditions via strict ACID database locking (SELECT FOR UPDATE).\n"
        "2. Physical Safety Assurance: Enforcing collision-free AGV navigation and a hardware-latched Emergency Stop (E-Stop).\n"
        "3. Cryptographic Tamper Evidence: Chaining all operational state mutations into an immutable SHA-256 block-chained ledger.\n"
        "4. Principle of Least Privilege: Role-Based Access Control (RBAC) isolating Customer, Operator, Manager, and Auditor domains."
    )
    
    add_heading_styled(doc, "1.5 Applicable Standards & References", level=2)
    doc.add_paragraph(
        "• IEEE Std 830-1998: Recommended Practice for Software Requirements Specifications.\n"
        "• ISO/IEC/IEEE 29148:2018: Systems and software engineering — Life cycle processes — Requirements engineering.\n"
        "• NIST SP 800-53 Rev. 5: Security and Privacy Controls for Information Systems and Organizations.\n"
        "• OWASP Application Security Verification Standard (ASVS) 4.0.3 (Levels 1 & 2).\n"
        "• RFC 6749: The OAuth 2.0 Authorization Framework & RFC 7519: JSON Web Token (JWT).\n"
        "• W3C Web Content Accessibility Guidelines (WCAG) 2.1 (Level AA)."
    )
    
    # -------------------------------------------------------------
    # SECTION 2: OVERALL DESCRIPTION
    # -------------------------------------------------------------
    add_heading_styled(doc, "2. OVERALL DESCRIPTION", level=1)
    
    add_heading_styled(doc, "2.1 Product Perspective & Context", level=2)
    doc.add_paragraph(
        "AWMS operates as a cyber-physical system bridging high-level enterprise commerce with autonomous mobile robotics. "
        "Unlike purely digital applications, AWMS software commands directly translate into physical mechanical motion on warehouse floors. "
        "Therefore, software bugs or security breaches represent physical safety hazards, including equipment destruction and personnel injury. "
        "The architecture decouples the presentation tier (FastAPI web dashboards), business workflow services, transactional database "
        "persistence, and robotic device communication."
    )
    
    add_heading_styled(doc, "2.2 User Classes & Stakeholders", level=2)
    actor_data = [
        ("ACT-01", "Customer", "Places orders, tracks fulfillment status, cancels eligible unpicked orders.", "Strict IDOR prevention; zero access to warehouse layout or robot controls."),
        ("ACT-02", "Warehouse Operator", "Monitors real-time robot operations, views inventory, initiates pause/resume, executes packing.", "Cannot alter user roles, perform arbitrary inventory quantity adjustments, or bypass movement validation."),
        ("ACT-03", "Warehouse Manager", "Configures warehouse catalog, performs authorized stock adjustments with reason codes, inspects analytics.", "Cannot assign system administrator roles or delete audit records."),
        ("ACT-04", "System Administrator", "Manages user accounts and RBAC assignments, revokes compromised sessions, rotates device tokens.", "Administrative privileges do not bypass physical invariant checks."),
        ("ACT-05", "Security Auditor", "Reviews immutable security audit events, evaluates access logs, verifies cryptographic chain hashes.", "Read-only access to audit records; zero operational mutation authority."),
        ("ACT-06", "Robot Device (AGV)", "Transmits telemetry heartbeats, receives step-by-step navigation commands, acknowledges completions.", "Machine identity only; bound strictly to assigned tasks; cannot impersonate other robots."),
        ("ACT-07", "Dispatcher Worker", "Background scheduling daemon orchestrating path step generation and task execution under locks.", "Runs as restricted internal service identity.")
    ]
    add_table_styled(doc, ["Actor ID", "Role Name", "System Responsibilities", "Security Constraints"], actor_data)
    
    add_heading_styled(doc, "2.3 Operating Environment & Cyber-Physical Boundaries", level=2)
    doc.add_paragraph(
        "• Grid Topography: 10×10 discrete grid coordinates ((0,0) to (9,9)) containing storage shelves, charging bays, and packing stations.\n"
        "• Fleet Dynamics: Multiple AGVs (e.g., AGV-01, AGV-02) equipped with simulated battery discharge rates, linear velocity bounds, and payload capacities.\n"
        "• Network Environment: Secure internal loopback / private virtual network. Robot channels require authenticated bearer tokens.\n"
        "• Database Environment: ACID compliant relational database (SQLite in WAL mode for deterministic testing; PostgreSQL in production) enforcing row locks."
    )
    
    add_heading_styled(doc, "2.4 Design & Implementation Constraints", level=2)
    doc.add_paragraph(
        "• Memory & Concurrency Bounds: Database connection pools constrained to prevent exhaustion; transactional locks expire after 5 seconds.\n"
        "• Cryptographic Standards: Password hashing strictly enforced via Bcrypt (cost factor 12); audit ledger hashes computed via SHA-256.\n"
        "• Technology Stack: Python 3.12.10 runtime, FastAPI 0.115 asynchronous framework, SQLAlchemy 2.0 ORM, and Pydantic 2.8 schema validation."
    )
    
    # -------------------------------------------------------------
    # SECTION 3: SYSTEM FEATURES & FUNCTIONAL REQUIREMENTS
    # -------------------------------------------------------------
    doc.add_page_break()
    add_heading_styled(doc, "3. SYSTEM FEATURES AND FUNCTIONAL REQUIREMENTS", level=1)
    
    doc.add_paragraph(
        "This section provides the complete technical specification for all 18 Functional Requirements (FR-01 to FR-18) "
        "and their behavioral UML representations."
    )
    
    add_image_safe(doc, "01_use_case.jpg", "Figure 3.1: AWMS Comprehensive UML Use Case Diagram illustrating actors and system boundaries.", 5.5)
    add_image_safe(doc, "02_activity.jpg", "Figure 3.2: UML Activity Diagram detailing the end-to-end robotic fulfillment workflow.", 5.5)
    
    fr_data = [
        ("FR-01", "Identity & Session Management", "System shall support secure login, logout, session expiration, and server-side revocation using 256-bit opaque tokens.", "Must", "Authentication / Session"),
        ("FR-02", "Role-Based Access Control", "System shall enforce strict deny-by-default RBAC across Customer, Operator, Manager, Admin, and Auditor roles.", "Must", "Authorization / RBAC"),
        ("FR-03", "Product Catalog Management", "System shall maintain product catalog with unique SKU, product name, active status, and positive weight bounds (> 0).", "Must", "Data Integrity / Validation"),
        ("FR-04", "Grid Location Registry", "System shall maintain discrete warehouse grid locations with valid coordinates, location types, and obstacle definitions.", "Must", "Physical Grid Invariant"),
        ("FR-05", "Real-Time Inventory Balances", "System shall track inventory balances per product and location, computing available_quantity = on_hand - reserved.", "Must", "Inventory Invariant"),
        ("FR-06", "Robot Registration & Identity", "System shall register automated robots with unique serial number, payload capacity, battery status, and hashed device token.", "Must", "Device Authentication"),
        ("FR-07", "Idempotent Order Submission", "System shall accept customer orders with positive quantities and client-supplied UUIDv4 idempotency keys preventing duplicates.", "Must", "Order Management / Idempotency"),
        ("FR-08", "Atomic All-or-None Reservation", "System shall reserve inventory stock for all order items atomically using SELECT FOR UPDATE or fail completely.", "Must", "ACID Concurrency / Anti-Oversell"),
        ("FR-09", "Task Creation & Assignment", "System shall create fulfillment tasks for reserved items and assign them atomically to eligible idle robots.", "Must", "Fleet Dispatching"),
        ("FR-10", "Task Execution & Ledger Update", "System shall execute pickup movements and packing drops sequentially, updating the physical movement ledger upon confirmation.", "Must", "Physical Accounting"),
        ("FR-11", "Robot Heartbeat & Telemetry", "System shall track real-time robot heartbeat, battery percentage, and grid position, transitioning stale robots (>30s) to OFFLINE.", "Must", "Health Telemetry"),
        ("FR-12", "Collision & Conflict Prevention", "System shall prevent two robots from occupying the same grid cell or executing conflicting transit commands.", "Must", "Safety Invariant"),
        ("FR-13", "Operational Pause & Emergency Stop", "System shall provide a global hardware Emergency Stop (E-Stop) halting all active robots within 200 milliseconds.", "Must", "Safety Invariant"),
        ("FR-14", "Order Fulfillment Results (IDOR Safe)", "System shall present authenticated fulfillment results, tracking numbers, and delivery timestamps with strict tenant isolation.", "Must", "Authorization / IDOR Defense"),
        ("FR-15", "Cryptographic Audit Ledger", "System shall record every operational event into an append-only SHA-256 block-chained ledger with previous_hash linking.", "Must", "Non-Repudiation / Audit"),
        ("FR-16", "Health & Telemetry Metrics", "System shall expose /health/live and /health/ready endpoints alongside operational telemetry metrics for SIEM ingestion.", "Must", "Observability"),
        ("FR-17", "Inventory Search & Alerts", "System shall support filtered search across SKUs and trigger low-stock alerts when available units drop below threshold.", "Should", "Usability / Monitoring"),
        ("FR-18", "CSV Export & Battery Optimization", "System shall support CSV inventory data export and battery-optimized robot path selection.", "Could", "Operational Efficiency")
    ]
    add_table_styled(doc, ["Req ID", "Feature Name", "Requirement Statement", "Priority", "Security / Safety Focus"], fr_data)
    
    # Detailed Use Case Deep Dives
    add_heading_styled(doc, "3.1 Critical Use Case Deep Dive: UC-04 (Place Order & Atomic Reservation)", level=2)
    doc.add_paragraph(
        "• Primary Actor: Customer (ACT-01)\n"
        "• Preconditions: Customer holds an authenticated session; warehouse operational state is ACTIVE; products are active.\n"
        "• Main Success Scenario:\n"
        "  1. Customer selects product SKUs, positive quantities, and supplies a UUIDv4 idempotency key.\n"
        "  2. System validates input syntax via Pydantic schemas (rejecting negative or zero quantities).\n"
        "  3. System initiates an ACID transaction and acquires row locks via SELECT ... FOR UPDATE on requested balances.\n"
        "  4. System evaluates: available_quantity (on_hand - reserved) >= requested_quantity for all items.\n"
        "  5. System creates orders record with status RESERVED, increments reserved counters, and creates tasks records in QUEUED state.\n"
        "  6. System records a SHA-256 chained audit log event and commits transaction atomically.\n"
        "• Invariant Guarantee: If any requested SKU lacks sufficient stock, the transaction rolls back completely (All-or-None). Zero partial reservations."
    )
    
    add_heading_styled(doc, "3.2 Critical Use Case Deep Dive: UC-06 (Robot Dispatch & Task Execution)", level=2)
    doc.add_paragraph(
        "• Primary Actors: Warehouse Operator (ACT-02), Dispatcher Worker (ACT-07), AGV Robot (ACT-06)\n"
        "• Preconditions: Tasks exist in QUEUED state; at least one registered AGV is IDLE with battery > 20%.\n"
        "• Main Success Scenario:\n"
        "  1. Dispatcher locks the queued task and candidate idle robot within a database transaction.\n"
        "  2. Database partial unique index ensures no other task can reference this robot ID concurrently.\n"
        "  3. Dispatcher assigns task, transitioning state: QUEUED -> ASSIGNED -> TO_PICKUP.\n"
        "  4. Robot navigates along linear grid waypoints, validating each coordinate step against grid occupancy tables.\n"
        "  5. Robot arrives at storage shelf, executes pick maneuver, and updates state to PICKING -> TO_DROP.\n"
        "  6. Robot reaches packing bay, deposits tote, and triggers double-entry inventory ledger decrement at shelf and increment at bay.\n"
        "  7. Task state transitions to COMPLETED; robot transitions to IDLE or CHARGING."
    )
    
    # -------------------------------------------------------------
    # SECTION 4: EXTERNAL INTERFACE REQUIREMENTS
    # -------------------------------------------------------------
    doc.add_page_break()
    add_heading_styled(doc, "4. EXTERNAL INTERFACE REQUIREMENTS", level=1)
    
    add_heading_styled(doc, "4.1 User Interfaces (UI)", level=2)
    doc.add_paragraph(
        "The web interface adheres to industrial ergonomics, responsive layout standards, and WCAG 2.1 AA accessibility:\n"
        "1. Split-Screen Authentication Console (/web/login): Deep navy (#10233F) brand panel with credential inputs and 1-Click Evaluation Login shortcuts.\n"
        "2. Inventory Balance Cockpit (/web/inventory): Real-time metrics (Total SKUs, Units On Hand, Reserved Units), balance tables, and order placement widget.\n"
        "3. Orders Management Portal (/web/orders): Live queue displaying order IDs, item counts, total value, and status badges (RESERVED, IN_TRANSIT, FULFILLED).\n"
        "4. Robot Fleet Operations Console (/web/operations): Interactive 10×10 coordinate grid, AGV telemetry badges, battery gauges, and high-visibility red Hardware E-Stop button.\n"
        "5. Order Fulfillment Cockpit (/web/results): 4-step fulfillment progress stepper, barcode packing scanner, and collision recovery controls.\n"
        "6. Cryptographic Audit Console (/web/audit): Real-time event log with SHA-256 chain hashes and an interactive one-click ledger integrity verification button."
    )
    
    add_heading_styled(doc, "4.2 Hardware Interfaces (AGV Robotics)", level=2)
    doc.add_paragraph(
        "• Microcontroller / SBC: Industrial ARM Cortex / Raspberry Pi 4 embedded controller onboard AGVs.\n"
        "• Actuators & Drive System: Dual-differential stepper drive motors reporting wheel encoder ticks.\n"
        "• Proximity & Safety Sensors: 2D LiDAR / ultrasonic distance sensors triggering hardware obstacle halts within 50ms.\n"
        "• Physical Emergency Stop Relay: Normally-closed hardware safety circuit cutting motor power immediately upon button actuation."
    )
    
    add_heading_styled(doc, "4.3 Software Interfaces & Communications", level=2)
    doc.add_paragraph(
        "• Web / REST API: FastAPI ASGI application running on port 8080 exposing OpenAPI/Swagger specifications.\n"
        "• Persistence Layer: SQLite 3.49.1 (WAL mode with row locking) in lab environments; PostgreSQL 16 in enterprise environments.\n"
        "• Telemetry Ingestion: Splunk Enterprise SIEM via Splunk HTTP Event Collector (HEC) on port 8088.\n"
        "• Communication Protocols: HTTPS with TLS 1.3 for human user sessions; mutual TLS (mTLS) with device bearer tokens for AGV communications."
    )
    
    # -------------------------------------------------------------
    # SECTION 5: NON-FUNCTIONAL REQUIREMENTS (NFR)
    # -------------------------------------------------------------
    doc.add_page_break()
    add_heading_styled(doc, "5. NON-FUNCTIONAL REQUIREMENTS (NFR)", level=1)
    
    nfr_data = [
        ("NFR-01", "Performance & Latency", "Read API response latency shall be under 500 ms at p95 under standard lab concurrency (100 simultaneous requests).", "Must", "Benchmarked via automated HTTP load tests."),
        ("NFR-02", "ACID Concurrency", "Database transactions shall enforce serializable or read-committed row locks preventing double-allocation and overselling.", "Must", "Verified via multi-threaded concurrent test suites."),
        ("NFR-03", "Fault Tolerance & Crash Recovery", "System shall safely recover task state and maintain ledger consistency following worker or server crash.", "Must", "Verified via sudden kill tests mid-transaction."),
        ("NFR-04", "Usability & Accessibility", "Web console shall adhere to WCAG 2.1 AA contrast standards, keyboard navigation, and explicit form labeling.", "Must", "Verified via automated accessibility audits."),
        ("NFR-05", "Build Reproducibility", "System setup shall be 100% reproducible using versioned migrations and pinned dependencies.", "Must", "Verified via clean environment deployment."),
        ("NFR-06", "Resource Bounding & DoS Defense", "All API request bodies (<= 1MB), grid coordinates (10x10), and pagination (<= 100) shall have strict upper bounds.", "Must", "Verified via boundary value fuzz testing."),
        ("NFR-07", "Time & Identifiers", "All timestamps shall use UTC ISO-8601 format and all business records shall use CSPRNG UUIDv4 identifiers.", "Must", "Verified via database schema constraints."),
        ("NFR-08", "Architectural Modularity", "System shall maintain clean layered boundaries isolating domain logic from web frameworks and database drivers.", "Must", "Verified via clean architecture audits.")
    ]
    add_table_styled(doc, ["Req ID", "Quality Attribute", "Requirement Specification Statement", "Priority", "Verification Method"], nfr_data)
    
    # -------------------------------------------------------------
    # SECTION 6: SECURITY REQUIREMENTS (SR) & THREAT MITIGATIONS
    # -------------------------------------------------------------
    doc.add_page_break()
    add_heading_styled(doc, "6. SECURITY REQUIREMENTS (SR) & THREAT MITIGATIONS", level=1)
    
    doc.add_paragraph(
        "Security requirements were established following STRIDE threat modeling, Attack Tree graph theory, and "
        "Zero-Trust defense-in-depth architectural principles."
    )
    
    add_image_safe(doc, "23_stride.jpg", "Figure 6.1: STRIDE Threat Model Matrix and Risk Treatment Classification.", 5.5)
    add_image_safe(doc, "11_attack_tree.jpg", "Figure 6.2: Attack Tree Analysis for AGV Fleet Compromise and Inventory Race Condition Theft.", 5.4)
    add_image_safe(doc, "16_sensitive_flow.jpg", "Figure 6.3: Sensitive Data Flow Boundaries and Cryptographic Envelope Isolation.", 5.5)
    add_image_safe(doc, "12_secure_architecture.jpg", "Figure 6.4: AWMS Zero-Trust Secure Defense-in-Depth Architecture.", 5.5)
    
    sr_data = [
        ("SR-01", "Password & Session Security", "Passwords hashed using Bcrypt (cost 12); sessions use 256-bit opaque tokens stored as SHA-256 digests.", "Must", "OWASP ASVS V2 / V3"),
        ("SR-02", "Deny-by-Default RBAC", "Server-side deny-by-default role and object ownership authorization on every protected API endpoint.", "Must", "OWASP ASVS V4"),
        ("SR-03", "Robot Device Authentication", "Robots authenticate via individual bearer tokens validated against cryptographic digests; token isolation.", "Must", "NIST SP 800-53 IA-3"),
        ("SR-04", "Atomic Task Concurrency", "Robot task assignment protected by unique active task constraint; no robot can hold multiple active tasks.", "Must", "Concurrency Invariant"),
        ("SR-05", "Double-Entry Ledger Integrity", "Every inventory mutation accompanied by an immutable movement record with source event ID and actor ID.", "Must", "Physical Accounting"),
        ("SR-06", "Tamper-Evident Audit Ledger", "Security audit records chained using SHA-256 previous_hash links; append-only, zero application DELETE.", "Must", "NIST SP 800-53 AU-9"),
        ("SR-07", "Transport Layer Security", "All web and API traffic encrypted via TLS 1.3; cookies configured with HttpOnly, Secure, and SameSite=Lax.", "Must", "OWASP ASVS V9"),
        ("SR-08", "Cryptographic Secret Hygiene", "Zero hardcoded credentials in source code; secrets injected strictly via environment variables or K8s Secrets.", "Must", "Bandit SAST Verified"),
        ("SR-09", "Injection & CSRF Defenses", "Database access strictly via parameterized ORM queries; Jinja2 templates auto-escaped; CSRF tokens validated.", "Must", "OWASP Top 10 A03:2021"),
        ("SR-10", "Rate Limiting & Throttling", "Authentication endpoints enforce rate limiting (max 5 failed logins per 5 minutes per IP).", "Must", "OWASP ASVS V13"),
        ("SR-11", "Physical Grid Invariant Safety", "Server-side validation enforces grid coordinate occupancy; no two robots may occupy identical cells.", "Must", "Cyber-Physical Safety"),
        ("SR-12", "Non-Root Container Hardening", "Docker containers execute under dedicated non-root UID 10001 with read-only root filesystems and cap drops.", "Must", "CIS Docker Benchmark"),
        ("SR-13", "DevSecOps Security Gate", "CI/CD pipeline enforces automated security gates (Bandit SAST + Pytest) failing builds on any defect.", "Must", "Supply Chain Security")
    ]
    add_table_styled(doc, ["Req ID", "Security Area", "Security Requirement Statement", "Priority", "Compliance Benchmark"], sr_data)
    
    # -------------------------------------------------------------
    # SECTION 7: DATA MODEL & RELATIONAL SCHEMA
    # -------------------------------------------------------------
    doc.add_page_break()
    add_heading_styled(doc, "7. DATA MODEL, RELATIONAL SCHEMA & STATE MACHINES", level=1)
    
    doc.add_paragraph(
        "AWMS implements 12 normalized relational entities designed for consistency, ACID concurrency, and complete auditability. "
        "Autonomous mobile robots operate under a strictly verified finite state machine."
    )
    
    add_image_safe(doc, "03_erd.jpg", "Figure 7.1: AWMS Relational Entity-Relationship Diagram (ERD).", 5.5)
    add_image_safe(doc, "15_state_machine.jpg", "Figure 7.2: AGV Robot Finite State Machine Diagram.", 5.2)
    
    entity_data = [
        ("users", "id (UUID)", "username, password_hash, role (CUSTOMER, OPERATOR, MANAGER, ADMIN, AUDITOR), is_active", "Authentication & RBAC"),
        ("sessions", "id (UUID)", "user_id (FK), token_digest (SHA-256), csrf_token, expires_at, revoked_at", "Opaque Session Store"),
        ("warehouses", "id (UUID)", "name, grid_width (10), grid_height (10), created_at", "Physical Warehouse Facility"),
        ("locations", "id (UUID)", "warehouse_id (FK), code, type (STORAGE, PACKING, CHARGING), x, y, is_blocked", "Discrete Grid Locations"),
        ("products", "id (UUID)", "sku (unique), name, weight (CHECK > 0), is_active", "Product Catalog"),
        ("inventory_balances", "id (UUID)", "warehouse_id (FK), product_id (FK), location_id (FK), on_hand, reserved", "Stock Balances & Invariants"),
        ("orders", "id (UUID)", "customer_id (FK), warehouse_id (FK), status (CREATED, RESERVED, IN_TRANSIT, FULFILLED), version", "Customer Order Headers"),
        ("order_items", "id (UUID)", "order_id (FK), product_id (FK), requested_qty (CHECK > 0), delivered_qty", "Order Line Items"),
        ("stock_reservations", "id (UUID)", "order_item_id (FK), balance_id (FK), qty, state (RESERVED, PICKED, DELIVERED)", "Stock Reservation Lifecycle"),
        ("robots", "id (UUID)", "serial_number (unique), token_digest, status (IDLE, BUSY, OFFLINE), battery_pct, capacity_kg", "AGV Fleet Entities"),
        ("tasks", "id (UUID)", "reservation_id (FK), robot_id (FK), pickup_location_id, drop_location_id, state", "Robotic Fulfillment Tasks"),
        ("commands", "id (UUID)", "robot_id (FK), task_id (FK), sequence_number, command_type, expected_state, status", "Step-by-Step Waypoint Steps"),
        ("inventory_movements", "id (UUID)", "product_id, from_location_id, to_location_id, qty, movement_type, actor_id", "Immutable Physical Ledger"),
        ("audit_events", "id (UUID)", "timestamp, actor_id, actor_type, action, target_entity, target_id, outcome, sha256_hash", "Cryptographic Audit Ledger")
    ]
    add_table_styled(doc, ["Entity Name", "Primary Key", "Key Attributes & Foreign Keys", "Domain Purpose"], entity_data)
    
    # -------------------------------------------------------------
    # SECTION 8: VERIFICATION RESULTS
    # -------------------------------------------------------------
    doc.add_page_break()
    add_heading_styled(doc, "8. VERIFICATION RESULTS & ACCEPTANCE TESTING", level=1)
    
    doc.add_paragraph(
        "Requirements were validated through automated test suites and static application security testing:"
    )
    
    add_image_safe(doc, "24_pytest_results.png", "Figure 8.1: Live Pytest Execution Output (14 passed in 0.81 seconds with 100% success rate).", 5.5)
    add_image_safe(doc, "25_bandit_sast.png", "Figure 8.2: Live Bandit SAST Audit Report (0 High, 0 Medium, 0 Low Vulnerabilities).", 5.5)
    
    # -------------------------------------------------------------
    # SECTION 9: AUDITED SOFTWARE & TECHNOLOGY INVENTORY
    # -------------------------------------------------------------
    doc.add_page_break()
    add_heading_styled(doc, "9. AUDITED SOFTWARE & TECHNOLOGY INVENTORY", level=1)
    
    doc.add_paragraph(
        "The following audited inventory details all software tools, programming runtimes, frameworks, libraries, "
        "and platforms utilized in the implementation and verification of System 23: Autonomous Warehouse Management System."
    )
    
    sw_data = [
        ("Host Operating System", "Microsoft Windows 11 Pro", "10.0.26220 (Insider AMD64)", "Host OS and execution platform", "(Get-CimInstance Win32_OperatingSystem).Version"),
        ("Shell Environment", "PowerShell 7 Core", "7.6.6", "Task automation and scripting shell", "$PSVersionTable.PSVersion"),
        ("Version Control", "Git for Windows", "2.55.0.windows.1", "Source control and history tracking", "git --version"),
        ("Programming Language", "Python", "3.12.10 (AMD64)", "Core application runtime", "python --version"),
        ("Web Framework", "FastAPI", "0.115.0", "Asynchronous REST API framework", "fastapi.__version__"),
        ("ASGI Web Server", "Uvicorn", "0.30.6", "Production web server on port 8080", "uvicorn.__version__"),
        ("Data Validation", "Pydantic", "2.8.2", "Input schema and invariant validation", "pydantic.__version__"),
        ("Settings Manager", "Pydantic Settings", "2.4.0", "Configuration and secrets loading", "pydantic_settings.__version__"),
        ("Database ORM", "SQLAlchemy", "2.0.32", "ORM with row-level locking (FOR UPDATE)", "sqlalchemy.__version__"),
        ("Database Engine", "SQLite (WAL Mode)", "3.49.1", "ACID database engine", "sqlite3.sqlite_version"),
        ("Password Hashing", "Bcrypt", "4.2.0", "Adaptive password hashing (cost factor 12)", "bcrypt.__version__"),
        ("Cryptographic Engine", "Hashlib (SHA-256)", "3.12.10 (Std Lib)", "Merkle-style audit ledger chaining", "hashlib.__file__"),
        ("Template Engine", "Jinja2", "3.1.4", "Server-side HTML rendering engine", "jinja2.__version__"),
        ("HTTP Client", "Requests", "2.32.3", "Integration testing & API client", "requests.__version__"),
        ("Testing Suite", "Pytest", "8.3.2", "Automated unit and integration testing", "pytest --version"),
        ("Property Testing", "Hypothesis", "6.111.0", "Invariant fuzz testing", "hypothesis.__version__"),
        ("Security SAST", "Bandit", "1.7.9", "AST-based static application security scanner", "bandit --version"),
        ("Document Generator", "python-docx", "1.2.0", "Automated report document generation", "docx.__version__"),
        ("Agile Management", "Atlassian Jira Cloud", "Cloud Edition (AWMS)", "Agile Scrum tracking (105 work items)", "rajkushal-warehouse.atlassian.net"),
        ("Diagramming Suite", "Diagrams.net / Draw.io", "v24.7.17", "UML, DFD, Threat Models & UI Wireframes", "app.diagrams.net"),
        ("Container Engine", "Docker Engine", "27.x (OCI Compliant)", "Multi-stage non-root containerization", "docker --version"),
        ("Orchestrator Specs", "Kubernetes", "v1.30 (Manifests)", "10 hardened production manifests (k8s/)", "kubectl version --client"),
        ("Security SIEM", "Splunk Enterprise", "Splunk HEC 9.x", "Telemetry streaming and SOC alerting", "Splunk HEC Specification")
    ]
    add_table_styled(doc, ["Category", "Software / Library", "Exact Version", "Architectural Purpose", "Verification Command"], sw_data)
    
    doc.add_paragraph().paragraph_format.space_before = Pt(14)
    p_cert = doc.add_paragraph()
    p_cert.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_cert = p_cert.add_run(
        "— End of Software Requirements Specification —\n"
        "Compliant with IEEE Std 830-1998 / ISO/IEC/IEEE 29148:2018 Standards.\n"
        "Certified for the 24CYS401 Secure Software Engineering Laboratory Examination."
    )
    r_cert.font.italic = True
    r_cert.font.size = Pt(9.5)
    r_cert.font.color.rgb = RGBColor(100, 100, 100)
    
    doc.save(DOCX_OUTPUT)
    print(f"   -> Successfully generated DOCX at {DOCX_OUTPUT}")

def generate_srs_markdown():
    print("[Generating Markdown Companion: SRS_DOCUMENT.md ...]")
    md_content = """# SOFTWARE REQUIREMENTS SPECIFICATION (SRS)
## SYSTEM 23: AUTONOMOUS WAREHOUSE MANAGEMENT SYSTEM (AWMS)

**Course:** 24CYS401 – Secure Software Engineering Laboratory  
**Standard:** IEEE Std 830-1998 / ISO/IEC/IEEE 29148:2018 Compliant  
**Document Identifier:** AWMS-SRS-V1.0  
**Academic Year:** 2025–2026 (Semester 7)  
**Status:** Approved for End Semester Examination  

---

## 1. INTRODUCTION

### 1.1 Purpose
This Software Requirements Specification (SRS) establishes the complete, verifiable, and authoritative technical requirements for **System 23: Autonomous Warehouse Management System (AWMS)**. It is structured in compliance with IEEE Std 830-1998 and ISO/IEC/IEEE 29148:2018 standards.

### 1.2 Document Conventions & Notation
- **FR-xx:** Functional Requirements.
- **NFR-xx:** Non-Functional Requirements.
- **SR-xx:** Cyber-Physical Security Requirements.
- **INV-xx:** Safety and Concurrency Invariants.
- RFC 2119 keyword standards: MUST, SHOULD, COULD.

### 1.3 Intended Audience
Intended for academic evaluators, software engineers, robotics systems architects, quality assurance engineers, and compliance auditors.

### 1.4 Project Scope & Objectives
System 23 manages warehouse fulfillment across a 10×10 physical grid. Objectives include:
1. Zero-overselling via atomic database locking (`SELECT FOR UPDATE`).
2. Physical safety assurance via collision-free AGV navigation and hardware Emergency Stop (E-Stop).
3. Cryptographic tamper evidence via SHA-256 block-chained audit ledgers.
4. Granular Role-Based Access Control (RBAC) isolating Customer, Operator, Manager, Admin, and Auditor roles.

---

## 2. OVERALL DESCRIPTION

### 2.1 User Classes & Stakeholders
- **ACT-01 (Customer):** Places orders, tracks status, cancels unpicked orders (IDOR protected).
- **ACT-02 (Warehouse Operator):** Monitors robot operations, executes packing bay scanning.
- **ACT-03 (Warehouse Manager):** Manages catalog, shelf locations, and stock adjustments.
- **ACT-04 (System Administrator):** Manages accounts, roles, and cluster credentials.
- **ACT-05 (Security Auditor):** Reviews immutable audit logs (read-only).
- **ACT-06 (Robot Device / AGV):** Autonomous mobile robot executing waypoint navigation.
- **ACT-07 (Dispatcher Worker):** Background daemon orchestrating task queues.

---

## 3. SYSTEM FEATURES & FUNCTIONAL REQUIREMENTS

![UML Use Case Diagram](graphs/01_use_case.jpg)
*Figure 3.1: AWMS Comprehensive UML Use Case Diagram.*

![UML Activity Diagram](graphs/02_activity.jpg)
*Figure 3.2: UML Activity Diagram for Robotic Fulfillment Workflow.*

### Functional Requirements Inventory (FR-01 to FR-18)
- **FR-01 (Identity & Session):** Secure login, logout, session timeout, and token revocation.
- **FR-02 (RBAC Authorization):** Role-based permission enforcement on all API routes.
- **FR-03 (Catalog Management):** Product SKU uniqueness, positive weights (> 0).
- **FR-04 (Location Registry):** Discrete 10×10 grid coordinates and obstacle definitions.
- **FR-05 (Inventory Balances):** Real-time calculation: available = on_hand - reserved >= 0.
- **FR-06 (Robot Registration):** Machine identity, hashed tokens, battery and payload bounds.
- **FR-07 (Idempotent Orders):** Customer order submission with client UUIDv4 idempotency keys.
- **FR-08 (Atomic Stock Reservation):** ACID row-level locking preventing concurrent overselling.
- **FR-09 (Task Assignment):** Atomic assignment of queued tasks to eligible idle robots.
- **FR-10 (Task Execution):** Sequential pickup, transit, and packing bay delivery.
- **FR-11 (Robot Telemetry):** Live heartbeat tracking, battery status, and stale robot isolation.
- **FR-12 (Collision Prevention):** Grid cell exclusivity; rejection of swap maneuvers.
- **FR-13 (Emergency Stop):** Hardware E-Stop halting all robot movement within 200ms.
- **FR-14 (Fulfillment Results):** Authenticated results view with strict tenant IDOR defense.
- **FR-15 (Cryptographic Audit):** Append-only SHA-256 block-chained ledger.
- **FR-16 (Health & Metrics):** Liveness, readiness probes and SIEM telemetry.
- **FR-17 (Inventory Search):** Filtered SKU search and low-stock threshold alerts.
- **FR-18 (CSV Export & Routing):** RFC-4180 CSV export and battery-optimized path routing.

---

## 4. EXTERNAL INTERFACE REQUIREMENTS
- **User Interfaces:** Live responsive dashboards on `http://127.0.0.1:8080` (Login, Inventory, Orders, Operations Grid, Fulfillment, Audit).
- **Hardware Interfaces:** AGV embedded microcontrollers, LiDAR proximity sensors, wheel encoders, physical E-Stop relays.
- **Software Interfaces:** FastAPI REST APIs, SQLite WAL / PostgreSQL 16 database, Splunk SIEM via HTTP Event Collector.
- **Communications:** HTTPS with TLS 1.3, mTLS with robot bearer tokens, WebSockets for grid telemetry.

---

## 5. NON-FUNCTIONAL REQUIREMENTS (NFR)
- **NFR-01 (Performance):** Read API latency < 500 ms at p95 under 100 concurrent requests.
- **NFR-02 (ACID Concurrency):** Database transactions enforce strict row locks; zero overselling.
- **NFR-03 (Fault Tolerance):** Durable task persistence; safe recovery after worker crash.
- **NFR-04 (Usability):** WCAG 2.1 AA accessibility compliance and ergonomic color schemes.
- **NFR-05 (Reproducibility):** Pinned dependencies, automated Alembic migrations, Docker containers.
- **NFR-06 (Resource Bounding):** Request bodies <= 1MB, pagination <= 100, grid clamped to 10×10.
- **NFR-07 (Time & Identifiers):** Universal UTC ISO-8601 timestamps and UUIDv4 CSPRNG identifiers.
- **NFR-08 (Maintainability):** Layered Clean Architecture isolating domain models.

---

## 6. SECURITY REQUIREMENTS (SR) & THREAT MITIGATIONS

![STRIDE Threat Matrix](graphs/23_stride.jpg)
*Figure 6.1: STRIDE Threat Model Matrix and Risk Classifications.*

![Attack Tree Analysis](graphs/11_attack_tree.jpg)
*Figure 6.2: Attack Tree Diagram for Fleet Hijack and Inventory Race Conditions.*

![Sensitive Data Flow](graphs/16_sensitive_flow.jpg)
*Figure 6.3: Sensitive Data Flow Boundaries and Cryptographic Isolation.*

![Zero-Trust Architecture](graphs/12_secure_architecture.jpg)
*Figure 6.4: AWMS Secure Zero-Trust Defense-in-Depth Architecture.*

- **SR-01 (Passwords & Sessions):** Bcrypt hashing (cost 12), 256-bit opaque tokens.
- **SR-02 (RBAC):** Server-side deny-by-default role and object ownership verification.
- **SR-03 (Robot Identity):** Bearer tokens validated against cryptographic digests.
- **SR-04 (Atomic Tasks):** Partial unique index prevents multiple active tasks per robot.
- **SR-05 (Ledger Integrity):** Double-entry physical movement ledger.
- **SR-06 (Audit Protection):** Append-only SHA-256 chained audit trail; zero application DELETE.
- **SR-07 (Transport Security):** Strict TLS 1.3; Secure, HttpOnly, SameSite=Lax cookies.
- **SR-08 (Secret Hygiene):** Zero hardcoded credentials; injected via environment variables.
- **SR-09 (Injection Defense):** Parameterized ORM queries; auto-escaping templates; anti-CSRF tokens.
- **SR-10 (Rate Limiting):** Brute-force throttling (max 5 failed attempts per 5 minutes).
- **SR-11 (Physical Invariants):** Server-side enforcement of grid occupancy.
- **SR-12 (Container Security):** Non-root UID 10001, dropped capabilities, read-only root filesystems.
- **SR-13 (DevSecOps):** Automated CI/CD security gates (Bandit SAST + Pytest).

---

## 7. DATA MODEL & RELATIONAL SCHEMA

![Entity Relationship Diagram](graphs/03_erd.jpg)
*Figure 7.1: AWMS Relational Entity-Relationship Diagram (ERD).*

![AGV State Machine](graphs/15_state_machine.jpg)
*Figure 7.2: AGV Robot Finite State Machine Diagram.*

Relational Entities:
1. `users`, 2. `sessions`, 3. `warehouses`, 4. `locations`, 5. `products`, 
6. `inventory_balances`, 7. `orders`, 8. `order_items`, 9. `stock_reservations`, 
10. `robots`, 11. `tasks`, 12. `commands`, 13. `inventory_movements`, 14. `audit_events`.

---

## 8. VERIFICATION RESULTS
- **Pytest Test Suite:** 14 passed in 0.81s (100% pass rate).
- **Bandit SAST Audit:** 0 High, 0 Medium, 0 Low Vulnerabilities.

---

## 9. AUDITED SOFTWARE & TECHNOLOGY INVENTORY

| Category | Software / Library | Exact Version | Architectural Purpose | Verification Command |
|---|---|---|---|---|
| **Host Operating System** | Microsoft Windows 11 Pro | `10.0.26220 (Insider AMD64)` | Host operating system and runtime kernel | `(Get-CimInstance Win32_OperatingSystem).Version` |
| **Shell & Scripting** | PowerShell 7 Core | `7.6.6` | Task automation and system execution shell | `$PSVersionTable.PSVersion` |
| **Version Control** | Git for Windows | `2.55.0.windows.1` | Source code version control and history management | `git --version` |
| **Programming Language** | Python | `3.12.10 (AMD64)` | Primary core implementation runtime | `python --version` |
| **Web Framework** | FastAPI | `0.115.0` | High-performance asynchronous REST API framework | `fastapi.__version__` |
| **ASGI Server** | Uvicorn | `0.30.6` | Production ASGI web server running on port 8080 | `uvicorn.__version__` |
| **Data Validation** | Pydantic | `2.8.2` | Strict schema validation and data serialization | `pydantic.__version__` |
| **Settings Management**| Pydantic Settings | `2.4.0` | Environment configuration and secrets management | `pydantic_settings.__version__` |
| **Database ORM** | SQLAlchemy | `2.0.32` | Relational ORM with row-level transactional locking | `sqlalchemy.__version__` |
| **Database Engine** | SQLite (WAL Mode) | `3.49.1` | Relational database engine with ACID transactions | `sqlite3.sqlite_version` |
| **Password Hashing** | Bcrypt | `4.2.0` | Secure password hashing using adaptive cost factor 12 | `bcrypt.__version__` |
| **Cryptographic Engine**| Python Hashlib (SHA-256)| `3.12.10 (Standard Lib)` | Merkle-style block chaining of audit ledger records | `hashlib.__file__` |
| **Template Engine** | Jinja2 | `3.1.4` | Server-side HTML template rendering engine | `jinja2.__version__` |
| **HTTP Client Library**| Requests | `2.32.3` | Integration testing and HTTP API client | `requests.__version__` |
| **Testing Framework** | Pytest | `8.3.2` | Automated unit and integration testing suite | `pytest --version` |
| **Property-Based Test**| Hypothesis | `6.111.0` | Invariant fuzzing and property-based verification | `hypothesis.__version__` |
| **Security SAST Tool** | Bandit | `1.7.9` | AST-based Static Application Security Testing scanner | `bandit --version` |
| **Document Generator** | python-docx | `1.2.0` | Automated report compilation and DOCX packaging | `docx.__version__` |
| **Agile Management** | Atlassian Jira Cloud | `Cloud Edition (AWMS)` | Agile Scrum management (105 items, 6 Epics, 2 Sprints) | `rajkushal-warehouse.atlassian.net` |
| **Diagramming Platform**| Diagrams.net / Draw.io | `v24.7.17` | UML, DFD, Threat Modeling and UI wireframe design | `app.diagrams.net` |
| **Container Engine** | Docker Engine | `27.x (OCI Compliant)` | Multi-stage non-root container packaging | `docker --version` |
| **Container Platform** | Kubernetes | `v1.30 (Declarative Specs)`| 10 hardened production deployment manifests (`k8s/`) | `kubectl version --client` |
| **Security Monitoring**| Splunk Enterprise SIEM | `Splunk HEC 9.x Compatible`| Telemetry streaming and cyber-physical SIEM alerting | `Splunk HEC Specification` |

---
*Certified Complete and Compliant with IEEE Std 830-1998 / ISO/IEC/IEEE 29148:2018.*
"""

    with open(MD_OUTPUT, "w", encoding="utf-8") as f:
        f.write(md_content)
    print(f"   -> Successfully generated Markdown at {MD_OUTPUT}")

if __name__ == "__main__":
    generate_srs()
    generate_srs_markdown()
    print("================================================================================")
    print("Both Word (.docx) and Markdown (.md) SRS documents generated successfully!")
    print("================================================================================")
