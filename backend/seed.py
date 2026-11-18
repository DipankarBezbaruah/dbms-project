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
        # Skip if database already has data (prevents re-seeding on every deploy)
        try:
            if User.query.first() is not None:
                print("[SKIP] Database already has data. Seed skipped.")
                return
        except Exception:
            pass  # Table might not exist yet, continue to create

        # Drop all tables and enum types properly for PostgreSQL
        from sqlalchemy import text
        try:
            db.drop_all()
            # PostgreSQL keeps enum types after drop_all — remove them manually
            for enum_name in ['userrole', 'outpassstatus', 'approvaldecision']:
                db.session.execute(text(f"DROP TYPE IF EXISTS {enum_name} CASCADE"))
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"[WARN] Drop cleanup: {e}")

        db.create_all()
        print("[OK] Tables created successfully.")

        now = datetime.now(timezone.utc)

        # ==============================================================
        #  SYSTEM ADMIN (first admin -- can create all other users)
        # ==============================================================
        admin_user = User(
            email="admin@hostelout.com",
            role=UserRole.Admin,
            name="System Admin",
        )
        admin_user.set_password("admin123")
        db.session.add(admin_user)

        # ==============================================================
        #  USER ACCOUNTS
        # ==============================================================

        # -- Wardens (5) -----------------------------------------------
        warden_data = [
            ("ramesh.kumar@gmail.com",    "Dr. Ramesh Kumar",    "9876500001"),
            ("sunita.devi@gmail.com",     "Dr. Sunita Devi",     "9876500002"),
            ("manoj.borah@gmail.com",     "Dr. Manoj Borah",     "9876500003"),
            ("kalpana.nair@gmail.com",    "Dr. Kalpana Nair",    "9876500004"),
            ("debojit.sarmah@gmail.com",  "Dr. Debojit Sarmah",  "9876500005"),
        ]
        u_wardens = []
        for email, name, _ in warden_data:
            u = User(email=email, role=UserRole.Warden, name=name)
            u.set_password("warden123")
            u_wardens.append(u)

        # -- Mentors (5 -- one per department) -------------------------
        mentor_data = [
            ("ananya.sharma@gmail.com",   "Dr. Ananya Sharma",   "CSE"),
            ("vikram.singh@gmail.com",    "Dr. Vikram Singh",    "ECE"),
            ("priyanka.das@gmail.com",    "Dr. Priyanka Das",    "ME"),
            ("himanshu.medhi@gmail.com",  "Dr. Himanshu Medhi",  "CE"),
            ("rupali.baruah@gmail.com",   "Dr. Rupali Baruah",   "FET"),
        ]
        u_mentors = []
        for email, name, _ in mentor_data:
            u = User(email=email, role=UserRole.Mentor, name=name)
            u.set_password("mentor123")
            u_mentors.append(u)

        # -- HODs (5 -- one per department) ----------------------------
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
            u.set_password("hod123")
            u_hods.append(u)

        # -- Students (32) ---------------------------------------------
        student_data = [
            # (email, name, roll_no, contact, department, hostel_name)
            # --- CSE (7 students) ---
            ("rahul.deka@gmail.com",        "Rahul Deka",        "2023CSE001", "9000000001", "CSE", "Hostel A"),
            ("priya.mahanta@gmail.com",     "Priya Mahanta",     "2023CSE002", "9000000002", "CSE", "Hostel B"),
            ("ankit.sarma@gmail.com",       "Ankit Sarma",       "2023CSE003", "9000000003", "CSE", "Hostel C"),
            ("neha.bora@gmail.com",         "Neha Bora",         "2023CSE004", "9000000004", "CSE", "Hostel D"),
            ("rohit.kalita@gmail.com",      "Rohit Kalita",      "2023CSE005", "9000000005", "CSE", "Hostel E"),
            ("sneha.choudhury@gmail.com",   "Sneha Choudhury",   "2023CSE006", "9000000006", "CSE", "Hostel A"),
            ("arjun.nath@gmail.com",        "Arjun Nath",        "2023CSE007", "9000000007", "CSE", "Hostel B"),
            # --- ECE (7 students) ---
            ("amit.choudhury@gmail.com",    "Amit Choudhury",    "2023ECE001", "9000000008", "ECE", "Hostel C"),
            ("kavita.rani@gmail.com",       "Kavita Rani",       "2023ECE002", "9000000009", "ECE", "Hostel D"),
            ("deepak.nath@gmail.com",       "Deepak Nath",       "2023ECE003", "9000000010", "ECE", "Hostel E"),
            ("ritu.kalita@gmail.com",       "Ritu Kalita",       "2023ECE004", "9000000011", "ECE", "Hostel A"),
            ("sanjay.malakar@gmail.com",    "Sanjay Malakar",    "2023ECE005", "9000000012", "ECE", "Hostel B"),
            ("mrinmoy.dey@gmail.com",       "Mrinmoy Dey",       "2023ECE006", "9000000013", "ECE", "Hostel C"),
            ("pallabi.saikia@gmail.com",    "Pallabi Saikia",    "2023ECE007", "9000000014", "ECE", "Hostel D"),
            # --- ME (6 students) ---
            ("suraj.hazarika@gmail.com",    "Suraj Hazarika",    "2023ME001",  "9000000015", "ME",  "Hostel E"),
            ("pooja.das@gmail.com",         "Pooja Das",         "2023ME002",  "9000000016", "ME",  "Hostel A"),
            ("manish.baruah@gmail.com",     "Manish Baruah",     "2023ME003",  "9000000017", "ME",  "Hostel B"),
            ("ankita.phukan@gmail.com",     "Ankita Phukan",     "2023ME004",  "9000000018", "ME",  "Hostel C"),
            ("bikash.medhi@gmail.com",      "Bikash Medhi",      "2023ME005",  "9000000019", "ME",  "Hostel D"),
            ("jyoti.bhuyan@gmail.com",      "Jyoti Bhuyan",      "2023ME006",  "9000000020", "ME",  "Hostel E"),
            # --- CE (6 students) ---
            ("tapash.dutta@gmail.com",      "Tapash Dutta",      "2023CE001",  "9000000021", "CE",  "Hostel A"),
            ("monika.baishya@gmail.com",    "Monika Baishya",    "2023CE002",  "9000000022", "CE",  "Hostel B"),
            ("kunal.rajkhowa@gmail.com",    "Kunal Rajkhowa",    "2023CE003",  "9000000023", "CE",  "Hostel C"),
            ("pinkimoni.borah@gmail.com",   "Pinkimoni Borah",   "2023CE004",  "9000000024", "CE",  "Hostel D"),
            ("nabajit.deka@gmail.com",      "Nabajit Deka",      "2023CE005",  "9000000025", "CE",  "Hostel E"),
            ("barsha.kashyap@gmail.com",    "Barsha Kashyap",    "2023CE006",  "9000000026", "CE",  "Hostel A"),
            # --- FET (6 students) ---
            ("diganta.gogoi@gmail.com",     "Diganta Gogoi",     "2023FET001", "9000000027", "FET", "Hostel B"),
            ("mitali.sharma@gmail.com",     "Mitali Sharma",     "2023FET002", "9000000028", "FET", "Hostel C"),
            ("partha.bora@gmail.com",       "Partha Bora",       "2023FET003", "9000000029", "FET", "Hostel D"),
            ("anuradha.hazarika@gmail.com", "Anuradha Hazarika", "2023FET004", "9000000030", "FET", "Hostel E"),
            ("hemanta.talukdar@gmail.com",  "Hemanta Talukdar",  "2023FET005", "9000000031", "FET", "Hostel A"),
            ("kaberi.das@gmail.com",        "Kaberi Das",        "2023FET006", "9000000032", "FET", "Hostel B"),
        ]

        u_students = []
        for email, name, *_ in student_data:
            u = User(email=email, role=UserRole.Student, name=name)
            u.set_password("student123")
            u_students.append(u)

        # -- Security (1) ----------------------------------------------
        u_security = User(email="security.desk@gmail.com", role=UserRole.Security, name="Ramu Kalita")
        u_security.set_password("security123")

        # Flush all users
        all_users = [*u_wardens, *u_mentors, *u_hods, *u_students, u_security]
        db.session.add_all(all_users)
        db.session.flush()

        # ==============================================================
        #  MENTORS (linked to user accounts)
        # ==============================================================
        mentors = []
        for u, (_, _, dept) in zip(u_mentors, mentor_data):
            m = Mentor(user_id=u.user_id, department=dept)
            mentors.append(m)
        db.session.add_all(mentors)
        db.session.flush()
        mentor_cse, mentor_ece, mentor_me, mentor_ce, mentor_fet = mentors

        # ==============================================================
        #  HODs (linked to user accounts)
        # ==============================================================
        hods = []
        for u, (_, _, dept) in zip(u_hods, hod_data):
            h = HOD(user_id=u.user_id, department=dept)
            hods.append(h)
        db.session.add_all(hods)
        db.session.flush()

        # ==============================================================
        #  WARDENS (linked to user accounts)
        # ==============================================================
        wardens = []
        for u, (_, name, contact) in zip(u_wardens, warden_data):
            w = Warden(user_id=u.user_id, name=name, contact_no=contact)
            wardens.append(w)
        db.session.add_all(wardens)
        db.session.flush()
        warden_a, warden_b, warden_c, warden_d, warden_e = wardens

        # ==============================================================
        #  HOSTELS (5)
        # ==============================================================
        hostel_a = Hostel(hostel_name="Hostel A", warden_id=warden_a.warden_id)
        hostel_b = Hostel(hostel_name="Hostel B", warden_id=warden_b.warden_id)
        hostel_c = Hostel(hostel_name="Hostel C", warden_id=warden_c.warden_id)
        hostel_d = Hostel(hostel_name="Hostel D", warden_id=warden_d.warden_id)
        hostel_e = Hostel(hostel_name="Hostel E", warden_id=warden_e.warden_id)
        hostels = [hostel_a, hostel_b, hostel_c, hostel_d, hostel_e]
        db.session.add_all(hostels)
        db.session.flush()

        # ==============================================================
        #  ROOMS (3 per hostel = 15 rooms)
        # ==============================================================
        rooms = {}
        for hostel, prefix in [(hostel_a, "A"), (hostel_b, "B"), (hostel_c, "C"),
                               (hostel_d, "D"), (hostel_e, "E")]:
            for num in ["101", "102", "103"]:
                r = Room(hostel_id=hostel.hostel_id, room_no=f"{prefix}-{num}")
                db.session.add(r)
                rooms[f"{prefix}-{num}"] = r
        db.session.flush()

        student_data = [
            # (email, name, roll_no, contact, department, hostel)
            # --- CSE (7 students) ---
            ("rahul.deka@gmail.com",        "Rahul Deka",        "2023CSE001", "9000000001", "CSE", "Hostel A"),
            ("priya.mahanta@gmail.com",     "Priya Mahanta",     "2023CSE002", "9000000002", "CSE", "Hostel B"),
            ("ankit.sarma@gmail.com",       "Ankit Sarma",       "2023CSE003", "9000000003", "CSE", "Hostel C"),
            ("neha.bora@gmail.com",         "Neha Bora",         "2023CSE004", "9000000004", "CSE", "Hostel D"),
            ("rohit.kalita@gmail.com",      "Rohit Kalita",      "2023CSE005", "9000000005", "CSE", "Hostel E"),
            ("sneha.choudhury@gmail.com",   "Sneha Choudhury",   "2023CSE006", "9000000006", "CSE", "Hostel A"),
            ("arjun.nath@gmail.com",        "Arjun Nath",        "2023CSE007", "9000000007", "CSE", "Hostel B"),
            # --- ECE (7 students) ---
            ("amit.choudhury@gmail.com",    "Amit Choudhury",    "2023ECE001", "9000000008", "ECE", "Hostel C"),
            ("kavita.rani@gmail.com",       "Kavita Rani",       "2023ECE002", "9000000009", "ECE", "Hostel D"),
            ("deepak.nath@gmail.com",       "Deepak Nath",       "2023ECE003", "9000000010", "ECE", "Hostel E"),
            ("ritu.kalita@gmail.com",       "Ritu Kalita",       "2023ECE004", "9000000011", "ECE", "Hostel A"),
            ("sanjay.malakar@gmail.com",    "Sanjay Malakar",    "2023ECE005", "9000000012", "ECE", "Hostel B"),
            ("mrinmoy.dey@gmail.com",       "Mrinmoy Dey",       "2023ECE006", "9000000013", "ECE", "Hostel C"),
            ("pallabi.saikia@gmail.com",    "Pallabi Saikia",    "2023ECE007", "9000000014", "ECE", "Hostel D"),
            # --- ME (6 students) ---
            ("suraj.hazarika@gmail.com",    "Suraj Hazarika",    "2023ME001",  "9000000015", "ME",  "Hostel E"),
            ("pooja.das@gmail.com",         "Pooja Das",         "2023ME002",  "9000000016", "ME",  "Hostel A"),
            ("manish.baruah@gmail.com",     "Manish Baruah",     "2023ME003",  "9000000017", "ME",  "Hostel B"),
            ("ankita.phukan@gmail.com",     "Ankita Phukan",     "2023ME004",  "9000000018", "ME",  "Hostel C"),
            ("bikash.medhi@gmail.com",      "Bikash Medhi",      "2023ME005",  "9000000019", "ME",  "Hostel D"),
            ("jyoti.bhuyan@gmail.com",      "Jyoti Bhuyan",      "2023ME006",  "9000000020", "ME",  "Hostel E"),
            # --- CE (6 students) ---
            ("tapash.dutta@gmail.com",      "Tapash Dutta",      "2023CE001",  "9000000021", "CE",  "Hostel A"),
            ("monika.baishya@gmail.com",    "Monika Baishya",    "2023CE002",  "9000000022", "CE",  "Hostel B"),
            ("kunal.rajkhowa@gmail.com",    "Kunal Rajkhowa",    "2023CE003",  "9000000023", "CE",  "Hostel C"),
            ("pinkimoni.borah@gmail.com",   "Pinkimoni Borah",   "2023CE004",  "9000000024", "CE",  "Hostel D"),
            ("nabajit.deka@gmail.com",      "Nabajit Deka",      "2023CE005",  "9000000025", "CE",  "Hostel E"),
            ("barsha.kashyap@gmail.com",    "Barsha Kashyap",    "2023CE006",  "9000000026", "CE",  "Hostel A"),
            # --- FET (6 students) ---
            ("diganta.gogoi@gmail.com",     "Diganta Gogoi",     "2023FET001", "9000000027", "FET", "Hostel B"),
            ("mitali.sharma@gmail.com",     "Mitali Sharma",     "2023FET002", "9000000028", "FET", "Hostel C"),
            ("partha.bora@gmail.com",       "Partha Bora",       "2023FET003", "9000000029", "FET", "Hostel D"),
            ("anuradha.hazarika@gmail.com", "Anuradha Hazarika", "2023FET004", "9000000030", "FET", "Hostel E"),
            ("hemanta.talukdar@gmail.com",  "Hemanta Talukdar",  "2023FET005", "9000000031", "FET", "Hostel A"),
            ("kaberi.das@gmail.com",        "Kaberi Das",        "2023FET006", "9000000032", "FET", "Hostel B"),
        ]

        mentor_map = {"CSE": mentor_cse, "ECE": mentor_ece, "ME": mentor_me,
                      "CE": mentor_ce, "FET": mentor_fet}

        hostel_obj_map = {
            "Hostel A": hostel_a,
            "Hostel B": hostel_b,
            "Hostel C": hostel_c,
            "Hostel D": hostel_d,
            "Hostel E": hostel_e
        }
        
        prefix_map = {
            "Hostel A": "A",
            "Hostel B": "B",
            "Hostel C": "C",
            "Hostel D": "D",
            "Hostel E": "E"
        }

        room_nums = ["101", "102", "103"]

        students = []
        for i, (email, name, roll_no, contact, dept, hostel_name) in enumerate(student_data):
            prefix = prefix_map[hostel_name]
            room_key = f"{prefix}-{room_nums[i % 3]}"
            s = Student(
                user_id=u_students[i].user_id,
                name=name,
                roll_no=roll_no,
                room_id=rooms[room_key].room_id,
                hostel_id=hostel_obj_map[hostel_name].hostel_id,
                contact_no=contact,
                mentor_id=mentor_map[dept].mentor_id,
                department=dept,
            )
            students.append(s)
        db.session.add_all(students)
        db.session.flush()

        # ==============================================================
        #  SECURITY STAFF (1)
        # ==============================================================
        guard = SecurityStaff(user_id=u_security.user_id, name="Ramu Kalita", shift="Day")
        db.session.add(guard)
        db.session.flush()

        # ==============================================================
        #  OUTPASSES (varied scenarios)
        # ==============================================================

        # ------------------------------------------------------------------
        db.session.commit()

        # ==============================================================
        #  SUMMARY
        # ==============================================================

        print("[OK] Database seeded successfully!")
        print()
        print("   -- Hostels --")
        for h, w in zip(hostels, wardens):
            print(f"     {h.hostel_name}  ->  Warden: {w.name}")
        print()
        print("   -- Departments --")
        depts = ["CSE", "ECE", "ME", "CE", "FET"]
        for d, m, h in zip(depts, u_mentors, u_hods):
            print(f"     {d:<4} ->  Mentor: {m.name:<22}  HOD: {h.name}")
        print()
        print(f"   -- Students ({len(students)}) --")
        for s in students:
            print(f"     {s.roll_no:<12} {s.name:<22} {s.department:<4} "
                  f"{s.hostel.hostel_name}  Room {s.room.room_no}")
        print()
        print("   -- Security --")
        print(f"     {guard.name} ({guard.shift} shift)")
        print()
        print()
        print("   ===================================================")
        print("   LOGIN CREDENTIALS  (password shown after /)")
        print("   ===================================================")
        print()
        print("   Wardens (all: warden123):")
        for (email, name, _), h in zip(warden_data, hostels):
            print(f"     {email:<30} ({h.hostel_name})")
        print()
        print("   Mentors (all: mentor123):")
        for email, name, dept in mentor_data:
            print(f"     {email:<30} ({dept})")
        print()
        print("   HODs (all: hod123):")
        for email, name, dept in hod_data:
            print(f"     {email:<30} ({dept})")
        print()
        print("   Students (all: student123):")
        for (email, _, roll_no, _, dept, _) in student_data:
            print(f"     {email:<35} ({roll_no}, {dept})")
        print()
        print("   Security: security.desk@gmail.com / security123")
        print()
        print("   ★ Admin: admin@hostelout.com / admin123")


if __name__ == "__main__":
    seed()
