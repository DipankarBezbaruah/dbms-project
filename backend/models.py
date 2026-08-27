"""SQLAlchemy ORM models for HostelOut."""

from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import enum

db = SQLAlchemy()


# ── Enum types ────────────────────────────────────────────────────────────────

class UserRole(enum.Enum):
    Student = "Student"
    Mentor = "Mentor"
    Warden = "Warden"
    HOD = "HOD"
    Security = "Security"


class OutpassStatus(enum.Enum):
    Pending = "Pending"
    Approved = "Approved"
    Rejected = "Rejected"


class ApprovalDecision(enum.Enum):
    Approved = "Approved"
    Rejected = "Rejected"


# ── Models ────────────────────────────────────────────────────────────────────

class User(db.Model):
    """Unified login table — every person who signs in has exactly one row here."""
    __tablename__ = "users"

    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.Enum(UserRole), nullable=False)
    name = db.Column(db.String(120), nullable=False)

    # One-to-one back-references (set by the child tables)
    student = db.relationship("Student", back_populates="user", uselist=False)
    warden = db.relationship("Warden", back_populates="user", uselist=False)
    mentor = db.relationship("Mentor", back_populates="user", uselist=False)
    hod = db.relationship("HOD", back_populates="user", uselist=False)
    security_staff = db.relationship("SecurityStaff", back_populates="user", uselist=False)

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)


class Mentor(db.Model):
    """A faculty member who mentors a group of students."""
    __tablename__ = "mentors"

    mentor_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.user_id"), unique=True, nullable=False
    )
    department = db.Column(db.String(100), nullable=False)

    # Relationships
    user = db.relationship("User", back_populates="mentor")
    students = db.relationship("Student", back_populates="mentor")


class HOD(db.Model):
    """Head of Department — has oversight over all students in their department."""
    __tablename__ = "hods"

    hod_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.user_id"), unique=True, nullable=False
    )
    department = db.Column(db.String(100), nullable=False)

    # Relationships
    user = db.relationship("User", back_populates="hod")


class Warden(db.Model):
    __tablename__ = "wardens"

    warden_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.user_id"), unique=True, nullable=False
    )
    name = db.Column(db.String(120), nullable=False)
    contact_no = db.Column(db.String(20), nullable=False)

    # Relationships
    user = db.relationship("User", back_populates="warden")
    hostels = db.relationship("Hostel", back_populates="warden")


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
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.user_id"), unique=True, nullable=False
    )
    name = db.Column(db.String(120), nullable=False)
    roll_no = db.Column(db.String(30), unique=True, nullable=False)
    room_id = db.Column(
        db.Integer, db.ForeignKey("rooms.room_id"), nullable=False
    )
    hostel_id = db.Column(
        db.Integer, db.ForeignKey("hostels.hostel_id"), nullable=False
    )
    contact_no = db.Column(db.String(20), nullable=False)
    mentor_id = db.Column(
        db.Integer, db.ForeignKey("mentors.mentor_id"), nullable=True
    )
    department = db.Column(db.String(100), nullable=True)

    # Relationships
    user = db.relationship("User", back_populates="student")
    room = db.relationship("Room", back_populates="students")
    hostel = db.relationship("Hostel", back_populates="students")
    mentor = db.relationship("Mentor", back_populates="students")
    outpasses = db.relationship("Outpass", back_populates="student")


class SecurityStaff(db.Model):
    __tablename__ = "security_staff"

    staff_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.user_id"), unique=True, nullable=False
    )
    name = db.Column(db.String(120), nullable=False)
    shift = db.Column(db.String(30), nullable=False)

    # Relationships
    user = db.relationship("User", back_populates="security_staff")
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
    approved_by = db.Column(
        db.Integer, db.ForeignKey("users.user_id"), nullable=False
    )
    approver_role = db.Column(db.String(30), nullable=False)  # e.g. "Warden", "Mentor", "HOD"
    decision = db.Column(db.Enum(ApprovalDecision), nullable=False)
    decided_at = db.Column(db.DateTime, nullable=False)

    # Relationships
    outpass = db.relationship("Outpass", back_populates="approval")
    approver = db.relationship("User")


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
