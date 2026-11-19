"""HostelOut -- Flask REST API for Digital Outpass & Leave Register."""

import os
from datetime import datetime, timedelta, timezone

from flask import Flask, request, jsonify, session
from flask_cors import CORS

from config import Config
from models import (
    db,
    User,
    UserRole,
    Hostel,
    Warden,
    Mentor,
    HOD,
    Room,
    Student,
    SecurityStaff,
    Outpass,
    Approval,
    GateLog,
    OutpassStatus,
    ApprovalDecision,
)


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Cookie settings for cross-domain deployment (Vercel frontend -> Render backend)
    app.config['SESSION_COOKIE_SAMESITE'] = 'None'
    app.config['SESSION_COOKIE_SECURE'] = True
    app.config['SESSION_COOKIE_HTTPONLY'] = True

    db.init_app(app)

    # Allow requests from your Vercel frontend
    allowed_origins = [
        "http://localhost:5173",                                        # local Vite dev
        "http://localhost:5000",                                        # local Flask dev
        os.environ.get("FRONTEND_URL", "http://localhost:5173"),        # production
    ]
    CORS(app, supports_credentials=True, origins=allowed_origins)
    return app


app = create_app()

# Minimum minutes between exit and return logging (anti-cheat)
MIN_RETURN_GAP_MINUTES = 30


# -- Helpers -------------------------------------------------------------------

def _now():
    """Return the current UTC time."""
    return datetime.now(timezone.utc)


def _outpass_to_dict(op: Outpass) -> dict:
    """Serialize an Outpass (and nested approvals / gate_log) to a dict."""
    d = {
        "outpass_id": op.outpass_id,
        "student_id": op.student_id,
        "student_name": op.student.name,
        "roll_no": op.student.roll_no,
        "department": op.student.department,
        "hostel_name": op.student.hostel.hostel_name if op.student.hostel else None,
        "warden_name": op.student.hostel.warden.name if op.student.hostel and op.student.hostel.warden else None,
        "reason": op.reason,
        "destination": op.destination,
        "requested_departure": op.requested_departure.isoformat(),
        "requested_return": op.requested_return.isoformat(),
        "leave_days": op.leave_days,
        "status": op.status.value,
        "remark": op.remark,
        # Multi-level approval status
        "mentor_approved": op.mentor_approved,
        "warden_approved": op.warden_approved,
        "hod_approved": op.hod_approved,
        "requires_hod": op.requires_hod,
    }

    # All approval records
    approval_list = []
    for a in op.approvals:
        approval_list.append({
            "approval_id": a.approval_id,
            "approved_by": a.approved_by,
            "approver_name": a.approver.name if a.approver else None,
            "approver_role": a.approver_role,
            "decision": a.decision.value,
            "remark": a.remark,
            "decided_at": a.decided_at.isoformat(),
        })
    d["approvals"] = approval_list

    if op.gate_log:
        d["gate_log"] = {
            "gatelog_id": op.gate_log.gatelog_id,
            "staff_id": op.gate_log.staff_id,
            "actual_exit_time": (
                op.gate_log.actual_exit_time.isoformat()
                if op.gate_log.actual_exit_time
                else None
            ),
            "actual_return_time": (
                op.gate_log.actual_return_time.isoformat()
                if op.gate_log.actual_return_time
                else None
            ),
        }

    # Computed overdue flag
    if op.status == OutpassStatus.Approved and op.gate_log and op.gate_log.actual_exit_time:
        compare_time = op.gate_log.actual_return_time or _now()
        req_return = op.requested_return
        if req_return.tzinfo is None:
            req_return = req_return.replace(tzinfo=timezone.utc)
        if compare_time.tzinfo is None:
            compare_time = compare_time.replace(tzinfo=timezone.utc)
        if compare_time > req_return:
            d["is_overdue"] = True
            d["overdue_by_minutes"] = int((compare_time - req_return).total_seconds() / 60)
        else:
            d["is_overdue"] = False
            d["overdue_by_minutes"] = 0
    else:
        d["is_overdue"] = False
        d["overdue_by_minutes"] = 0
    return d


def _user_payload(user: User) -> dict:
    """Build the JSON payload returned on login / /auth/me."""
    payload = {
        "user_id": user.user_id,
        "email": user.email,
        "name": user.name,
        "role": user.role.value,
    }
    if user.role == UserRole.Student and user.student:
        s = user.student
        payload["student_id"] = s.student_id
        payload["roll_no"] = s.roll_no
        payload["hostel_id"] = s.hostel_id
        payload["hostel_name"] = s.hostel.hostel_name if s.hostel else None
        payload["warden_name"] = s.hostel.warden.name if s.hostel and s.hostel.warden else None
        payload["room_no"] = s.room.room_no if s.room else None
        payload["mentor_id"] = s.mentor_id
        payload["department"] = s.department
    elif user.role == UserRole.Warden and user.warden:
        w = user.warden
        payload["warden_id"] = w.warden_id
        payload["contact_no"] = w.contact_no
        payload["hostels"] = [
            {"hostel_id": h.hostel_id, "hostel_name": h.hostel_name}
            for h in w.hostels
        ]
        if w.hostels:
            payload["hostel_id"] = w.hostels[0].hostel_id
            payload["hostel_name"] = w.hostels[0].hostel_name
    elif user.role == UserRole.Mentor and user.mentor:
        m = user.mentor
        payload["mentor_id"] = m.mentor_id
        payload["department"] = m.department
    elif user.role == UserRole.HOD and user.hod:
        h = user.hod
        payload["hod_id"] = h.hod_id
        payload["department"] = h.department
    elif user.role == UserRole.Security and user.security_staff:
        ss = user.security_staff
        payload["staff_id"] = ss.staff_id
        payload["shift"] = ss.shift

    return payload


