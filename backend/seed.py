"""Seed the HostelOut database with sample data."""

from datetime import datetime, timedelta, timezone

from app import app
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


def seed():
    with app.app_context():
        # Drop and recreate all tables (clean slate)
        db.drop_all()
        db.create_all()

        # ── User accounts ────────────────────────────────────────────────

        user_student1 = User(
            email="rahul@tezu.ac.in", role=UserRole.Student, name="Rahul D."
        )
        user_student1.set_password("student123")

        user_student2 = User(
            email="priya@tezu.ac.in", role=UserRole.Student, name="Priya M."
        )
        user_student2.set_password("student123")

        user_student3 = User(
            email="ankit@tezu.ac.in", role=UserRole.Student, name="Ankit S."
        )
        user_student3.set_password("student123")

        user_mentor = User(
            email="mentor@tezu.ac.in", role=UserRole.Mentor, name="Dr. R. K. Das"
        )
        user_mentor.set_password("mentor123")

        user_warden = User(
            email="warden@tezu.ac.in", role=UserRole.Warden, name="Dr. A. K. Sharma"
        )
        user_warden.set_password("warden123")

        user_hod = User(
            email="hod@tezu.ac.in", role=UserRole.HOD, name="Prof. A. Bordoloi"
        )
        user_hod.set_password("hod123")

        user_security = User(
            email="security@tezu.ac.in", role=UserRole.Security, name="Ramu K."
        )
        user_security.set_password("security123")

        db.session.add_all([
            user_student1, user_student2, user_student3,
            user_mentor, user_warden, user_hod, user_security,
        ])
        db.session.flush()

        # ── Mentor ───────────────────────────────────────────────────────

        mentor = Mentor(
            user_id=user_mentor.user_id,
            department="CSE",
        )
        db.session.add(mentor)
        db.session.flush()

        # ── HOD ──────────────────────────────────────────────────────────

        hod = HOD(
            user_id=user_hod.user_id,
            department="CSE",
        )
        db.session.add(hod)
        db.session.flush()

        # ── Warden ───────────────────────────────────────────────────────

        warden = Warden(
            user_id=user_warden.user_id,
            name="Dr. A. K. Sharma",
            contact_no="9876543210",
        )
        db.session.add(warden)
        db.session.flush()

        # ── Hostel ───────────────────────────────────────────────────────

        hostel = Hostel(hostel_name="Bhaskar Hostel", warden_id=warden.warden_id)
        db.session.add(hostel)
        db.session.flush()

        # ── Rooms ────────────────────────────────────────────────────────

        room1 = Room(hostel_id=hostel.hostel_id, room_no="101")
        room2 = Room(hostel_id=hostel.hostel_id, room_no="102")
        db.session.add_all([room1, room2])
        db.session.flush()

        # ── Students ─────────────────────────────────────────────────────

        s1 = Student(
            user_id=user_student1.user_id,
            name="Rahul D.",
            roll_no="TU2023001",
            room_id=room1.room_id,
            hostel_id=hostel.hostel_id,
            contact_no="9000000001",
            mentor_id=mentor.mentor_id,
            department="CSE",
        )
        s2 = Student(
            user_id=user_student2.user_id,
            name="Priya M.",
            roll_no="TU2023002",
            room_id=room1.room_id,
            hostel_id=hostel.hostel_id,
            contact_no="9000000002",
            mentor_id=mentor.mentor_id,
            department="CSE",
        )
        s3 = Student(
            user_id=user_student3.user_id,
            name="Ankit S.",
            roll_no="TU2023003",
            room_id=room2.room_id,
            hostel_id=hostel.hostel_id,
            contact_no="9000000003",
            mentor_id=mentor.mentor_id,
            department="CSE",
        )
        db.session.add_all([s1, s2, s3])
        db.session.flush()

        # ── Security Staff ───────────────────────────────────────────────

        guard = SecurityStaff(
            user_id=user_security.user_id,
            name="Ramu K.",
            shift="Day",
        )
        db.session.add(guard)
        db.session.flush()

        now = datetime.now(timezone.utc)

        # ── Outpass 1: Pending ───────────────────────────────────────────

        op1 = Outpass(
            student_id=s1.student_id,
            reason="Family visit",
            destination="Guwahati",
            requested_departure=now + timedelta(days=1),
            requested_return=now + timedelta(days=2),
            status=OutpassStatus.Pending,
        )
        db.session.add(op1)

        # ── Outpass 2: Approved + exit logged (Rahul → Poruwa) ──────────

        op2 = Outpass(
            student_id=s1.student_id,
            reason="Market visit",
            destination="Poruwa",
            requested_departure=now - timedelta(hours=3),
            requested_return=now + timedelta(hours=3),
            status=OutpassStatus.Approved,
            warden_remark="Approved. Be back on time.",
        )
        db.session.add(op2)
        db.session.flush()

        approval2 = Approval(
            outpass_id=op2.outpass_id,
            approved_by=user_warden.user_id,
            approver_role="Warden",
            decision=ApprovalDecision.Approved,
            decided_at=now - timedelta(hours=3, minutes=30),
        )
        db.session.add(approval2)

        gate2 = GateLog(
            outpass_id=op2.outpass_id,
            staff_id=guard.staff_id,
            actual_exit_time=now - timedelta(hours=3),
        )
        db.session.add(gate2)

        # ── Outpass 3: Approved + exit logged + OVERDUE (Priya) ─────────

        op3 = Outpass(
            student_id=s2.student_id,
            reason="Medical checkup",
            destination="Tezpur Town",
            requested_departure=now - timedelta(hours=6),
            requested_return=now - timedelta(hours=2),  # 2 hours past due
            status=OutpassStatus.Approved,
            warden_remark="Take care.",
        )
        db.session.add(op3)
        db.session.flush()

        approval3 = Approval(
            outpass_id=op3.outpass_id,
            approved_by=user_warden.user_id,
            approver_role="Warden",
            decision=ApprovalDecision.Approved,
            decided_at=now - timedelta(hours=6, minutes=15),
        )
        db.session.add(approval3)

        gate3 = GateLog(
            outpass_id=op3.outpass_id,
            staff_id=guard.staff_id,
            actual_exit_time=now - timedelta(hours=6),
            # actual_return_time is NULL → still out → overdue
        )
        db.session.add(gate3)

        db.session.commit()

        print("[OK] Database seeded successfully!")
        print(f"   Hostel:   {hostel.hostel_name} (id={hostel.hostel_id})")
        print(f"   Warden:   {warden.name} (id={warden.warden_id})")
        print(f"   Mentor:   {mentor.user.name} (id={mentor.mentor_id}, dept={mentor.department})")
        print(f"   HOD:      {hod.user.name} (id={hod.hod_id}, dept={hod.department})")
        print(f"   Rooms:    {room1.room_no}, {room2.room_no}")
        print(f"   Students: {s1.name}, {s2.name}, {s3.name} (all mentored by {mentor.user.name})")
        print(f"   Guard:    {guard.name}")
        print(f"   Outpasses: 3 (Pending, Approved+Exit, Approved+Overdue)")
        print()
        print("   -- Login credentials --")
        print("   Student:  rahul@tezu.ac.in / student123")
        print("   Student:  priya@tezu.ac.in / student123")
        print("   Student:  ankit@tezu.ac.in / student123")
        print("   Mentor:   mentor@tezu.ac.in / mentor123")
        print("   Warden:   warden@tezu.ac.in / warden123")
        print("   HOD:      hod@tezu.ac.in / hod123")
        print("   Security: security@tezu.ac.in / security123")


if __name__ == "__main__":
    seed()
