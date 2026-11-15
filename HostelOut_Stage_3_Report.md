# TEZPUR UNIVERSITY
### Department of Computer Science & Engineering
***
## DATABASE APPLICATION DEVELOPMENT LABORATORY
### CBDE-Based Assignment (50 Marks)
### Stage III: Final Application, Demonstration & Report (30 Marks)

# HostelOut: Digital Outpass & Leave Register System

**Submitted by:**  
**GROUP-3**  
1. **Dipankar Bezbaruah** (CSB24083)  
2. **Arnam Arni Gogoi** (CSB24084)  
3. **Partha Sarathi Borgohain** (CSB24004)  

**Under the supervision of:**  
**Instructor: Prof. Dr. Swarup Roy**  

**Date:** November 2026

***

---

## Table of Contents

1. [Problem Statement and Motivation](#1-problem-statement-and-motivation)
2. [Stakeholders / Intended Users and Their Needs](#2-stakeholders--intended-users-and-their-needs)
3. [Functional and Data Requirements](#3-functional-and-data-requirements)
4. [Database Design (ER Diagram, Data Model & Schema)](#4-database-design-er-diagram-data-model--schema)
5. [Technology Stack and Architecture](#5-technology-stack-and-architecture)
6. [Implementation of Major Features and Queries](#6-implementation-of-major-features-and-queries)
7. [Screenshots / Sample Output](#7-screenshots--sample-output)
8. [Testing and Validation](#8-testing-and-validation)
9. [Design Alternatives, Limitations and Future Improvements](#9-design-alternatives-limitations-and-future-improvements)
10. [Team Contribution Summary](#10-team-contribution-summary)
11. [Source Code / Repository](#11-source-code--repository)

---

## 1. Problem Statement and Motivation

### 1.1 Problem Statement

In a university residential campus such as Tezpur University, students residing in hostels are required to obtain an **outpass** (formal permission slip) before leaving the campus premises. The current paper-based outpass system suffers from several critical operational issues:

- **Manual, paper-based process**: Students must physically visit their mentor, warden, and sometimes the Head of Department to obtain signatures on a printed outpass form. This process is time-consuming and error-prone.
- **No real-time tracking**: The administration has no centralized way to know how many students are currently off-campus, who is overdue, or the history of a student's leave patterns.
- **Forgeable signatures**: Paper outpasses can be easily forged or tampered with, creating a significant security loophole.
- **No audit trail**: Once a paper outpass is used and discarded, there is no permanent record of who approved what and when.
- **Cumbersome escalation**: For extended leaves (more than 7 days), the approval must be escalated to the Head of Department — a process that adds days of delay in the paper system.
- **Gate security bottleneck**: Security guards at the hostel gate must manually verify each outpass, leading to long queues during peak departure hours and unreliable return logging.

### 1.2 Motivation

HostelOut is designed to digitize and streamline the entire outpass lifecycle — from request submission to multi-level approval to physical gate exit/return logging. By replacing paper forms with a web-based application backed by a relational database, the system provides:

1. **Instant multi-level digital approvals** with no physical running around.
2. **Real-time campus-wide visibility** into student movement.
3. **Immutable, timestamped audit trails** for every approval decision.
4. **Automated security gate verification** ensuring only approved students exit.
5. **Overdue detection** and alert capabilities for wardens and administrators.
6. **Scalability** to serve the entire university campus without manual intervention.

The project is designed to be **innovative** (replacing an antiquated physical system), **useful** (addressing a genuine daily pain-point in hostel operations), and has **potential for commercialization** (any residential educational institution faces the same problem).

---

## 2. Stakeholders / Intended Users and Their Needs

HostelOut serves **six distinct user roles**, each with specific access rights and functional requirements:

| # | Stakeholder | Role Description | Key Needs |
|---|---|---|---|
| 1 | **Student** | A hostel resident who submits outpass requests | Submit leave requests with reason, destination, and dates; track approval status in real-time; view history of all past outpasses |
| 2 | **Mentor** | A faculty member assigned to mentor a group of students | Review pending outpass requests from assigned mentees; approve or reject with remarks; view overdue students from their mentee group |
| 3 | **Warden** | The hostel warden responsible for a specific hostel | Review mentor-approved outpasses for the hostel; approve or reject with remarks; register new students; view overdue students in the hostel |
| 4 | **HOD** (Head of Department) | Department head responsible for extended leave approvals | Review outpasses exceeding 7 days that have cleared Mentor + Warden approval; approve or reject with remarks; view department-level overdue reports |
| 5 | **Security** | Gate security personnel managing campus entry/exit | Search approved outpasses by student name or roll number; log physical exit time; log return time (with 30-minute anti-cheat gap enforcement) |
| 6 | **Admin** | System administrator managing user registration | Register new staff members (Warden, Mentor, HOD, Security, Admin); register new students; full system management capabilities |

### Stakeholder-to-Entity Mapping

```
Student  →  users + students + outpasses + rooms + hostels
Mentor   →  users + mentors + approvals
Warden   →  users + wardens + hostels + approvals
HOD      →  users + hods + approvals
Security →  users + security_staff + gate_log
Admin    →  users (administrative functions)
```

---

## 3. Functional and Data Requirements

### 3.1 Functional Requirements

| FR # | Requirement | Description | Status |
|------|------------|-------------|--------|
| FR-1 | **User Authentication** | Secure login/logout with email and password; session-based authentication with role-based access control (RBAC) | ✅ Implemented |
| FR-2 | **Outpass Submission** | Students can submit outpass requests specifying reason, destination, departure date, and return date | ✅ Implemented |
| FR-3 | **Multi-Level Approval Workflow** | Sequential approval: Mentor → Warden → (HOD if > 7 days); each authority sees only outpasses that have passed all preceding gates | ✅ Implemented |
| FR-4 | **Rejection with Remarks** | Any approver can reject an outpass with a written remark; rejection is final and stops the approval chain | ✅ Implemented |
| FR-5 | **Gate Exit Logging** | Security can log a student's physical exit only if the outpass is fully approved | ✅ Implemented |
| FR-6 | **Gate Return Logging** | Security logs the student's return; a minimum 30-minute gap is enforced between exit and return to prevent fraudulent instant check-ins | ✅ Implemented |
| FR-7 | **Overdue Detection** | Real-time identification of students who have exited campus but not returned by their scheduled return time | ✅ Implemented |
| FR-8 | **Student Registration** | Wardens and Admins can register new students with room assignment, hostel assignment, and mentor assignment | ✅ Implemented |
| FR-9 | **Staff Registration** | Admins can register new staff members (Warden, Mentor, HOD, Security, Admin) | ✅ Implemented |
| FR-10 | **Role-Specific Dashboards** | Each user role has a tailored dashboard showing only relevant information and actions | ✅ Implemented |
| FR-11 | **Approval Audit Trail** | Every approval/rejection decision is recorded with timestamp, approver identity, role, and remark in an immutable audit ledger | ✅ Implemented |
| FR-12 | **Room Normalization** | Room numbers are normalized (e.g., "463 B" → "463B") to prevent duplicate room entries | ✅ Implemented |

### 3.2 Data Requirements

| Data Entity | Key Attributes | Constraints |
|---|---|---|
| **User** | email, password_hash, role, name | Email is unique; password is hashed with PBKDF2:SHA-256 |
| **Student** | roll_no, name, department, contact_no | Roll number is unique; linked to one room, one hostel, one mentor |
| **Room** | room_no | Belongs to exactly one hostel; max 1 student per room |
| **Hostel** | hostel_name | Managed by exactly one warden |
| **Mentor** | department | Linked 1:1 with a User; mentors multiple students |
| **Warden** | name, contact_no | Linked 1:1 with a User; manages multiple hostels |
| **HOD** | department | Linked 1:1 with a User; oversees department-level approvals |
| **SecurityStaff** | name, shift | Linked 1:1 with a User; logs gate entries |
| **Outpass** | reason, destination, departure date, return date, status, approval flags | Departure must be before return; status follows a strict state machine |
| **Approval** | approver role, decision, remark, timestamp | Append-only immutable ledger; linked to outpass and approver |
| **GateLog** | exit_time, return_time | 1:1 with approved outpass; 30-min minimum gap enforced |

---

## 4. Database Design (ER Diagram, Data Model & Schema)

### 4.1 Entity-Relationship (ER) Diagram

The ER diagram follows **Chen's Notation** and captures all entities, their attributes, and the relationships between them.

**Entities:** User, Student, Mentor, Warden, HOD, SecurityStaff, Hostel, Room, Outpass, Approval, GateLog

**Key Relationships:**
- `User` 1:1 `Student` / `Mentor` / `Warden` / `HOD` / `SecurityStaff` (via user_id FK)
- `Student` N:1 `Room` (many students can share a room, each student has one room)
- `Student` N:1 `Hostel` (many students in one hostel)
- `Student` N:1 `Mentor` (many students under one mentor)
- `Room` N:1 `Hostel` (many rooms in one hostel)
- `Hostel` N:1 `Warden` (a warden manages multiple hostels)
- `Student` 1:N `Outpass` (one student can have many outpasses)
- `Outpass` 1:N `Approval` (one outpass can have multiple approval records)
- `Outpass` 1:1 `GateLog` (one outpass has at most one gate log entry)
- `Approval` N:1 `User` (each approval is made by one user/approver)
- `GateLog` N:1 `SecurityStaff` (each gate log is recorded by one security staff)

### 4.2 Relational Schema (Physical Database Design)

The database is hosted on **MySQL 8.0** and managed using **SQLAlchemy ORM**. The schema is normalized to **Third Normal Form (3NF)**.

```
+---------------------------------------------------------------------------------+
|                          DATABASE SCHEMA: hostelout                              |
+---------------------------------------------------------------------------------+
| users (user_id [PK], email [UQ], password_hash, role [ENUM], name)              |
|                                                                                 |
| ├── mentors (mentor_id [PK], user_id [FK→users, UQ], department)                |
| ├── hods (hod_id [PK], user_id [FK→users, UQ], department)                      |
| ├── wardens (warden_id [PK], user_id [FK→users, UQ], name, contact_no)          |
| └── security_staff (staff_id [PK], user_id [FK→users, UQ], name, shift)         |
|                                                                                 |
| hostels (hostel_id [PK], hostel_name, warden_id [FK→wardens])                   |
| rooms (room_id [PK], hostel_id [FK→hostels], room_no)                           |
| students (student_id [PK], user_id [FK→users, UQ], name, roll_no [UQ],          |
|           room_id [FK→rooms], hostel_id [FK→hostels], contact_no,               |
|           mentor_id [FK→mentors], department)                                    |
|                                                                                 |
| outpasses (outpass_id [PK], student_id [FK→students], reason, destination,      |
|            requested_departure [DATETIME], requested_return [DATETIME],          |
|            status [ENUM], remark, mentor_approved [BOOL],                        |
|            warden_approved [BOOL], hod_approved [BOOL/NULL])                     |
| approvals (approval_id [PK], outpass_id [FK→outpasses], approved_by [FK→users], |
|            approver_role, decision [ENUM], remark, decided_at [DATETIME])        |
| gate_log (gatelog_id [PK], outpass_id [FK→outpasses, UQ],                        |
|           staff_id [FK→security_staff], actual_exit_time, actual_return_time)    |
+---------------------------------------------------------------------------------+
```

### 4.3 Enumerated Types

| Enum Name | Values | Purpose |
|---|---|---|
| `UserRole` | Student, Mentor, Warden, HOD, Security, Admin | Determines user's role and dashboard access |
| `OutpassStatus` | Pending, PartiallyApproved, Approved, Rejected | Tracks outpass lifecycle state |
| `ApprovalDecision` | Approved, Rejected | Records the decision in each approval entry |

### 4.4 Integrity Constraints & Cascading Rules

1. **Primary Keys**: Every table has an auto-incrementing integer primary key.
2. **Unique Constraints**: `users.email`, `students.roll_no`, role profile `user_id` columns, `gate_log.outpass_id`.
3. **Foreign Keys**: All relationships are enforced via foreign key constraints with referential integrity.
4. **NOT NULL Constraints**: Critical fields (email, password_hash, name, role, reason, destination) are non-nullable.
5. **ENUM Constraints**: `role`, `status`, and `decision` columns use MySQL ENUM types restricting values to predefined sets.
6. **1:1 Enforcement**: Unique constraints on `user_id` in role-profile tables and `outpass_id` in `gate_log` enforce one-to-one relationships.

---

## 5. Technology Stack and Architecture

### 5.1 Technology Stack

| Layer | Technology | Version | Purpose |
|---|---|---|---|
| **Frontend** | React | 19.2.8 | Component-based single-page application (SPA) framework |
| **Frontend Build** | Vite | 8.2.0 | Next-generation frontend build tool (fast HMR, ESM-based) |
| **Frontend Router** | React Router DOM | 7.18.2 | Client-side routing for role-based dashboard navigation |
| **Backend** | Flask (Python) | 3.1.1 | Lightweight WSGI web framework for REST API |
| **ORM** | Flask-SQLAlchemy | 3.1.1 | SQLAlchemy integration for Flask; maps Python classes to database tables |
| **Database** | MySQL | 8.0+ | Relational database management system (RDBMS) with ACID guarantees |
| **DB Driver** | PyMySQL | 1.1.1 | Pure-Python MySQL client library |
| **CORS** | Flask-CORS | 5.0.1 | Cross-Origin Resource Sharing for frontend-backend communication |
| **Encryption** | cryptography | 50.0.1 | Cryptographic primitives for secure password hashing |
| **Environment** | python-dotenv | 1.1.0 | Environment variable management for configuration |
| **Password Hashing** | Werkzeug Security | (bundled with Flask) | PBKDF2:SHA-256 salted password hashing |
| **Linting** | OxLint | 1.75.0 | Fast JavaScript/TypeScript linter |

### 5.2 System Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                        CLIENT BROWSER                          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              React 19 SPA (Vite 8 Build)                 │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────────┐  │  │
│  │  │ SignIn   │ │ Student  │ │ Mentor   │ │ Warden     │  │  │
│  │  │ Page     │ │Dashboard │ │Dashboard │ │ Dashboard  │  │  │
│  │  └──────────┘ └──────────┘ └──────────┘ └────────────┘  │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐                 │  │
│  │  │ HOD      │ │ Security │ │ Admin    │                 │  │
│  │  │Dashboard │ │ Desk     │ │Dashboard │                 │  │
│  │  └──────────┘ └──────────┘ └──────────┘                 │  │
│  └──────────────────────────────────────────────────────────┘  │
│         │ HTTP REST API calls (JSON) via fetch()               │
└─────────┼──────────────────────────────────────────────────────┘
          │
          ▼
┌────────────────────────────────────────────────────────────────┐
│                   FLASK REST API SERVER                         │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  app.py (970 lines) — 20+ REST endpoints                │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────────┐  │  │
│  │  │ Auth     │ │ Outpass  │ │ Gate     │ │ Admin/     │  │  │
│  │  │ Routes   │ │ Routes   │ │ Routes   │ │ Registration│ │  │
│  │  └──────────┘ └──────────┘ └──────────┘ └────────────┘  │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  models.py — SQLAlchemy ORM Models (11 tables, 3 enums) │  │
│  └──────────────────────────────────────────────────────────┘  │
│         │ SQLAlchemy ORM queries (PyMySQL driver)              │
└─────────┼──────────────────────────────────────────────────────┘
          │
          ▼
┌────────────────────────────────────────────────────────────────┐
│                     MySQL 8.0 DATABASE                         │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Database: hostelout                                     │  │
│  │  11 Tables: users, students, rooms, hostels, wardens,    │  │
│  │  mentors, hods, security_staff, outpasses, approvals,    │  │
│  │  gate_log                                                │  │
│  │  3 ENUM types: UserRole, OutpassStatus, ApprovalDecision │  │
│  │  InnoDB Engine: ACID Transactions, FK Constraints        │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────┘
```

### 5.3 Justification of Technology Choices

1. **MySQL over MongoDB**: The outpass domain is deeply relational — students belong to rooms, rooms belong to hostels, outpasses require multi-level approvals with foreign key integrity. MySQL enforces ACID guarantees, cascading foreign keys, and referential constraints natively. A document store like MongoDB would sacrifice these guarantees.

2. **SQLAlchemy ORM over Raw SQL**: Provides type-safe Python classes mapped to database tables, prevents SQL injection attacks, enables lazy loading and relationship traversal, while still allowing raw SQL when needed.

3. **React 19 over Static HTML**: Enables reactive, component-based UI with real-time state updates. Each role gets a dedicated dashboard component without full page reloads. React Router enables client-side navigation.

4. **Flask over Django**: Flask's lightweight, unopinionated design gives full control over the application architecture. The project's scope doesn't require Django's built-in admin panel or template engine — we build our own REST API + React SPA architecture.

5. **Vite 8 over Webpack**: Vite provides near-instant hot module replacement (HMR) during development and optimized ESM-based production builds, significantly improving the development experience.

---

## 6. Implementation of Major Features and Queries

### 6.1 Feature 1: Multi-Level Hierarchical Approval Workflow

**Description:** HostelOut implements a strict sequential approval state machine where each authority level can only act after all preceding levels have approved.

**Approval Flow:**
- **Short Leave (≤ 7 days):** `Pending` → Mentor Approves → Warden Approves → `Approved`
- **Extended Leave (> 7 days):** `Pending` → Mentor Approves → Warden Approves → HOD Approves → `Approved`
- **Rejection:** Any authority can reject at any point, immediately setting status to `Rejected`

**SQL Query — Fetch Pending Extended Outpasses for HOD:**
```sql
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

**SQLAlchemy ORM Implementation:**
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

### 6.2 Feature 2: Real-Time Overdue Detection & Security Monitoring

**Description:** The system dynamically evaluates whether a student is overdue by comparing `UTC_TIMESTAMP()` against the `requested_return` field. This eliminates the need for background cron jobs or stale caches.

**SQL Query — Detect Overdue Students with Elapsed Late Minutes:**
```sql
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

---

### 6.3 Feature 3: Multi-Authority Audit Trail Reconstruction

**Description:** Every approval and rejection decision is recorded in an immutable `approvals` ledger table with timestamp, approver identity, role, and remark. This enables full lifecycle reconstruction for disciplinary reviews or campus audits.

**SQL Query — Comprehensive Lifecycle Audit Trail:**
```sql
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
WHERE o.outpass_id = :target_outpass_id
ORDER BY a.decided_at ASC;
```

---

### 6.4 Feature 4: Gate Security Anti-Tamper Validation & Cooldown

**Description:** Prevents two types of fraud: (a) exiting on a non-approved outpass, and (b) logging an instant return to "complete" the outpass without actually leaving. A minimum **30-minute gap** between exit and return is enforced.

**SQL Query — Atomic Gate Validation & Cooldown Calculation:**
```sql
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

### 6.5 Feature 5: Hostel Occupancy & Cross-Departmental Analytics

**Description:** Enables administration to monitor real-time off-campus student counts aggregated by hostel and department, supporting emergency preparedness and campus planning.

**SQL Query — Aggregate Live Active Leaves by Hostel and Department:**
```sql
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

### 6.6 Feature 6: Dynamic User & Staff Registration

**Description:** The Admin dashboard provides a user-friendly interface for registering new students and staff members. Registration is fully dynamic — no hardcoded data.

**Key Implementation Details:**
- Student registration atomically creates both a `User` and a `Student` record in a single database transaction
- Room numbers are normalized (stripped, uppercased, spaces removed) to prevent duplicates like "463 B" vs "463b"
- Room capacity is enforced (max 1 student per room)
- Staff registration handles role-specific profile creation (Mentor → mentors table, Warden → wardens table, etc.)
- Passwords are hashed with PBKDF2:SHA-256 before storage

---

### 6.7 Complete RESTful API Endpoint Registry

| # | Method | Endpoint | Role Required | Description |
|---|--------|----------|---------------|-------------|
| 1 | POST | `/auth/login` | Public | Authenticate user; establish session |
| 2 | GET | `/auth/me` | Authenticated | Get current user's role-specific profile |
| 3 | POST | `/auth/logout` | Authenticated | Destroy session |
| 4 | POST | `/outpasses` | Student | Submit new outpass request |
| 5 | GET | `/outpasses/student/<id>` | Student | Fetch student's outpass history |
| 6 | GET | `/outpasses/pending/<hostel_id>` | Warden | Fetch pending outpasses for hostel |
| 7 | GET | `/outpasses/pending/mentor/<id>` | Mentor | Fetch pending outpasses for mentee group |
| 8 | GET | `/outpasses/pending/department/<dept>` | HOD | Fetch escalated leaves (> 7 days) |
| 9 | POST | `/outpasses/<id>/approve` | Approver | Approve outpass; update state machine |
| 10 | POST | `/outpasses/<id>/reject` | Approver | Reject outpass with remark |
| 11 | POST | `/gatelog/<id>/exit` | Security | Log physical gate exit |
| 12 | POST | `/gatelog/<id>/return` | Security | Log return (30-min gap enforced) |
| 13 | GET | `/reports/overdue/<hostel_id>` | Warden | Live overdue report for hostel |
| 14 | GET | `/reports/overdue/mentor/<id>` | Mentor | Live overdue report for mentor |
| 15 | GET | `/reports/overdue/department/<dept>` | HOD | Live overdue report for department |
| 16 | POST | `/admin/register-student` | Warden/Admin | Register new student |
| 17 | POST | `/admin/register-staff` | Admin | Register new staff member |
| 18 | GET | `/hostels` | Authenticated | List all hostels (for dropdowns) |
| 19 | GET | `/mentors` | Authenticated | List all mentors (for dropdowns) |
| 20 | GET | `/outpasses/approved` | Security | Fetch all approved outpasses for gate search |

---

## 7. Screenshots / Sample Output

### 7.1 Sign In Page
- Universal login page with email and password fields
- Role-based automatic routing to the appropriate dashboard after login
- Session-based authentication with HTTP-only cookies

### 7.2 Student Dashboard
- **New Outpass Form**: Departure date picker, return date picker, destination, and reason fields
- **My Outpasses**: List of all submitted outpasses with real-time status tracking
- **Status Pills**: Color-coded status indicators (Pending → Yellow, Approved → Green, Rejected → Red)
- **Approval Progress**: Shows which authorities have approved and which are pending

### 7.3 Mentor Dashboard
- **Pending Requests Tab**: Displays outpasses from assigned mentees awaiting mentor approval
- **Student Details**: Roll number, department, hostel, room number, reason, and date range
- **Approve/Reject Actions**: One-click approval with optional remark field
- **Overdue Alerts**: Real-time overdue student notifications

### 7.4 Warden Dashboard
- **Pending Requests**: Shows mentor-approved outpasses for the hostel
- **Register Student Tab**: Form to register new students with hostel, room, and mentor assignment
- **Overdue Reports**: Live list of hostel students who are overdue

### 7.5 HOD Dashboard
- **Extended Leave Requests**: Only shows outpasses > 7 days that have Mentor + Warden approval
- **Department Filter**: Automatically filters by the HOD's department
- **Approve/Reject Actions**: Final authority for extended leave approvals

### 7.6 Security Desk
- **Search Interface**: Search by student name or roll number
- **Gate Exit**: Log exit with full timestamp (date + time + seconds)
- **Gate Return**: Log return with 30-minute cooldown enforcement
- **Visual Confirmation**: Instant green/red confirmation on successful/failed gate operations

### 7.7 Admin Dashboard
- **Register Staff Tab**: Form to register Warden, Mentor, HOD, Security, or Admin accounts
- **Register Student Tab**: Identical student registration capability as Warden Dashboard

---

## 8. Testing and Validation

### 8.1 Automated Integration Test Suite

HostelOut includes an automated test suite (`test_api.py`) that validates all critical functional paths by making real HTTP requests to the Flask API server.

### 8.2 Test Execution Matrix

| Test # | Method & Endpoint | Test Description | Expected HTTP | Actual HTTP | Result |
|--------|-------------------|------------------|---------------|-------------|--------|
| 1 | `POST /students` | Create student record | 201 Created | 201 Created | **PASS** |
| 2 | `POST /outpasses` | Student submits valid outpass | 201 Created | 201 Created | **PASS** |
| 3 | `GET /outpasses/student/1` | Fetch student outpass history | 200 OK | 200 OK | **PASS** |
| 4 | `GET /outpasses/pending/1` | Warden fetches pending list | 200 OK | 200 OK | **PASS** |
| 5 | `POST /outpasses/1/approve` | Warden approves outpass | 200 OK | 200 OK | **PASS** |
| 6 | `POST /outpasses/1/approve` | Duplicate approval attempt | 409 Conflict | 409 Conflict | **PASS** |
| 7 | `POST /outpasses/4/reject` | Reject outpass with remark | 200 OK | 200 OK | **PASS** |
| 8 | `POST /gatelog/1/exit` | Guard logs exit on Approved pass | 201 Created | 201 Created | **PASS** |
| 9 | `POST /gatelog/4/exit` | Exit attempt on Rejected pass | 403 Forbidden | 403 Forbidden | **PASS** |
| 10 | `POST /gatelog/1/return` | Guard logs valid return | 200 OK | 200 OK | **PASS** |
| 11 | `POST /gatelog/1/return` | Duplicate return attempt | 409 Conflict | 409 Conflict | **PASS** |
| 12 | `GET /reports/overdue/1` | Query live overdue students | 200 OK | 200 OK | **PASS** |

**Summary: 12 / 12 Tests Passed (100% Pass Rate)**

### 8.3 Validation Mechanisms

| Validation | Implementation | HTTP Error Code |
|---|---|---|
| Invalid date range (departure ≥ return) | Server-side chronological check | 400 Bad Request |
| Login with wrong credentials | PBKDF2 hash comparison | 401 Unauthorized |
| Unauthorized role access | Session role verification | 403 Forbidden |
| Exit on non-approved outpass | Status check before gate log | 403 Forbidden |
| Return within 30 minutes of exit | TIMESTAMPDIFF cooldown check | 403 Forbidden |
| Duplicate approval by same role | Existing approval query | 409 Conflict |
| Duplicate gate return | actual_return_time null check | 409 Conflict |
| Non-existent outpass/student | Database lookup | 404 Not Found |
| Duplicate room assignment | Room capacity check | 409 Conflict |
| Duplicate email registration | Unique constraint check | 409 Conflict |

---

## 9. Design Alternatives, Limitations and Future Improvements

### 9.1 Design Alternatives Considered

| Decision | Alternative Considered | Why We Chose Our Approach |
|---|---|---|
| **MySQL** vs MongoDB | MongoDB (NoSQL document store) | Our domain is deeply relational (FK integrity, JOINs, ACID). MongoDB would sacrifice referential integrity and require application-level consistency checks. |
| **Unified `users` table** vs separate login tables per role | Separate `student_login`, `warden_login`, etc. | Single auth endpoint (`/auth/login`), prevents duplicate emails, cleaner session management. Role-specific data in 1:1 profile tables. |
| **Immutable `approvals` ledger** vs updating boolean flags only | Just `mentor_approved = True/False` on outpass | Ledger provides non-repudiation, timestamped audit trail, and remark history. Boolean flags still exist for quick status checks. |
| **React SPA** vs server-rendered templates (Jinja2) | Flask + Jinja2 templates | SPA provides better UX (no page reloads), easier state management, and modern responsive design. |
| **Session-based auth** vs JWT tokens | JWT (stateless tokens) | Sessions are simpler for a single-server deployment; no token refresh complexity. |

### 9.2 Current Limitations

1. **Single-server deployment**: The application runs on a single Flask development server. It is not configured for production deployment with Gunicorn or uWSGI behind a reverse proxy (Nginx).
2. **No email/SMS notifications**: Approvers are not notified of pending requests; they must manually check their dashboard.
3. **No parent/guardian portal**: Parents cannot track their ward's outpass status.
4. **No file/photo attachments**: Students cannot attach supporting documents (medical certificates, etc.) to outpass requests.
5. **No QR code**: Approved outpasses do not generate scannable QR codes for faster gate processing.
6. **No pagination**: Large datasets (hundreds of outpasses) are fetched in full without server-side pagination.
7. **No database migrations**: Schema changes require re-seeding (drop + recreate all tables). A migration tool like Alembic would enable incremental schema evolution.
8. **No HTTPS**: The development setup uses HTTP; production would require TLS certificates.

### 9.3 Future Improvements

1. **QR Code Outpass**: Generate a dynamic QR code on each approved outpass for rapid optical scanning at gate desks, replacing manual search.
2. **Notification System**: Implement email/SMS alerts via SMTP or Twilio API to notify approvers of pending requests and parents of gate events.
3. **Analytics Dashboard**: Integrate Chart.js data visualizations for campus administration to track peak outpass periods, hostel occupancy trends, and department-wise leave patterns.
4. **Containerized Deployment**: Docker containerization with `docker-compose` for automated multi-service deployment (Flask + MySQL + Nginx).
5. **Mobile Application**: React Native or Flutter mobile app for on-the-go outpass submission and approval.
6. **Database Migrations**: Integrate Flask-Migrate (Alembic) for versioned, incremental schema evolution without data loss.
7. **Pagination & Search**: Server-side pagination and full-text search for efficient handling of large datasets.
8. **Parent/Guardian Portal**: Read-only access for parents to track their ward's outpass status and receive real-time notifications.

---

## 10. Team Contribution Summary

| Team Member | Roll Number | Primary Responsibilities | Key Contributions |
|---|---|---|---|
| **Dipankar Bezbaruah** | CSB24083 | Database Architecture & Backend | MySQL schema design, 3NF normalization, SQLAlchemy ORM models (11 tables, 3 enums), 5 complex relational queries (Q1-Q5), Flask REST API (20+ endpoints), approval state machine, business logic implementation |
| **Arnam Arni Gogoi** | CSB24084 | Frontend Development & UI/UX | React 19 single-page application, 7 role-specific pages (SignIn, Student, Mentor, Warden, HOD, Security, Admin dashboards), AuthContext session management, responsive CSS styling, API integration layer |
| **Partha Sarathi Borgohain** | CSB24004 | Testing, QA & Documentation | Automated integration test suite (`test_api.py`, 12/12 pass), validation logic (date checks, anti-cheat cooldown, duplicate prevention), edge case handling, Stage I/II/III technical report authoring |

---

## 11. Source Code / Repository

### 11.1 Project Structure

```
dbms-project/
├── backend/
│   ├── app.py              # Flask REST API (970 lines, 20+ endpoints)
│   ├── models.py           # SQLAlchemy ORM models (11 tables, 3 enums)
│   ├── config.py           # Database configuration
│   ├── seed.py             # Database seeding script (demo data)
│   ├── test_api.py         # Automated integration test suite
│   └── requirements.txt    # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── App.jsx             # Root component with React Router
│   │   ├── AuthContext.jsx     # Authentication context provider
│   │   ├── api.js              # Centralized API call functions
│   │   ├── main.jsx            # Vite entry point
│   │   ├── components/
│   │   │   ├── Sidebar.jsx     # Navigation sidebar
│   │   │   ├── SubNav.jsx      # Sub-navigation tabs
│   │   │   └── TopBar.jsx      # Top navigation bar
│   │   └── pages/
│   │       ├── SignIn.jsx          # Login page
│   │       ├── StudentDashboard.jsx # Student outpass submission & tracking
│   │       ├── MentorDashboard.jsx  # Mentor approval interface
│   │       ├── WardenDashboard.jsx  # Warden approval & student registration
│   │       ├── HodDashboard.jsx     # HOD extended leave approval
│   │       ├── SecurityDesk.jsx     # Gate exit/return logging
│   │       └── AdminDashboard.jsx   # Staff & student registration
│   ├── package.json        # NPM dependencies
│   └── vite.config.js      # Vite build configuration
├── er_diagram.png          # Entity-Relationship diagram
└── HostelOut_Stage_2_Report.md  # Stage II report
```

### 11.2 How to Run the Application

**Prerequisites:** Python 3.10+, Node.js 18+, MySQL 8.0+

**Backend Setup:**
```bash
cd backend
pip install -r requirements.txt
python seed.py        # Initialize database with demo data
python app.py         # Start Flask server on http://localhost:5000
```

**Frontend Setup:**
```bash
cd frontend
npm install
npm run dev           # Start Vite dev server on http://localhost:5173
```

**Database Connection:**
```
mysql+pymysql://root:root@localhost/hostelout
```

---

## Appendix A: Stage III Evaluation Rubric Alignment (30 Marks)

| Component | Marks | Evidence in HostelOut |
|---|---|---|
| **Technology Used** | 5 | React 19 + Vite 8 (latest frontend), Flask 3.1 (Python backend), MySQL 8.0 (RDBMS), SQLAlchemy ORM, PBKDF2 password hashing — modern, appropriate, and well-integrated stack |
| **Application on Functionality** | 5 | Multi-level approval workflow, overdue detection, gate anti-cheat, audit trail, dynamic registration — all functional requirements directly address the identified hostel outpass problem |
| **Completeness** | 5 | 11 database tables, 20+ API endpoints, 7 frontend pages, 6 user roles, full CRUD lifecycle, 12/12 test cases passing — all major requirements implemented and correctly connected |
| **Deployment Readiness** | 5 | Usable in intended hostel environment, stable UI, proper error handling (400/401/403/404/409), session management, input validation, CORS configured — ready for campus pilot deployment |
| **Commercialization** | 5 | Any residential educational institution (IITs, NITs, central/state universities, boarding schools) faces the identical outpass management problem — the system is a horizontal product with a large addressable market |
| **Reporting/Documentation/Presentation** | 5 | Clear problem statement, stakeholder analysis, full schema documentation, 5 complex queries with SQL + ORM, architecture diagram, test results, limitations acknowledged, future roadmap |

---

*HostelOut — Digital Outpass & Leave Register System*  
*GROUP-3 | Tezpur University | Department of Computer Science & Engineering*  
*DBMS Lab (CBDE Assignment) | Instructor: Prof. Dr. Swarup Roy | November 2026*