# -- Auth Routes ---------------------------------------------------------------

@app.route("/auth/login", methods=["POST"])
def login():
    """Authenticate a user by email + password, return user info."""
    data = request.get_json(force=True)
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({"error": "Invalid email or password"}), 401

    session["user_id"] = user.user_id
    return jsonify(_user_payload(user)), 200


@app.route("/auth/me", methods=["GET"])
def auth_me():
    """Return the currently logged-in user (from session)."""
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Not authenticated"}), 401

    user = db.session.get(User, user_id)
    if not user:
        session.pop("user_id", None)
        return jsonify({"error": "User not found"}), 401

    return jsonify(_user_payload(user)), 200


@app.route("/auth/logout", methods=["POST"])
def logout():
    """Clear the session."""
    session.pop("user_id", None)
    return jsonify({"message": "Logged out"}), 200


# -- Student Routes ------------------------------------------------------------

@app.route("/students", methods=["POST"])
def create_student():
    """Create a new student (for seeding / testing)."""
    data = request.get_json(force=True)
    required = ("name", "roll_no", "room_id", "hostel_id", "contact_no", "user_id")
    missing = [f for f in required if f not in data]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    student = Student(
        name=data["name"],
        roll_no=data["roll_no"],
        room_id=data["room_id"],
        hostel_id=data["hostel_id"],
        contact_no=data["contact_no"],
        user_id=data["user_id"],
        mentor_id=data.get("mentor_id"),
        department=data.get("department"),
    )
    db.session.add(student)
    db.session.commit()
    return jsonify({
        "message": "Student created",
        "student_id": student.student_id,
    }), 201


# -- Admin: Register a new student --------------------------------------------

@app.route("/admin/register-student", methods=["POST"])
def admin_register_student():
    """
    Admin endpoint: Warden or HOD registers a new student.
    Creates both User and Student records in one call.
    """
    data = request.get_json(force=True)

    # Check that the caller is a Warden or HOD
    caller_user_id = data.get("caller_user_id")
    if caller_user_id:
        caller = db.session.get(User, caller_user_id)
        if not caller or caller.role not in {UserRole.Warden, UserRole.HOD, UserRole.Admin}:
            return jsonify({"error": "Only Wardens, HODs, or Admins can register students"}), 403

    required = ("name", "email", "password", "roll_no", "department",
                "hostel_id", "room_no", "contact_no", "mentor_id")
    missing = [f for f in required if f not in data]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    # Check if email already exists
    if User.query.filter_by(email=data["email"].strip().lower()).first():
        return jsonify({"error": "Email already registered"}), 409

    # Check if roll_no already exists
    if Student.query.filter_by(roll_no=data["roll_no"]).first():
        return jsonify({"error": "Roll number already registered"}), 409

    # Find or create the room in the given hostel
    hostel_id = data["hostel_id"]
    room_no = str(data["room_no"]).strip().upper().replace(" ", "")
    room = Room.query.filter_by(hostel_id=hostel_id, room_no=room_no).first()
    if not room:
        room = Room(hostel_id=hostel_id, room_no=room_no)
        db.session.add(room)
        db.session.flush()
    else:
        # Check room capacity (max 1 student per room)
        current_occupants = Student.query.filter_by(room_id=room.room_id).count()
        if current_occupants >= 1:
            return jsonify({
                "error": f"Room {room_no} is already occupied. "
                         f"Please assign a different room."
            }), 409

    # Create User
    user = User(
        email=data["email"].strip().lower(),
        role=UserRole.Student,
        name=data["name"],
    )
    user.set_password(data["password"])
    db.session.add(user)
    db.session.flush()

    # Create Student
    student = Student(
        user_id=user.user_id,
        name=data["name"],
        roll_no=data["roll_no"],
        room_id=room.room_id,
        hostel_id=hostel_id,
        contact_no=data["contact_no"],
        mentor_id=data["mentor_id"],
        department=data["department"],
    )
    db.session.add(student)
    db.session.commit()

    return jsonify({
        "message": "Student registered successfully",
        "student_id": student.student_id,
        "user_id": user.user_id,
        "email": user.email,
    }), 201


# -- Outpass Routes ------------------------------------------------------------

@app.route("/outpasses", methods=["POST"])
def create_outpass():
    """Student submits a new outpass request."""
    data = request.get_json(force=True)
    required = (
        "student_id", "reason", "destination",
        "requested_departure", "requested_return",
    )
    missing = [f for f in required if f not in data]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    student = db.session.get(Student, data["student_id"])
    if not student:
        return jsonify({"error": "Student not found"}), 404

    departure = datetime.fromisoformat(data["requested_departure"])
    return_dt = datetime.fromisoformat(data["requested_return"])
    leave_days = (return_dt.date() - departure.date()).days

    outpass = Outpass(
        student_id=data["student_id"],
        reason=data["reason"],
        destination=data["destination"],
        requested_departure=departure,
        requested_return=return_dt,
        status=OutpassStatus.Pending,
        mentor_approved=False,
        warden_approved=False,
        hod_approved=None if leave_days <= 7 else False,
    )
    db.session.add(outpass)
    db.session.commit()
    return jsonify({
        "message": "Outpass request created",
        "outpass_id": outpass.outpass_id,
        "requires_hod": leave_days > 7,
    }), 201


