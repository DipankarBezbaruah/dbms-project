"""Seed the HostelOut database with sample data."""

from datetime import datetime, timedelta, timezone

from app import app
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


def seed():
    with app.app_context():
        # Drop and recreate all tables (clean slate)
        db.drop_all()
        db.create_all()

        # ── Warden ────────────────────────────────────────────────────────
        warden = Warden(name="Dr. A. K. Sharma", contact_no="9876543210")
        db.session.add(warden)
        db.session.flush()  # get warden_id

        # ── Hostel ────────────────────────────────────────────────────────
        hostel = Hostel(hostel_name="Bhaskar Hostel", warden_id=warden.warden_id)
        db.session.add(hostel)
        db.session.flush()

        # ── Rooms ─────────────────────────────────────────────────────────
        room1 = Room(hostel_id=hostel.hostel_id, room_no="101")
        room2 = Room(hostel_id=hostel.hostel_id, room_no="102")
        db.session.add_all([room1, room2])
        db.session.flush()

        # ── Students ──────────────────────────────────────────────────────
        s1 = Student(
            name="Rahul D.",
            roll_no="TU2023001",
            room_id=room1.room_id,
            hostel_id=hostel.hostel_id,
            contact_no="9000000001",
        )
        s2 = Student(
            name="Priya M.",
            roll_no="TU2023002",
            room_id=room1.room_id,
            hostel_id=hostel.hostel_id,
            contact_no="9000000002",
        )
        s3 = Student(
            name="Ankit S.",
            roll_no="TU2023003",
            room_id=room2.room_id,
            hostel_id=hostel.hostel_id,
            contact_no="9000000003",
        )
        db.session.add_all([s1, s2, s3])
        db.session.flush()

        # ── Security Staff ────────────────────────────────────────────────
        guard = SecurityStaff(name="Ramu K.", shift="Day")
        db.session.add(guard)
        db.session.flush()

        now = datetime.now(timezone.utc)

        # ── Outpass 1: Pending ────────────────────────────────────────────
        op1 = Outpass(
            student_id=s1.student_id,
            reason="Family visit",
            destination="Guwahati",
            requested_departure=now + timedelta(days=1),
            requested_return=now + timedelta(days=2),
            status=OutpassStatus.Pending,
        )
        db.session.add(op1)

        # ── Outpass 2: Approved + exit logged (Rahul → Poruwa) ───────────
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
            warden_id=warden.warden_id,
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

        # ── Outpass 3: Approved + exit logged + OVERDUE (Priya) ──────────
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
            warden_id=warden.warden_id,
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
        print(f"   Rooms:    {room1.room_no}, {room2.room_no}")
        print(f"   Students: {s1.name}, {s2.name}, {s3.name}")
        print(f"   Guard:    {guard.name}")
        print(f"   Outpasses: 3 (Pending, Approved+Exit, Approved+Overdue)")


if __name__ == "__main__":
    seed()
