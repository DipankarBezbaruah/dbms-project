"""HostelOut — Flask REST API for Digital Outpass & Leave Register."""

from datetime import datetime, timezone

from flask import Flask, request, jsonify
from flask_cors import CORS

from config import Config
from models import (
    db,
    Hostel,
    Warden,
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
    CORS(app)
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
            "warden_id": op.approval.warden_id,
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
    if op.status == OutpassStatus.Approved and op.gate_log:
        compare_time = op.gate_log.actual_return_time or _now()
        # Make requested_return offset-aware if it isn't already
        req_return = op.requested_return
        if req_return.tzinfo is None:
            req_return = req_return.replace(tzinfo=timezone.utc)
        if compare_time.tzinfo is None:
            compare_time = compare_time.replace(tzinfo=timezone.utc)
        d["is_overdue"] = compare_time > req_return
    else:
        d["is_overdue"] = False
    return d


# ── Routes ────────────────────────────────────────────────────────────────────

# ---- Students ----------------------------------------------------------------

@app.route("/students", methods=["POST"])
def create_student():
    """Create a new student (for seeding / testing)."""
    data = request.get_json(force=True)
    required = ("name", "roll_no", "room_id", "hostel_id", "contact_no")
    missing = [f for f in required if f not in data]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    student = Student(
        name=data["name"],
        roll_no=data["roll_no"],
        room_id=data["room_id"],
        hostel_id=data["hostel_id"],
        contact_no=data["contact_no"],
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


@app.route("/outpasses/<int:outpass_id>/approve", methods=["POST"])
def approve_outpass(outpass_id):
    """Warden approves an outpass (creates Approval record, updates status)."""
    outpass = db.session.get(Outpass, outpass_id)
    if not outpass:
        return jsonify({"error": "Outpass not found"}), 404

    # Business rule: cannot approve if already decided
    if outpass.approval:
        return jsonify({"error": "Outpass already has a decision"}), 409

    data = request.get_json(force=True)
    warden_id = data.get("warden_id")
    if not warden_id:
        return jsonify({"error": "warden_id is required"}), 400

    warden = db.session.get(Warden, warden_id)
    if not warden:
        return jsonify({"error": "Warden not found"}), 404

    outpass.status = OutpassStatus.Approved
    outpass.warden_remark = data.get("remark")

    approval = Approval(
        outpass_id=outpass_id,
        warden_id=warden_id,
        decision=ApprovalDecision.Approved,
        decided_at=_now(),
    )
    db.session.add(approval)
    db.session.commit()
    return jsonify({"message": "Outpass approved", "approval_id": approval.approval_id}), 200


@app.route("/outpasses/<int:outpass_id>/reject", methods=["POST"])
def reject_outpass(outpass_id):
    """Warden rejects an outpass (creates Approval record, updates status)."""
    outpass = db.session.get(Outpass, outpass_id)
    if not outpass:
        return jsonify({"error": "Outpass not found"}), 404

    if outpass.approval:
        return jsonify({"error": "Outpass already has a decision"}), 409

    data = request.get_json(force=True)
    warden_id = data.get("warden_id")
    if not warden_id:
        return jsonify({"error": "warden_id is required"}), 400

    warden = db.session.get(Warden, warden_id)
    if not warden:
        return jsonify({"error": "Warden not found"}), 404

    outpass.status = OutpassStatus.Rejected
    outpass.warden_remark = data.get("remark")

    approval = Approval(
        outpass_id=outpass_id,
        warden_id=warden_id,
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


# ── Entrypoint ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000)