@app.route("/outpasses/student/<int:student_id>", methods=["GET"])
def student_outpasses(student_id):
    """Student views their own outpass history."""
    student = db.session.get(Student, student_id)
    if not student:
        return jsonify({"error": "Student not found"}), 404

    outpasses = (
        Outpass.query
        .filter_by(student_id=student_id)
        .order_by(Outpass.requested_departure.desc())
        .all()
    )
    return jsonify([_outpass_to_dict(op) for op in outpasses]), 200


# -- Pending outpasses for each role -------------------------------------------

@app.route("/outpasses/pending/<int:hostel_id>", methods=["GET"])
def pending_outpasses_warden(hostel_id):
    """Warden views outpasses needing their approval for their hostel."""
    hostel = db.session.get(Hostel, hostel_id)
    if not hostel:
        return jsonify({"error": "Hostel not found"}), 404

    outpasses = (
        Outpass.query
        .join(Student)
        .filter(
            Student.hostel_id == hostel_id,
            Outpass.status.in_([OutpassStatus.Pending, OutpassStatus.PartiallyApproved]),
            Outpass.warden_approved == False,
        )
        .order_by(Outpass.requested_departure.asc())
        .all()
    )
    return jsonify([_outpass_to_dict(op) for op in outpasses]), 200


@app.route("/outpasses/pending/mentor/<int:mentor_id>", methods=["GET"])
def mentor_pending_outpasses(mentor_id):
    """Mentor views outpasses needing their approval from their mentees."""
    mentor = db.session.get(Mentor, mentor_id)
    if not mentor:
        return jsonify({"error": "Mentor not found"}), 404

    outpasses = (
        Outpass.query
        .join(Student)
        .filter(
            Student.mentor_id == mentor_id,
            Outpass.status.in_([OutpassStatus.Pending, OutpassStatus.PartiallyApproved]),
            Outpass.mentor_approved == False,
        )
        .order_by(Outpass.requested_departure.asc())
        .all()
    )
    return jsonify([_outpass_to_dict(op) for op in outpasses]), 200


@app.route("/outpasses/pending/department/<department>", methods=["GET"])
def department_pending_outpasses(department):
    """
    HOD views outpasses needing their approval.
    Only shows outpasses that:
      1. Are > 7 days
      2. Both mentor AND warden have already approved
      3. HOD has NOT yet approved
    """
    outpasses = (
        Outpass.query
        .join(Student)
        .filter(
            Student.department == department,
            Outpass.status == OutpassStatus.PartiallyApproved,
            Outpass.mentor_approved == True,
            Outpass.warden_approved == True,
            Outpass.hod_approved == False,
        )
        .order_by(Outpass.requested_departure.asc())
        .all()
    )
    return jsonify([_outpass_to_dict(op) for op in outpasses]), 200


# -- All outpasses for each role (history) -------------------------------------

@app.route("/outpasses/mentor/<int:mentor_id>", methods=["GET"])
def mentor_all_outpasses(mentor_id):
    """Mentor views all outpass history for their mentees."""
    mentor = db.session.get(Mentor, mentor_id)
    if not mentor:
        return jsonify({"error": "Mentor not found"}), 404

    outpasses = (
        Outpass.query
        .join(Student)
        .filter(Student.mentor_id == mentor_id)
        .order_by(Outpass.requested_departure.desc())
        .all()
    )
    return jsonify([_outpass_to_dict(op) for op in outpasses]), 200


@app.route("/outpasses/department/<department>", methods=["GET"])
def department_all_outpasses(department):
    """HOD views all outpass history for students in their department."""
    outpasses = (
        Outpass.query
        .join(Student)
        .filter(Student.department == department)
        .order_by(Outpass.requested_departure.desc())
        .all()
    )
    return jsonify([_outpass_to_dict(op) for op in outpasses]), 200


@app.route("/outpasses/hostel/<int:hostel_id>", methods=["GET"])
def hostel_all_outpasses(hostel_id):
    """Warden views all outpass history for their hostel."""
    hostel = db.session.get(Hostel, hostel_id)
    if not hostel:
        return jsonify({"error": "Hostel not found"}), 404

    outpasses = (
        Outpass.query
        .join(Student)
        .filter(Student.hostel_id == hostel_id)
        .order_by(Outpass.requested_departure.desc())
        .all()
    )
    return jsonify([_outpass_to_dict(op) for op in outpasses]), 200


# -- Approve / Reject (Multi-Level) -------------------------------------------

