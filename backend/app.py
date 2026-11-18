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

    # Auto-create tables on startup (no shell needed)
    with app.app_context():
        db.create_all()

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


# -- Seed Endpoint (with full error handling) ----------------------------------

@app.route("/seed-database", methods=["GET"])
def seed_database():
    """Visit this URL in browser to populate the database with sample data."""
    import sys
    import subprocess
    import traceback

    try:
        # Check if already seeded
        count = User.query.count()
        if count > 0:
            return jsonify({"message": f"Database already has {count} users. Seed skipped."}), 200
    except Exception as e:
        return jsonify({"error": f"DB check failed: {str(e)}"}), 500

    try:
        result = subprocess.run(
            [sys.executable, "seed.py"],
            capture_output=True, text=True, timeout=120,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        if result.returncode == 0:
            return jsonify({
                "message": "Database seeded successfully!",
                "output": result.stdout[-1000:] if result.stdout else ""
            }), 200
        else:
            return jsonify({
                "error": "Seed script failed",
                "returncode": result.returncode,
                "stdout": result.stdout[-1000:] if result.stdout else "",
                "stderr": result.stderr[-1000:] if result.stderr else ""
            }), 500
    except Exception as e:
        return jsonify({
            "error": f"Exception: {str(e)}",
            "traceback": traceback.format_exc()
        }), 500


# -- Entrypoint ----------------------------------------------------------------

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000)
