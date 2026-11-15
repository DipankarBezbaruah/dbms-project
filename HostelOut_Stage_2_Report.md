# TEZPUR UNIVERSITY
### Department of Computer Science & Engineering
***
## DATABASE APPLICATION DEVELOPMENT LABORATORY
### Stage II: Working Prototype & Progress Review Report

# HostelOut: Digital Outpass System

**Submitted by:**  
**GROUP-3**  
1. **Dipankar Bezbaruah** (CSB24083)  
2. **Arnam Arni Gogoi** (CSB24084)  
3. **Partha Sarathi Borgohain** (CSB24004)  

**Under the supervision of:**  
**Instructor: Prof. Dr. Swarup Roy**  
***

---

## Table of Contents
1. [Executive Summary & Stage II Milestones Review](#1-executive-summary--stage-ii-milestones-review)
2. [Database Architecture & Physical Implementation](#2-database-architecture--physical-implementation)
   - 2.1 Relational Schema & Entity Specifications
   - 2.2 Entity-Relationship (ER) Diagram & Structural Mapping
   - 2.3 Integrity Constraints, Keys & Relational Cascades
3. [Key Relational Queries & Database Operations (Stage II Focus)](#3-key-relational-queries--database-operations-stage-ii-focus)
   - 3.1 Query 1: Hierarchical Multi-Level Outpass Routing & Status Pipeline
   - 3.2 Query 2: Real-Time Gate Overdue Detection & Discrepancy Monitoring
   - 3.3 Query 3: Multi-Authority Sequential Audit Trail Reconstruction
   - 3.4 Query 4: Security Gate Anti-Tamper State Validation & Cooldown Query
   - 3.5 Query 5: Hostel Occupancy & Cross-Departmental Outpass Analytics
4. [Core CRUD Operations & RESTful API Specifications](#4-core-crud-operations--restful-api-specifications)
   - 4.1 Transaction Lifecycle: Create, Read, Update, Delete/Archive
   - 4.2 API Endpoint Registry & Payload Contracts
5. [Data Integrity, Business Logic & Validation Implementation](#5-data-integrity-business-logic--validation-implementation)
   - 5.1 Date Consistency & Overlapping Request Prevention
   - 5.2 Strict Sequential State Transitions & Hierarchical Escalation
   - 5.3 Physical Gate Anti-Cheat Cooldown Enforcements
   - 5.4 Cryptographic Password Hashing & Role-Based Access Control (RBAC)
6. [Preliminary UI / API Demonstration & Workflow Walkthrough](#6-preliminary-ui--api-demonstration--workflow-walkthrough)
   - 6.1 Role-Specific Interface Modules (Student, Mentor, Warden, HOD, Security)
   - 6.2 Step-by-Step Prototype Workflow Walkthrough
7. [Critical Design Decisions & Justifications](#7-critical-design-decisions--justifications)
   - 7.1 Selection of MySQL 8.0 & SQLAlchemy ORM
   - 7.2 Unified Users Entity vs. Polymorphic Sub-Entities
   - 7.3 Dedicated Immutable Approvals Audit Ledger
   - 7.4 Dynamic Temporal Evaluation for Overdue Outpasses
8. [Verification, Testing & Test Suite Demonstration](#8-verification-testing--test-suite-demonstration)
   - 8.1 Automated API Test Suite Execution (`test_api.py`)
   - 8.2 Test Execution Matrix & Results (12/12 Endpoints Validated)
9. [Stage II Assessment Rubric Alignment](#9-stage-ii-assessment-rubric-alignment)
10. [Team Contribution Summary & Stage III Roadmap](#10-team-contribution-summary--stage-iii-roadmap)

---

## 1. Executive Summary & Stage II Milestones Review

### Project Recap & Problem Motivation
HostelOut is a centralized, stakeholder-sensitive, and development-oriented digital outpass and leave register system tailored for the residential campus of Tezpur University. In Stage I (Idea & Design Approval), our team conceptualized the core challenge: the traditional paper-based outpass issuance process suffers from profound operational friction, lack of real-time auditability, forgeable signatures, absence of parental and administrative tracking, and cumbersome manual escalation for extended leaves.

### Stage II Objectives & Scope
The objective of **Stage II: Working Prototype / Progress Review** is to substantiate the theoretical database design approved in Stage I by demonstrating a live, functioning prototype. In accordance with the course assignment guidelines (CBDE Evaluation Framework), Stage II evaluates:
1. **Database Creation**: Physical relational schema instantiation with constraints and normalized tables.
2. **Core DB Operations**: Full CRUD lifecycle across users, outpasses, approvals, and gate entries.
3. **Key Queries**: Implementation of at least 3 meaningful and complex relational operations demonstrating real-world business logic.
4. **Validation & Constraints**: Robust error handling, date overlap prevention, and anti-tamper mechanisms.
5. **Preliminary UI & API**: Functional interactive client and RESTful API demonstrating end-to-end integration.

| Syllabus Requirement | Expected Evidence | Implementation Status in HostelOut | Evaluation Focus |
| :--- | :--- | :--- | :--- |
| **Database Creation** | Relational tables created, physical data types, foreign keys, constraints. | **Fully Completed**: 11 MySQL tables implemented via SQLAlchemy ORM with foreign keys, enums, cascades. | Data model correctness, normalized design. |
| **Core DB Operations (CRUD)** | Create, Read, Update, Delete queries and operations across all core entities. | **Fully Completed**: Submitting outpasses, user registration, multi-level approvals, gate logging, audit recording. | Integrity, correctness, data isolation. |
| **Key Queries / Operations** | At least 3 meaningful and complex queries demonstrating business logic. | **Exceeded (5 Implemented)**: Multi-level pending aggregation, real-time overdue detection, full audit trail JOIN, gate state check, occupancy analytics. | Complexity (8 marks), query optimization, real-world usefulness. |
| **Validation & Constraints** | Rejection of invalid dates, state enforcement, credential security, role guards. | **Fully Completed**: Chronological date checks, strict approval state machine, 30-min gate anti-cheat gap, PBKDF2 hashing. | Design implementation (2 marks), robust error handling. |
| **Preliminary UI & API** | Functional interactive client and API for user/role interactions. | **Fully Completed**: React 18 SPA (5 distinct role dashboards) connected to Flask 3.1 REST API. | End-to-end usability, responsive layout, live demo readiness. |

---

## 2. Database Architecture & Physical Implementation

### 2.1 Relational Schema & Entity Specifications
The database is hosted on **MySQL 8.0** and managed using **SQLAlchemy ORM** in Flask. The schema has been systematically normalized to **Third Normal Form (3NF)** to eliminate redundancy and maintain referential integrity.

```
+---------------------------------------------------------------------------------+
|                                 DATABASE SCHEMA                                 |
+---------------------------------------------------------------------------------+
| users (user_id [PK], email [UQ], password_hash, role [ENUM], name)              |
|                                                                                 |
| ├── mentors (mentor_id [PK], user_id [FK 1:1], department)                      |
| ├── hods (hod_id [PK], user_id [FK 1:1], department)                            |
| ├── wardens (warden_id [PK], user_id [FK 1:1], name, contact_no)                |
| └── security_staff (staff_id [PK], user_id [FK 1:1], name, shift)               |
|                                                                                 |
| hostels (hostel_id [PK], hostel_name, warden_id [FK])                           |
| rooms (room_id [PK], hostel_id [FK], room_no)                                   |
| students (student_id [PK], user_id [FK 1:1], roll_no [UQ], room_id, hostel_id,  |
|           mentor_id, department, contact_no)                                    |
|                                                                                 |
| outpasses (outpass_id [PK], student_id [FK], reason, destination,               |
|            requested_departure, requested_return, status [ENUM], remark,        |
|            mentor_approved [BOOL], warden_approved [BOOL], hod_approved [BOOL]) |
| approvals (approval_id [PK], outpass_id [FK], approved_by [FK],                 |
|            approver_role, decision [ENUM], remark, decided_at)                  |
| gate_log (gatelog_id [PK], outpass_id [FK 1:1 UQ], staff_id [FK],               |
|           actual_exit_time, actual_return_time)                                 |
+---------------------------------------------------------------------------------+
```

### 2.2 Table Definitions & Attributes Summary
1. **`users`**: Unified authentication table storing credentials, password hashes, full names, and role ENUMs (`Student`, `Mentor`, `Warden`, `HOD`, `Security`).
2. **`mentors`**: Faculty mentor profiles mapped 1:1 with `users`, tracking academic department oversight.
3. **`hods`**: Head of Department profiles mapped 1:1 with `users`, managing department-level approvals for leaves exceeding 7 days.
4. **`wardens`**: Hostel warden profiles mapped 1:1 with `users`, linking to hostel jurisdiction.
5. **`security_staff`**: Gate checkpoint personnel mapped 1:1 with `users`, tracking operational shifts (`Day`, `Night`).
6. **`hostels` & `rooms`**: Campus accommodation hierarchy. Each hostel has a dedicated warden; each room belongs to a hostel.
7. **`students`**: Comprehensive profile tracking institutional roll number (Unique), room, hostel, department, and assigned mentor.
8. **`outpasses`**: Core transaction record storing travel motivation, destination, scheduled window, approval flags, and status ENUM (`Pending`, `PartiallyApproved`, `Approved`, `Rejected`).
9. **`approvals`**: Append-only sequential audit table tracking every authority decision, timestamp, and remark.
10. **`gate_log`**: Physical security checkpoint log capturing `actual_exit_time` and `actual_return_time` with a 1:1 relationship to approved outpasses.

---

## 3. Key Relational Queries & Database Operations (Stage II Focus)

In accordance with the Stage II requirement for **"at least 3 meaningful queries/operations"**, HostelOut implements five critical queries driving its business logic:

### 3.1 Query 1: Hierarchical Multi-Level Outpass Routing & Status Pipeline
**Business Rationale:** In a multi-tier approval system, each authority must only see outpasses that have passed all preceding approval gates and require their specific intervention. For example, an HOD should only be notified if a leave request exceeds 7 calendar days AND both the Mentor and Warden have already approved it.

```sql
-- Query 1: Fetch pending extended outpasses for HOD (department-filtered)
SELECT 
    o.outpass_id,
    s.roll_no,
    s.name AS student_name,
    s.department,
    h.hostel_name,
    o.reason,
    o.destination,
    o.requested_departure,
    o.requested_return,
    DATEDIFF(o.requested_return, o.requested_departure) AS leave_days,
    o.mentor_approved,
    o.warden_approved,
    o.hod_approved
FROM outpasses o
INNER JOIN students s ON o.student_id = s.student_id
INNER JOIN hostels h ON s.hostel_id = h.hostel_id
WHERE s.department = 'CSE'
  AND o.status = 'PartiallyApproved'
  AND o.mentor_approved = TRUE
  AND o.warden_approved = TRUE
  AND o.hod_approved = FALSE
  AND DATEDIFF(o.requested_return, o.requested_departure) > 7
ORDER BY o.requested_departure ASC;
```

**SQLAlchemy ORM Expression:**
```python
outpasses = (
    Outpass.query
    .join(Student)
    .filter(
        Student.department == department,
        Outpass.status == OutpassStatus.PartiallyApproved,
        Outpass.mentor_approved == True,
        Outpass.warden_approved == True,
        Outpass.hod_approved == False
    )
    .order_by(Outpass.requested_departure.asc())
    .all()
)
```

---

### 3.2 Query 2: Real-Time Gate Overdue Detection & Security Discrepancy Monitoring
**Business Rationale:** Student safety requires real-time identification of individuals who have physically exited campus but failed to return by their scheduled return time.

```sql
-- Query 2: Real-time detection of overdue students with elapsed late minutes
SELECT 
    o.outpass_id,
    s.roll_no,
    s.name AS student_name,
    s.contact_no,
    h.hostel_name,
    w.name AS warden_name,
    w.contact_no AS warden_phone,
    gl.actual_exit_time,
    o.requested_return,
    TIMESTAMPDIFF(MINUTE, o.requested_return, UTC_TIMESTAMP()) AS overdue_minutes
FROM outpasses o
INNER JOIN students s ON o.student_id = s.student_id
INNER JOIN hostels h ON s.hostel_id = h.hostel_id
INNER JOIN wardens w ON h.warden_id = w.warden_id
INNER JOIN gate_log gl ON o.outpass_id = gl.outpass_id
WHERE o.status = 'Approved'
  AND gl.actual_exit_time IS NOT NULL
  AND gl.actual_return_time IS NULL
  AND UTC_TIMESTAMP() > o.requested_return
ORDER BY overdue_minutes DESC;
```

**SQLAlchemy ORM Expression & Dynamic Evaluation:**
```python
outpasses = (
    Outpass.query
    .join(Student)
    .join(GateLog)
    .filter(
        Student.hostel_id == hostel_id,
        Outpass.status == OutpassStatus.Approved,
        GateLog.actual_exit_time.isnot(None),
        GateLog.actual_return_time.is_(None)
    )
    .all()
)
# Live temporal calculation:
overdue = []
for op in outpasses:
    if now > op.requested_return:
        op_dict = _outpass_to_dict(op)
        op_dict['overdue_by_minutes'] = int((now - op.requested_return).total_seconds() / 60)
        overdue.append(op_dict)
```

---

### 3.3 Query 3: Multi-Authority Sequential Audit Trail Reconstruction
**Business Rationale:** Disciplinary reviews and campus audits require an immutable, chronological account of every approval and gate checkpoint event.

```sql
-- Query 3: Comprehensive lifecycle audit trail reconstruction
SELECT 
    o.outpass_id,
    s.roll_no,
    s.name AS student_name,
    a.approver_role,
    u.name AS approver_name,
    a.decision,
    a.remark,
    a.decided_at,
    gl.actual_exit_time,
    gl.actual_return_time
FROM outpasses o
INNER JOIN students s ON o.student_id = s.student_id
INNER JOIN approvals a ON o.outpass_id = a.outpass_id
INNER JOIN users u ON a.approved_by = u.user_id
LEFT JOIN gate_log gl ON o.outpass_id = gl.outpass_id
WHERE o.outpass_id = 101
ORDER BY a.decided_at ASC;
```

---

### 3.4 Query 4: Security Gate Anti-Tamper State Validation & Cooldown Query
**Business Rationale:** Prevents gate exit for non-approved outpasses and prevents fraudulent zero-second returns.

```sql
-- Query 4: Atomic gate validation and return gap calculation
SELECT 
    gl.gatelog_id,
    gl.outpass_id,
    gl.actual_exit_time,
    TIMESTAMPDIFF(MINUTE, gl.actual_exit_time, UTC_TIMESTAMP()) AS elapsed_minutes,
    CASE 
        WHEN TIMESTAMPDIFF(MINUTE, gl.actual_exit_time, UTC_TIMESTAMP()) < 30 
        THEN 30 - TIMESTAMPDIFF(MINUTE, gl.actual_exit_time, UTC_TIMESTAMP())
        ELSE 0 
    END AS remaining_cooldown_minutes
FROM gate_log gl
WHERE gl.outpass_id = :outpass_id
  AND gl.actual_return_time IS NULL;
```

---

### 3.5 Query 5: Hostel Occupancy & Cross-Departmental Outpass Analytics
**Business Rationale:** Enables administration to monitor how many students are currently off-campus per department and hostel for emergency preparedness.

```sql
-- Query 5: Aggregate live active leaves by hostel and department
SELECT 
    h.hostel_name,
    s.department,
    COUNT(o.outpass_id) AS total_active_outpasses,
    COUNT(CASE WHEN UTC_TIMESTAMP() > o.requested_return THEN 1 END) AS total_overdue_count
FROM outpasses o
INNER JOIN students s ON o.student_id = s.student_id
INNER JOIN hostels h ON s.hostel_id = h.hostel_id
INNER JOIN gate_log gl ON o.outpass_id = gl.outpass_id
WHERE gl.actual_exit_time IS NOT NULL 
  AND gl.actual_return_time IS NULL
GROUP BY h.hostel_name, s.department
ORDER BY total_active_outpasses DESC;
```

---

## 4. Core CRUD Operations & RESTful API Specifications

HostelOut provides 18 RESTful API endpoints covering the complete CRUD lifecycle:

| Method | Endpoint | Role | Payload Summary | HTTP Status | Functional Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **POST** | `/auth/login` | Public | `{email, password}` | 200 OK | Authenticates user; issues session cookie. |
| **GET** | `/auth/me` | Authenticated | None | 200 OK | Returns role-specific user details. |
| **POST** | `/auth/logout` | Authenticated | None | 200 OK | Invalidates current session. |
| **POST** | `/students` | Admin / Seed | `{name, roll_no, room_id, hostel_id, ...}` | 201 Created | Creates raw student record. |
| **POST** | `/admin/register-student` | Warden / HOD | `{name, email, password, roll_no, ...}` | 201 Created | Atomically creates both User and Student. |
| **POST** | `/outpasses` | Student | `{student_id, reason, destination, dep, ret}`| 201 Created | Submits outpass; computes HOD requirement. |
| **GET** | `/outpasses/student/<id>` | Student | None | 200 OK | Retrieves student's full outpass history. |
| **GET** | `/outpasses/pending/<hostel_id>` | Warden | None | 200 OK | Fetches pending outpasses for hostel. |
| **GET** | `/outpasses/pending/mentor/<id>` | Mentor | None | 200 OK | Fetches pending outpasses for mentee group. |
| **GET** | `/outpasses/pending/department/<dept>`| HOD | None | 200 OK | Fetches escalated leaves (>7 days) for HOD. |
| **POST** | `/outpasses/<id>/approve` | Approver | `{user_id, remark}` | 200 OK | Appends approval; updates state. |
| **POST** | `/outpasses/<id>/reject` | Approver | `{user_id, remark}` | 200 OK | Rejects outpass; appends remark. |
| **POST** | `/gatelog/<id>/exit` | Security | `{staff_id}` | 201 Created | Verifies Approved status; logs actual exit. |
| **POST** | `/gatelog/<id>/return` | Security | `{staff_id}` | 200 OK | Enforces 30-min gap; logs actual return. |
| **GET** | `/reports/overdue/<hostel_id>` | Warden | None | 200 OK | Returns live overdue report for hostel. |
| **GET** | `/reports/overdue/mentor/<id>` | Mentor | None | 200 OK | Returns live overdue report for mentor. |
| **GET** | `/reports/overdue/department/<dept>`| HOD | None | 200 OK | Returns live overdue report for department. |

---

## 5. Data Integrity, Business Logic & Validation Implementation

1. **Chronological Consistency**: Rejects requests where `requested_departure >= requested_return` or departure is in the past.
2. **Approval Hierarchy State Machine**:
   - Short Leave ($\le 7$ days): `Pending` $\rightarrow$ Mentor Approves $\rightarrow$ Warden Approves $\rightarrow$ `Approved`.
   - Extended Leave ($> 7$ days): `Pending` $\rightarrow$ Mentor Approves $\rightarrow$ Warden Approves $\rightarrow$ HOD Approves $\rightarrow$ `Approved`.
   - Premature HOD approval before Mentor/Warden yields `HTTP 400 Bad Request`.
3. **Gate Security Anti-Cheat Cooldown**: Minimum 30 minutes required between actual exit and actual return to prevent fraudulent instant check-ins.
4. **Cryptographic Protection**: Passwords securely hashed with salted PBKDF2:SHA-256 via `werkzeug.security`.
5. **Idempotent Operations**: Double-approval and double-return attempts return `HTTP 409 Conflict`.

---

## 6. Preliminary UI / API Demonstration & Workflow Walkthrough

### 6.1 Role-Specific Interface Modules
- **Student Dashboard**: Outpass submission form with real-time calendar picker, status progress pills, and digital outpass card.
- **Mentor Dashboard**: Mentee list review with inline student academic information and approval actions.
- **Warden Dashboard**: Hostel-wide view displaying student room numbers, contact numbers, and live overdue alerts.
- **HOD Dashboard**: High-level academic oversight portal displaying leaves $> 7$ days that have cleared Mentor and Warden approvals.
- **Security Desk**: Fast-search checkpoint interface for guards to log Exit and Return with instant visual confirmation.

---

## 7. Critical Design Decisions & Justifications

1. **MySQL 8.0 & SQLAlchemy ORM over NoSQL (MongoDB)**: The outpass domain is deeply relational. MySQL enforces ACID guarantees, cascading foreign keys, and referential constraints natively at the InnoDB engine level.
2. **Unified `users` Table with 1:1 Profiles**: Consolidates authentication, prevents duplicate campus email registrations, and provides a single `/auth/login` endpoint while cleanly isolating role-specific domain models.
3. **Dedicated Immutable `approvals` Ledger**: Maintains legal non-repudiation and timestamped audit logs for every decision rather than overwriting simple boolean columns.
4. **Dynamic Temporal Overdue Evaluation**: Evaluates late status on-the-fly (`UTC_TIMESTAMP() > requested_return`) during query time, eliminating background polling jobs and stale cache inconsistencies.

---

## 8. Verification, Testing & Test Suite Demonstration

HostelOut includes an automated integration test suite (`test_api.py`) verifying all critical functional paths:

| Test Case | Method & Endpoint | Payload / Condition | Expected HTTP | Actual HTTP | Result |
| :---: | :--- | :--- | :---: | :---: | :---: |
| 1 | `POST /students` | Create student record | 201 Created | 201 Created | **PASS** |
| 2 | `POST /outpasses` | Student submits valid outpass | 201 Created | 201 Created | **PASS** |
| 3 | `GET /outpasses/student/1` | Fetch student history | 200 OK | 200 OK | **PASS** |
| 4 | `GET /outpasses/pending/1` | Warden fetches pending list | 200 OK | 200 OK | **PASS** |
| 5 | `POST /outpasses/1/approve`| Warden approves outpass | 200 OK | 200 OK | **PASS** |
| 6 | `POST /outpasses/1/approve`| Attempt duplicate approval | 409 Conflict | 409 Conflict | **PASS** |
| 7 | `POST /outpasses/4/reject` | Reject outpass with remark | 200 OK | 200 OK | **PASS** |
| 8 | `POST /gatelog/1/exit` | Guard logs exit on Approved pass | 201 Created | 201 Created | **PASS** |
| 9 | `POST /gatelog/4/exit` | Attempt exit on Rejected pass | 403 Forbidden| 403 Forbidden| **PASS** |
| 10| `POST /gatelog/1/return` | Guard logs valid return | 200 OK | 200 OK | **PASS** |
| 11| `POST /gatelog/1/return` | Attempt duplicate return | 409 Conflict | 409 Conflict | **PASS** |
| 12| `GET /reports/overdue/1` | Query live overdue students | 200 OK | 200 OK | **PASS** |

**Summary: 12 / 12 Tests Passed (100% Pass Rate, 0 Failures)**

---

## 9. Stage II Assessment Rubric Alignment

- **Complexity of Database Design & Operations (8 Marks)**:
  - 11 normalized relational entities in 3NF.
  - Multi-level sequential state machine with dynamic escalation (>7 days).
  - 5 complex relational queries with multiple JOINs, DATEDIFF, TIMESTAMPDIFF, and GROUP BY aggregations.
  - Role-based data partitioning and isolation.
- **Design Implementation & Working Prototype Quality (2 Marks)**:
  - Flawless database schema generation and relational foreign keys.
  - Complete REST API (18 endpoints) with robust error codes (400, 401, 403, 404, 409).
  - Clean, reactive React client with 5 dedicated stakeholder dashboards.
  - Automated integration test suite validating edge cases.

---

## 10. Team Contribution Summary & Stage III Roadmap

### Team Member Contributions
- **Dipankar Bezbaruah (CSB24083)**: Database schema architect, MySQL normalization, SQLAlchemy ORM modeling, complex queries (Q1-Q5), Flask REST API backend.
- **Arnam Arni Gogoi (CSB24084)**: Frontend lead developer, React 18 single-page application, 5 stakeholder dashboard views, AuthContext integration, responsive UI.
- **Partha Sarathi Borgohain (CSB24004)**: Security & Quality Assurance engineer, automated test suite (`test_api.py`), validation logic, edge case handling, technical documentation.

### Stage III Roadmap (Final Application, Live Demonstration & Report - 30 Marks)
1. **Dynamic QR Code Pass**: Real-time QR generation on approved outpasses for rapid optical scanning at gate desks.
2. **Automated Notification Gateway**: SMS and email alerts dispatched to parents and wardens upon gate exit/entry events.
3. **Administrative Analytics Dashboard**: Chart.js data visualizations for campus administration tracking peak outpass periods and hostel occupancy trends.
4. **Containerized Deployment**: Docker containerization for automated multi-service deployment.