@app.route("/outpasses/<int:outpass_id>/approve", methods=["POST"])
def approve_outpass(outpass_id):
    """
    Multi-level approval:
      - Mentor approves -> sets mentor_approved = True
      - Warden approves -> sets warden_approved = True
      - HOD approves (only for > 7 days, after mentor+warden) -> sets hod_approved = True
      - Status becomes Approved ONLY when ALL required approvals are in.
      - Until then, status is PartiallyApproved.
    """
    outpass = db.session.get(Outpass, outpass_id)
    if not outpass:
        return jsonify({"error": "Outpass not found"}), 404

    if outpass.status == OutpassStatus.Rejected:
        return jsonify({"error": "Outpass has already been rejected"}), 409

    if outpass.status == OutpassStatus.Approved:
        return jsonify({"error": "Outpass is already fully approved"}), 409

    data = request.get_json(force=True)
    user_id = data.get("user_id")
    if not user_id:
        return jsonify({"error": "user_id is required"}), 400

    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    role = user.role
    remark = data.get("remark")

    # Check role is allowed to approve
    if role == UserRole.Mentor:
        if outpass.mentor_approved:
            return jsonify({"error": "Mentor has already approved this outpass"}), 409
        outpass.mentor_approved = True

    elif role == UserRole.Warden:
        if outpass.warden_approved:
            return jsonify({"error": "Warden has already approved this outpass"}), 409
        outpass.warden_approved = True

    elif role == UserRole.HOD:
        if not outpass.requires_hod:
            return jsonify({"error": "HOD approval is not required for leave <= 7 days"}), 400
        if not outpass.mentor_approved or not outpass.warden_approved:
            return jsonify({"error": "Mentor and Warden must approve before HOD"}), 400
        if outpass.hod_approved:
            return jsonify({"error": "HOD has already approved this outpass"}), 409
        outpass.hod_approved = True

    else:
        return jsonify({"error": f"Role '{role.value}' cannot approve outpasses"}), 403

    # Create approval record
    approval = Approval(
        outpass_id=outpass_id,
        approved_by=user_id,
        approver_role=role.value,
        decision=ApprovalDecision.Approved,
        remark=remark,
        decided_at=_now(),
    )
    db.session.add(approval)

    # Update outpass status
    if outpass.is_fully_approved:
        outpass.status = OutpassStatus.Approved
        if remark:
            outpass.remark = remark
    else:
        outpass.status = OutpassStatus.PartiallyApproved

    db.session.commit()

    return jsonify({
        "message": f"Outpass approved by {role.value}",
        "approval_id": approval.approval_id,
        "status": outpass.status.value,
        "mentor_approved": outpass.mentor_approved,
        "warden_approved": outpass.warden_approved,
        "hod_approved": outpass.hod_approved,
        "is_fully_approved": outpass.is_fully_approved,
    }), 200


@app.route("/outpasses/<int:outpass_id>/reject", methods=["POST"])
def reject_outpass(outpass_id):
    """Any approver (Mentor/Warden/HOD) can reject -- immediately sets status to Rejected."""
    outpass = db.session.get(Outpass, outpass_id)
    if not outpass:
        return jsonify({"error": "Outpass not found"}), 404

    if outpass.status == OutpassStatus.Rejected:
        return jsonify({"error": "Outpass is already rejected"}), 409

    if outpass.status == OutpassStatus.Approved:
        return jsonify({"error": "Cannot reject an already approved outpass"}), 409

    data = request.get_json(force=True)
    user_id = data.get("user_id")
    if not user_id:
        return jsonify({"error": "user_id is required"}), 400

    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    allowed_roles = {UserRole.Warden, UserRole.Mentor, UserRole.HOD}
    if user.role not in allowed_roles:
        return jsonify({"error": f"Role '{user.role.value}' cannot reject outpasses"}), 403

    outpass.status = OutpassStatus.Rejected
    remark = data.get("remark")
    if remark:
        outpass.remark = remark

    approval = Approval(
        outpass_id=outpass_id,
        approved_by=user_id,
        approver_role=user.role.value,
        decision=ApprovalDecision.Rejected,
        remark=remark,
        decided_at=_now(),
    )
    db.session.add(approval)
    db.session.commit()
    return jsonify({
        "message": "Outpass rejected",
        "approval_id": approval.approval_id,
    }), 200


# -- Gate Log ------------------------------------------------------------------

@app.route("/gatelog/<int:outpass_id>/exit", methods=["POST"])
def log_exit(outpass_id):
    """Security staff logs the actual exit time."""
    outpass = db.session.get(Outpass, outpass_id)
    if not outpass:
        return jsonify({"error": "Outpass not found"}), 404

    if outpass.status != OutpassStatus.Approved:
        return jsonify({
            "error": f"Cannot log exit -- outpass status is '{outpass.status.value}', must be 'Approved'"
        }), 403

    if outpass.gate_log:
        return jsonify({"error": "Exit already logged for this outpass"}), 409

    data = request.get_json(force=True)
    staff_id = data.get("staff_id")
    if not staff_id:
        return jsonify({"error": "staff_id is required"}), 400

    staff = db.session.get(SecurityStaff, staff_id)
    if not staff:
        return jsonify({"error": "Security staff not found"}), 404

    gate_log = GateLog(
        outpass_id=outpass_id,
        staff_id=staff_id,
        actual_exit_time=_now(),
    )
    db.session.add(gate_log)
    db.session.commit()
    return jsonify({
        "message": "Exit logged",
        "gatelog_id": gate_log.gatelog_id,
        "actual_exit_time": gate_log.actual_exit_time.isoformat(),
    }), 201


