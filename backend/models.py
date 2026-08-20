"""SQLAlchemy ORM models for HostelOut."""

from flask_sqlalchemy import SQLAlchemy
import enum

db = SQLAlchemy()


# ── Enum types ────────────────────────────────────────────────────────────────

class OutpassStatus(enum.Enum):
    Pending = "Pending"
    Approved = "Approved"
    Rejected = "Rejected"


class ApprovalDecision(enum.Enum):
    Approved = "Approved"
    Rejected = "Rejected"


# ── Models ────────────────────────────────────────────────────────────────────

class Warden(db.Model):
    __tablename__ = "wardens"

    warden_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(120), nullable=False)
    contact_no = db.Column(db.String(20), nullable=False)

    # Relationships
    hostels = db.relationship("Hostel", back_populates="warden")
    approvals = db.relationship("Approval", back_populates="warden")


class Hostel(db.Model):
    __tablename__ = "hostels"

    hostel_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    hostel_name = db.Column(db.String(120), nullable=False)
    warden_id = db.Column(
        db.Integer, db.ForeignKey("wardens.warden_id"), nullable=False
    )

    # Relationships
    warden = db.relationship("Warden", back_populates="hostels")
    rooms = db.relationship("Room", back_populates="hostel")
    students = db.relationship("Student", back_populates="hostel")


class Room(db.Model):
    __tablename__ = "rooms"

    room_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    hostel_id = db.Column(
        db.Integer, db.ForeignKey("hostels.hostel_id"), nullable=False
    )
    room_no = db.Column(db.String(20), nullable=False)

    # Relationships
    hostel = db.relationship("Hostel", back_populates="rooms")
    students = db.relationship("Student", back_populates="room")


class Student(db.Model):
    __tablename__ = "students"

    student_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(120), nullable=False)
    roll_no = db.Column(db.String(30), unique=True, nullable=False)
    room_id = db.Column(
        db.Integer, db.ForeignKey("rooms.room_id"), nullable=False
    )
    hostel_id = db.Column(
        db.Integer, db.ForeignKey("hostels.hostel_id"), nullable=False
    )
    contact_no = db.Column(db.String(20), nullable=False)

    # Relationships
    room = db.relationship("Room", back_populates="students")
    hostel = db.relationship("Hostel", back_populates="students")
    outpasses = db.relationship("Outpass", back_populates="student")


class SecurityStaff(db.Model):
    __tablename__ = "security_staff"

    staff_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(120), nullable=False)
    shift = db.Column(db.String(30), nullable=False)

    # Relationships
    gate_logs = db.relationship("GateLog", back_populates="staff")


class Outpass(db.Model):
    __tablename__ = "outpasses"

    outpass_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_id = db.Column(
        db.Integer, db.ForeignKey("students.student_id"), nullable=False
    )
    reason = db.Column(db.Text, nullable=False)
    destination = db.Column(db.String(200), nullable=False)
    requested_departure = db.Column(db.DateTime, nullable=False)
    requested_return = db.Column(db.DateTime, nullable=False)
    status = db.Column(
        db.Enum(OutpassStatus), nullable=False, default=OutpassStatus.Pending
    )
    warden_remark = db.Column(db.Text, nullable=True)

    # Relationships
    student = db.relationship("Student", back_populates="outpasses")
    approval = db.relationship(
        "Approval", back_populates="outpass", uselist=False
    )
    gate_log = db.relationship(
        "GateLog", back_populates="outpass", uselist=False
    )


class Approval(db.Model):
    __tablename__ = "approvals"

    approval_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    outpass_id = db.Column(
        db.Integer,
        db.ForeignKey("outpasses.outpass_id"),
        unique=True,  # one-to-one
        nullable=False,
    )
    warden_id = db.Column(
        db.Integer, db.ForeignKey("wardens.warden_id"), nullable=False
    )
    decision = db.Column(db.Enum(ApprovalDecision), nullable=False)
    decided_at = db.Column(db.DateTime, nullable=False)

    # Relationships
    outpass = db.relationship("Outpass", back_populates="approval")
    warden = db.relationship("Warden", back_populates="approvals")


class GateLog(db.Model):
    __tablename__ = "gate_log"

    gatelog_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    outpass_id = db.Column(
        db.Integer,
        db.ForeignKey("outpasses.outpass_id"),
        unique=True,  # one-to-one
        nullable=False,
    )
    staff_id = db.Column(
        db.Integer, db.ForeignKey("security_staff.staff_id"), nullable=False
    )
    actual_exit_time = db.Column(db.DateTime, nullable=True)
    actual_return_time = db.Column(db.DateTime, nullable=True)

    # Relationships
    outpass = db.relationship("Outpass", back_populates="gate_log")
    staff = db.relationship("SecurityStaff", back_populates="gate_logs")
