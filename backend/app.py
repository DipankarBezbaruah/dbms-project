"""HostelOut — Flask REST API for Digital Outpass & Leave Register."""

from datetime import datetime, timezone

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
    db.init_app(app)
    CORS(app, supports_credentials=True)
    return app


app = create_app()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _now():
    """Return the current UTC time."""
    return datetime.now(timezone.utc)


def _outpass_to_dict(op: Outpass) -> dict:
    """Serialize an Outpass (and nested approval / gate_log) to a dict."""
    d = {
        "outpass_id": op.outpass_id,
        "student_id": op.student_id,
        "student_name": op.student.name,
        "roll_no": op.student.roll_no,
        "reason": op.reason,
        "destination": op.destination,
        "requested_departure": op.requested_departure.isoformat(),
        "requested_return": op.requested_return.isoformat(),
        "status": op.status.value,
        "warden_remark": op.warden_remark,
    }
    if op.approval:
        d["approval"] = {
            "approval_id": op.approval.approval_id,
            "approved_by": op.approval.approved_by,
            "approver_name": op.approval.approver.name if op.approval.approver else None,
            "approver_role": op.approval.approver_role,
            "decision": op.approval.decision.value,
            "decided_at": op.approval.decided_at.isoformat(),
        }
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
        # Make requested_return offset-aware if it isn't already
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
        payload["room_no"] = s.room.room_no if s.room else None
        payload["mentor_id"] = s.mentor_id
        payload["department"] = s.department
    elif user.role == UserRole.Warden and user.warden:
        w = user.warden
        payload["warden_id"] = w.warden_id
        payload["contact_no"] = w.contact_no
        # Include all hostels this warden manages
        payload["hostels"] = [
            {"hostel_id": h.hostel_id, "hostel_name": h.hostel_name}
            for h in w.hostels
        ]
        # Convenience: primary hostel (first one)
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


# ── Auth Routes ───────────────────────────────────────────────────────────────

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

    # Store user_id in session
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


# ── Routes ────────────────────────────────────────────────────────────────────

# ---- Students ----------------------------------------------------------------

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