@app.route("/gatelog/<int:outpass_id>/return", methods=["POST"])
def log_return(outpass_id):
    """Security staff logs the actual return time (with 30-min anti-cheat gap)."""
    outpass = db.session.get(Outpass, outpass_id)
    if not outpass:
        return jsonify({"error": "Outpass not found"}), 404

    if not outpass.gate_log:
        return jsonify({"error": "No exit logged yet for this outpass"}), 404

    if outpass.gate_log.actual_return_time:
        return jsonify({"error": "Return already logged for this outpass"}), 409

    # Anti-cheat: minimum 30 minutes between exit and return
    exit_time = outpass.gate_log.actual_exit_time
    if exit_time:
        if exit_time.tzinfo is None:
            exit_time = exit_time.replace(tzinfo=timezone.utc)
        now = _now()
        elapsed = (now - exit_time).total_seconds() / 60
        if elapsed < MIN_RETURN_GAP_MINUTES:
            remaining = int(MIN_RETURN_GAP_MINUTES - elapsed)
            return jsonify({
                "error": f"Return cannot be logged within {MIN_RETURN_GAP_MINUTES} minutes of exit. "
                         f"Please wait {remaining} more minute(s)."
            }), 400

    data = request.get_json(force=True)
    staff_id = data.get("staff_id")
    if staff_id:
        staff = db.session.get(SecurityStaff, staff_id)
        if not staff:
            return jsonify({"error": "Security staff not found"}), 404
        outpass.gate_log.staff_id = staff_id

    outpass.gate_log.actual_return_time = _now()
    db.session.commit()
    return jsonify({
        "message": "Return logged",
        "actual_return_time": outpass.gate_log.actual_return_time.isoformat(),
    }), 200


# -- Reports -------------------------------------------------------------------

@app.route("/reports/overdue/<int:hostel_id>", methods=["GET"])
def overdue_report(hostel_id):
    """List currently overdue students for a hostel (computed live)."""
    hostel = db.session.get(Hostel, hostel_id)
    if not hostel:
        return jsonify({"error": "Hostel not found"}), 404

    now = _now()

    outpasses = (
        Outpass.query
        .join(Student)
        .join(GateLog)
        .filter(
            Student.hostel_id == hostel_id,
            Outpass.status == OutpassStatus.Approved,
            GateLog.actual_exit_time.isnot(None),
            GateLog.actual_return_time.is_(None),
        )
        .all()
    )

    overdue = []
    for op in outpasses:
        req_return = op.requested_return
        if req_return.tzinfo is None:
            req_return = req_return.replace(tzinfo=timezone.utc)
        if now > req_return:
            d = _outpass_to_dict(op)
            overdue_by = now - req_return
            d["overdue_by_minutes"] = int(overdue_by.total_seconds() / 60)
            overdue.append(d)

    return jsonify(overdue), 200


@app.route("/reports/overdue/mentor/<int:mentor_id>", methods=["GET"])
def mentor_overdue_report(mentor_id):
    """List currently overdue students for a mentor (computed live)."""
    mentor = db.session.get(Mentor, mentor_id)
    if not mentor:
        return jsonify({"error": "Mentor not found"}), 404

    now = _now()

    outpasses = (
        Outpass.query
        .join(Student)
        .join(GateLog)
        .filter(
            Student.mentor_id == mentor_id,
            Outpass.status == OutpassStatus.Approved,
            GateLog.actual_exit_time.isnot(None),
            GateLog.actual_return_time.is_(None),
        )
        .all()
    )

    overdue = []
    for op in outpasses:
        req_return = op.requested_return
        if req_return.tzinfo is None:
            req_return = req_return.replace(tzinfo=timezone.utc)
        if now > req_return:
            d = _outpass_to_dict(op)
            overdue_by = now - req_return
            d["overdue_by_minutes"] = int(overdue_by.total_seconds() / 60)
            overdue.append(d)

    return jsonify(overdue), 200


@app.route("/reports/overdue/department/<department>", methods=["GET"])
def department_overdue_report(department):
    """List currently overdue students for a department (computed live for HOD)."""
    now = _now()

    outpasses = (
        Outpass.query
        .join(Student)
        .join(GateLog)
        .filter(
            Student.department == department,
            Outpass.status == OutpassStatus.Approved,
            GateLog.actual_exit_time.isnot(None),
            GateLog.actual_return_time.is_(None),
        )
        .all()
    )

    overdue = []
    for op in outpasses:
        req_return = op.requested_return
        if req_return.tzinfo is None:
            req_return = req_return.replace(tzinfo=timezone.utc)
        if now > req_return:
            d = _outpass_to_dict(op)
            overdue_by = now - req_return
            d["overdue_by_minutes"] = int(overdue_by.total_seconds() / 60)
            overdue.append(d)

    return jsonify(overdue), 200


# -- Lookup data (for registration form dropdowns) ----------------------------

@app.route("/hostels", methods=["GET"])
def list_hostels():
    """Return all hostels with their rooms."""
    hostels = Hostel.query.all()
    result = []
    for h in hostels:
        result.append({
            "hostel_id": h.hostel_id,
            "hostel_name": h.hostel_name,
            "rooms": [
                {"room_id": r.room_id, "room_no": r.room_no}
                for r in h.rooms
            ],
        })
    return jsonify(result), 200


@app.route("/mentors", methods=["GET"])
def list_mentors():
    """Return all mentors."""
    mentors = Mentor.query.all()
    return jsonify([
        {
            "mentor_id": m.mentor_id,
            "name": m.user.name,
            "department": m.department,
        }
        for m in mentors
    ]), 200


# -- Admin: Register any staff / admin -----------------------------------------

@app.route("/admin/register-staff", methods=["POST"])
def admin_register_staff():
    """
    Admin endpoint: Register a new Warden, Mentor, HOD, Security Staff, or Admin.
    Only accessible by users with Admin role.
    """
    data = request.get_json(force=True)

    # Check that the caller is an Admin
    caller_user_id = data.get("caller_user_id")
    if not caller_user_id:
        return jsonify({"error": "caller_user_id is required"}), 400

    caller = db.session.get(User, caller_user_id)
    if not caller or caller.role != UserRole.Admin:
        return jsonify({"error": "Only Admins can register staff"}), 403

    required = ("name", "email", "password", "role")
    missing = [f for f in required if f not in data]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    target_role = data["role"]
    valid_roles = {"Warden", "Mentor", "HOD", "Security", "Admin"}
    if target_role not in valid_roles:
        return jsonify({"error": f"Invalid role. Must be one of: {', '.join(sorted(valid_roles))}"}), 400

    # Check if email already exists
    if User.query.filter_by(email=data["email"].strip().lower()).first():
        return jsonify({"error": "Email already registered"}), 409

    # Create User
    user = User(
        email=data["email"].strip().lower(),
        role=UserRole[target_role],
        name=data["name"],
    )
    user.set_password(data["password"])
    db.session.add(user)
    db.session.flush()

    result = {
        "message": f"{target_role} registered successfully",
        "user_id": user.user_id,
        "email": user.email,
        "role": target_role,
    }

    # Create role-specific record
    if target_role == "Warden":
        contact_no = data.get("contact_no", "")
        if not contact_no:
            return jsonify({"error": "contact_no is required for Warden"}), 400
        warden = Warden(
            user_id=user.user_id,
            name=data["name"],
            contact_no=contact_no,
        )
        db.session.add(warden)
        db.session.flush()

        # If hostel_id is provided, assign the warden to that hostel
        hostel_id = data.get("hostel_id")
        if hostel_id:
            hostel = db.session.get(Hostel, hostel_id)
            if hostel:
                hostel.warden_id = warden.warden_id
        result["warden_id"] = warden.warden_id

    elif target_role == "Mentor":
        department = data.get("department")
        if not department:
            return jsonify({"error": "department is required for Mentor"}), 400
        mentor = Mentor(
            user_id=user.user_id,
            department=department,
        )
        db.session.add(mentor)
        db.session.flush()
        result["mentor_id"] = mentor.mentor_id

    elif target_role == "HOD":
        department = data.get("department")
        if not department:
            return jsonify({"error": "department is required for HOD"}), 400
        hod = HOD(
            user_id=user.user_id,
            department=department,
        )
        db.session.add(hod)
        db.session.flush()
        result["hod_id"] = hod.hod_id

    elif target_role == "Security":
        shift = data.get("shift", "General")
        security = SecurityStaff(
            user_id=user.user_id,
            name=data["name"],
            shift=shift,
        )
        db.session.add(security)
        db.session.flush()
        result["staff_id"] = security.staff_id

    # Admin role doesn't need an extra table record

    db.session.commit()
    return jsonify(result), 201


# -- Seed & Debug Endpoints ----------------------------------------------------

@app.route("/debug-db", methods=["GET"])
def debug_db():
    """Check if database connection works."""
    import traceback
    uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
    # Mask password
    masked = uri
    try:
        at_idx = uri.index("@")
        colon_idx = uri.index(":", uri.index("://") + 3)
        masked = uri[:colon_idx+1] + "****" + uri[at_idx:]
    except (ValueError, IndexError):
        pass

    try:
        from sqlalchemy import text
        with db.engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return jsonify({"status": "connected", "uri": masked}), 200
    except Exception as e:
        return jsonify({"status": "failed", "uri": masked, "error": str(e), "traceback": traceback.format_exc()}), 500