# ---- Outpasses ---------------------------------------------------------------

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

    outpass = Outpass(
        student_id=data["student_id"],
        reason=data["reason"],
        destination=data["destination"],
        requested_departure=datetime.fromisoformat(data["requested_departure"]),
        requested_return=datetime.fromisoformat(data["requested_return"]),
        status=OutpassStatus.Pending,
    )
    db.session.add(outpass)
    db.session.commit()
    return jsonify({
        "message": "Outpass request created",
        "outpass_id": outpass.outpass_id,
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


@app.route("/outpasses/pending/<int:hostel_id>", methods=["GET"])
def pending_outpasses(hostel_id):
    """Warden views pending outpass requests for their hostel."""
    hostel = db.session.get(Hostel, hostel_id)
    if not hostel:
        return jsonify({"error": "Hostel not found"}), 404

    outpasses = (
        Outpass.query
        .join(Student)
        .filter(
            Student.hostel_id == hostel_id,
            Outpass.status == OutpassStatus.Pending,
        )
        .order_by(Outpass.requested_departure.asc())
        .all()
    )
    return jsonify([_outpass_to_dict(op) for op in outpasses]), 200


@app.route("/outpasses/pending/mentor/<int:mentor_id>", methods=["GET"])
def mentor_pending_outpasses(mentor_id):
    """Mentor views pending outpass requests from their mentees only."""
    mentor = db.session.get(Mentor, mentor_id)
    if not mentor:
        return jsonify({"error": "Mentor not found"}), 404

    outpasses = (
        Outpass.query
        .join(Student)
        .filter(
            Student.mentor_id == mentor_id,
            Outpass.status == OutpassStatus.Pending,
        )
        .order_by(Outpass.requested_departure.asc())
        .all()
    )
    return jsonify([_outpass_to_dict(op) for op in outpasses]), 200


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


@app.route("/outpasses/pending/department/<department>", methods=["GET"])
def department_pending_outpasses(department):
    """HOD views pending outpass requests from all students in their department."""
    outpasses = (
        Outpass.query
        .join(Student)
        .filter(
            Student.department == department,
            Outpass.status == OutpassStatus.Pending,
        )
        .order_by(Outpass.requested_departure.asc())
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


@app.route("/outpasses/<int:outpass_id>/approve", methods=["POST"])
def approve_outpass(outpass_id):
    """Warden, Mentor, or HOD approves an outpass."""
    outpass = db.session.get(Outpass, outpass_id)
    if not outpass:
        return jsonify({"error": "Outpass not found"}), 404

    if outpass.approval:
        return jsonify({"error": "Outpass already has a decision"}), 409

    data = request.get_json(force=True)
    user_id = data.get("user_id")
    if not user_id:
        return jsonify({"error": "user_id is required"}), 400

    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    allowed_roles = {UserRole.Warden, UserRole.Mentor, UserRole.HOD}
    if user.role not in allowed_roles:
        return jsonify({"error": f"Role '{user.role.value}' is not authorized to approve outpasses"}), 403

    outpass.status = OutpassStatus.Approved
    outpass.warden_remark = data.get("remark")

    approval = Approval(
        outpass_id=outpass_id,
        approved_by=user_id,
        approver_role=user.role.value,
        decision=ApprovalDecision.Approved,
        decided_at=_now(),
    )
    db.session.add(approval)
    db.session.commit()
    return jsonify({"message": "Outpass approved", "approval_id": approval.approval_id}), 200


@app.route("/outpasses/<int:outpass_id>/reject", methods=["POST"])
def reject_outpass(outpass_id):
    """Warden, Mentor, or HOD rejects an outpass."""
    outpass = db.session.get(Outpass, outpass_id)
    if not outpass:
        return jsonify({"error": "Outpass not found"}), 404

    if outpass.approval:
        return jsonify({"error": "Outpass already has a decision"}), 409

    data = request.get_json(force=True)
    user_id = data.get("user_id")
    if not user_id:
        return jsonify({"error": "user_id is required"}), 400

    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    allowed_roles = {UserRole.Warden, UserRole.Mentor, UserRole.HOD}
    if user.role not in allowed_roles:
        return jsonify({"error": f"Role '{user.role.value}' is not authorized to reject outpasses"}), 403

    outpass.status = OutpassStatus.Rejected
    outpass.warden_remark = data.get("remark")

    approval = Approval(
        outpass_id=outpass_id,
        approved_by=user_id,
        approver_role=user.role.value,
        decision=ApprovalDecision.Rejected,
        decided_at=_now(),
    )
    db.session.add(approval)
    db.session.commit()
    return jsonify({"message": "Outpass rejected", "approval_id": approval.approval_id}), 200


# ---- Gate Log ----------------------------------------------------------------

@app.route("/gatelog/<int:outpass_id>/exit", methods=["POST"])
def log_exit(outpass_id):
    """Security staff logs the actual exit time."""
    outpass = db.session.get(Outpass, outpass_id)
    if not outpass:
        return jsonify({"error": "Outpass not found"}), 404

    # Business rule: only Approved outpasses can have a gate log
    if outpass.status != OutpassStatus.Approved:
        return jsonify({
            "error": f"Cannot log exit — outpass status is '{outpass.status.value}', must be 'Approved'"
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
    """Security staff logs the actual return time."""
    outpass = db.session.get(Outpass, outpass_id)
    if not outpass:
        return jsonify({"error": "Outpass not found"}), 404

    if not outpass.gate_log:
        return jsonify({"error": "No exit logged yet for this outpass"}), 404

    if outpass.gate_log.actual_return_time:
        return jsonify({"error": "Return already logged for this outpass"}), 409

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


# ---- Reports -----------------------------------------------------------------

@app.route("/reports/overdue/<int:hostel_id>", methods=["GET"])
def overdue_report(hostel_id):
    """List currently overdue students for a hostel (computed live)."""
    hostel = db.session.get(Hostel, hostel_id)
    if not hostel:
        return jsonify({"error": "Hostel not found"}), 404

    now = _now()

    # Approved outpasses for this hostel that have a gate log with an exit
    outpasses = (
        Outpass.query
        .join(Student)
        .join(GateLog)
        .filter(
            Student.hostel_id == hostel_id,
            Outpass.status == OutpassStatus.Approved,
            GateLog.actual_exit_time.isnot(None),
            GateLog.actual_return_time.is_(None),  # still out
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
            GateLog.actual_return_time.is_(None),  # still out
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
            GateLog.actual_return_time.is_(None),  # still out
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


# ── Entrypoint ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000)