@app.route("/seed-database", methods=["GET"])
def seed_database():
    """Seed the database with sample data using pre-computed password hashes.

    This avoids all CPU-intensive password hashing on the server.
    """
    import traceback
    from sqlalchemy import text, inspect

    # ---- Pre-computed password hashes (scrypt) ----
    HASHES = {
        "admin123":    "scrypt:32768:8:1$hSZwYc6c2H9nkZzw$c05a80d8fbc29a8a2301bc38c0bb3e5e04530fc309af141e434f650c66078a485dc86162d81df1c55ec86fc6a4bdd578d199a29cc69ad6e511c711fd5e422468",
        "warden123":   "scrypt:32768:8:1$g2oewxLIMbUBgO0d$e805a4a86adc607a3da060d44b83c64233c0a528b539ea00f1ae81fbc2faa7175ff4e623b2b405aaa1b9e51d4a3e07cac464db517f3a6e52824ceb7fc9435acf",
        "mentor123":   "scrypt:32768:8:1$7N3KngFDZYmFLM9q$d0314a332ba2671e58866901f146ea5ab66a793bd73dff4b99e2a2f737fd46fa9095454bce2f555769a86dc245646a420f02d7cb08c65e9835ba4759cf65d22f",
        "hod123":      "scrypt:32768:8:1$BJb9FpagZXQ4mrRF$a1741d2cda823a32eb9c36b1a37d33cfd689dfb01d9746440a3f38d88cd5ae02dcabedf22dff289601a490fdbd4e43ec510923767249409922c00f925748a364",
        "student123":  "scrypt:32768:8:1$GlBP0N5G3Cn6ChEf$b36fd64455c6e4e0e1533ce2fdd0c8f4189ee082005b98ceed12822a8cc1e5dcb29b5f6e09532054bf6acd1e62f7977145db05f468e46255f4a1b1c5ae23016a",
        "security123": "scrypt:32768:8:1$L9u8eHEH7q7wveSW$a98553c9e21c65e9472c665458bdcd182d1acba43cad3cfd5d0c166bdbcca9ecf798c562d34bdff2de0e404ec077e1f30a9a693817ee6cdb2ef95ab2f92f5842",
    }

    try:
        # Step 1: Create tables
        db.create_all()

        # Step 2: Check if already seeded (use a fresh connection)
        with db.engine.connect() as conn:
            result = conn.execute(text("SELECT count(*) FROM users"))
            count = result.scalar()
            if count > 0:
                return jsonify({"message": f"Database already has {count} users. Seed skipped."}), 200

        # Step 3: Inline seed — all in one transaction, NO password hashing
        # -------------------------------------------------------------------

        # Admin
        admin = User(email="admin@hostelout.com", role=UserRole.Admin, name="System Admin")
        admin.password_hash = HASHES["admin123"]
        db.session.add(admin)

        # Wardens (5 user accounts)
        warden_data = [
            ("ramesh.kumar@gmail.com",   "Dr. Ramesh Kumar",   "9876500001"),
            ("sunita.devi@gmail.com",    "Dr. Sunita Devi",    "9876500002"),
            ("manoj.borah@gmail.com",    "Dr. Manoj Borah",    "9876500003"),
            ("kalpana.nair@gmail.com",   "Dr. Kalpana Nair",   "9876500004"),
            ("debojit.sarmah@gmail.com", "Dr. Debojit Sarmah", "9876500005"),
        ]
        u_wardens = []
        for email, name, _ in warden_data:
            u = User(email=email, role=UserRole.Warden, name=name)
            u.password_hash = HASHES["warden123"]
            u_wardens.append(u)
            db.session.add(u)

        # Mentors (5)
        mentor_data = [
            ("ananya.sharma@gmail.com",  "Dr. Ananya Sharma",  "CSE"),
            ("vikram.singh@gmail.com",   "Dr. Vikram Singh",   "ECE"),
            ("priyanka.das@gmail.com",   "Dr. Priyanka Das",   "ME"),
            ("himanshu.medhi@gmail.com", "Dr. Himanshu Medhi", "CE"),
            ("rupali.baruah@gmail.com",  "Dr. Rupali Baruah",  "FET"),
        ]
        u_mentors = []
        for email, name, _ in mentor_data:
            u = User(email=email, role=UserRole.Mentor, name=name)
            u.password_hash = HASHES["mentor123"]
            u_mentors.append(u)
            db.session.add(u)

        # HODs (5)
        hod_data = [
            ("arvind.bordoloi@gmail.com", "Prof. Arvind Bordoloi", "CSE"),
            ("meena.patil@gmail.com",     "Prof. Meena Patil",     "ECE"),
            ("rajiv.gogoi@gmail.com",     "Prof. Rajiv Gogoi",     "ME"),
            ("tapan.seal@gmail.com",      "Prof. Tapan Seal",      "CE"),
            ("nibedita.deka@gmail.com",   "Prof. Nibedita Deka",   "FET"),
        ]
        u_hods = []
        for email, name, _ in hod_data:
            u = User(email=email, role=UserRole.HOD, name=name)
            u.password_hash = HASHES["hod123"]
            u_hods.append(u)
            db.session.add(u)

        # Students (32)
        student_info = [
            ("rahul.deka@gmail.com",        "Rahul Deka",        "2023CSE001", "9000000001", "CSE", "Hostel A"),
            ("priya.mahanta@gmail.com",     "Priya Mahanta",     "2023CSE002", "9000000002", "CSE", "Hostel B"),
            ("ankit.sarma@gmail.com",       "Ankit Sarma",       "2023CSE003", "9000000003", "CSE", "Hostel C"),
            ("neha.bora@gmail.com",         "Neha Bora",         "2023CSE004", "9000000004", "CSE", "Hostel D"),
            ("rohit.kalita@gmail.com",      "Rohit Kalita",      "2023CSE005", "9000000005", "CSE", "Hostel E"),
            ("sneha.choudhury@gmail.com",   "Sneha Choudhury",   "2023CSE006", "9000000006", "CSE", "Hostel A"),
            ("arjun.nath@gmail.com",        "Arjun Nath",        "2023CSE007", "9000000007", "CSE", "Hostel B"),
            ("amit.choudhury@gmail.com",    "Amit Choudhury",    "2023ECE001", "9000000008", "ECE", "Hostel C"),
            ("kavita.rani@gmail.com",       "Kavita Rani",       "2023ECE002", "9000000009", "ECE", "Hostel D"),
            ("deepak.nath@gmail.com",       "Deepak Nath",       "2023ECE003", "9000000010", "ECE", "Hostel E"),
            ("ritu.kalita@gmail.com",       "Ritu Kalita",       "2023ECE004", "9000000011", "ECE", "Hostel A"),
            ("sanjay.malakar@gmail.com",    "Sanjay Malakar",    "2023ECE005", "9000000012", "ECE", "Hostel B"),
            ("mrinmoy.dey@gmail.com",       "Mrinmoy Dey",       "2023ECE006", "9000000013", "ECE", "Hostel C"),
            ("pallabi.saikia@gmail.com",    "Pallabi Saikia",    "2023ECE007", "9000000014", "ECE", "Hostel D"),
            ("suraj.hazarika@gmail.com",    "Suraj Hazarika",    "2023ME001",  "9000000015", "ME",  "Hostel E"),
            ("pooja.das@gmail.com",         "Pooja Das",         "2023ME002",  "9000000016", "ME",  "Hostel A"),
            ("manish.baruah@gmail.com",     "Manish Baruah",     "2023ME003",  "9000000017", "ME",  "Hostel B"),
            ("ankita.phukan@gmail.com",     "Ankita Phukan",     "2023ME004",  "9000000018", "ME",  "Hostel C"),
            ("bikash.medhi@gmail.com",      "Bikash Medhi",      "2023ME005",  "9000000019", "ME",  "Hostel D"),
            ("jyoti.bhuyan@gmail.com",      "Jyoti Bhuyan",      "2023ME006",  "9000000020", "ME",  "Hostel E"),
            ("tapash.dutta@gmail.com",      "Tapash Dutta",      "2023CE001",  "9000000021", "CE",  "Hostel A"),
            ("monika.baishya@gmail.com",    "Monika Baishya",    "2023CE002",  "9000000022", "CE",  "Hostel B"),
            ("kunal.rajkhowa@gmail.com",    "Kunal Rajkhowa",    "2023CE003",  "9000000023", "CE",  "Hostel C"),
            ("pinkimoni.borah@gmail.com",   "Pinkimoni Borah",   "2023CE004",  "9000000024", "CE",  "Hostel D"),
            ("nabajit.deka@gmail.com",      "Nabajit Deka",      "2023CE005",  "9000000025", "CE",  "Hostel E"),
            ("barsha.kashyap@gmail.com",    "Barsha Kashyap",    "2023CE006",  "9000000026", "CE",  "Hostel A"),
            ("diganta.gogoi@gmail.com",     "Diganta Gogoi",     "2023FET001", "9000000027", "FET", "Hostel B"),
            ("mitali.sharma@gmail.com",     "Mitali Sharma",     "2023FET002", "9000000028", "FET", "Hostel C"),
            ("partha.bora@gmail.com",       "Partha Bora",       "2023FET003", "9000000029", "FET", "Hostel D"),
            ("anuradha.hazarika@gmail.com", "Anuradha Hazarika", "2023FET004", "9000000030", "FET", "Hostel E"),
            ("hemanta.talukdar@gmail.com",  "Hemanta Talukdar",  "2023FET005", "9000000031", "FET", "Hostel A"),
            ("kaberi.das@gmail.com",        "Kaberi Das",        "2023FET006", "9000000032", "FET", "Hostel B"),
        ]
        u_students = []
        for email, name, *_ in student_info:
            u = User(email=email, role=UserRole.Student, name=name)
            u.password_hash = HASHES["student123"]
            u_students.append(u)
            db.session.add(u)

        # Security (1)
        u_security = User(email="security.desk@gmail.com", role=UserRole.Security, name="Ramu Kalita")
        u_security.password_hash = HASHES["security123"]
        db.session.add(u_security)

        # Flush to get user_ids
        db.session.flush()

        # Mentor records
        mentors = []
        for u, (_, _, dept) in zip(u_mentors, mentor_data):
            m = Mentor(user_id=u.user_id, department=dept)
            mentors.append(m)
            db.session.add(m)
        db.session.flush()

        # HOD records
        for u, (_, _, dept) in zip(u_hods, hod_data):
            db.session.add(HOD(user_id=u.user_id, department=dept))
        db.session.flush()

        # Warden records
        wardens = []
        for u, (_, name, contact) in zip(u_wardens, warden_data):
            w = Warden(user_id=u.user_id, name=name, contact_no=contact)
            wardens.append(w)
            db.session.add(w)
        db.session.flush()

        # Hostels
        hostel_names = ["Hostel A", "Hostel B", "Hostel C", "Hostel D", "Hostel E"]
        hostel_objs = {}
        for hname, w in zip(hostel_names, wardens):
            h = Hostel(hostel_name=hname, warden_id=w.warden_id)
            hostel_objs[hname] = h
            db.session.add(h)
        db.session.flush()

        # Rooms (3 per hostel)
        prefix_map = {"Hostel A": "A", "Hostel B": "B", "Hostel C": "C", "Hostel D": "D", "Hostel E": "E"}
        rooms = {}
        for hname, hostel in hostel_objs.items():
            pfx = prefix_map[hname]
            for num in ["101", "102", "103"]:
                r = Room(hostel_id=hostel.hostel_id, room_no=f"{pfx}-{num}")
                rooms[f"{pfx}-{num}"] = r
                db.session.add(r)
        db.session.flush()

        # Mentor lookup by department
        mentor_map = {}
        for m, (_, _, dept) in zip(mentors, mentor_data):
            mentor_map[dept] = m

        # Student records
        room_nums = ["101", "102", "103"]
        for i, (email, name, roll_no, contact, dept, hostel_name) in enumerate(student_info):
            pfx = prefix_map[hostel_name]
            room_key = f"{pfx}-{room_nums[i % 3]}"
            s = Student(
                user_id=u_students[i].user_id,
                name=name,
                roll_no=roll_no,
                room_id=rooms[room_key].room_id,
                hostel_id=hostel_objs[hostel_name].hostel_id,
                contact_no=contact,
                mentor_id=mentor_map[dept].mentor_id,
                department=dept,
            )
            db.session.add(s)

        # Security staff record
        db.session.add(SecurityStaff(user_id=u_security.user_id, name="Ramu Kalita", shift="Day"))

        db.session.commit()
        return jsonify({"message": "Database seeded successfully!", "users": 49}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Seed failed: {str(e)}", "traceback": traceback.format_exc()}), 500


# -- Entrypoint ----------------------------------------------------------------

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000)
