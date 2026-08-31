"""Test all HostelOut API endpoints via HTTP requests."""

import requests
import json
import sys

BASE = "http://127.0.0.1:5000"
passed = 0
failed = 0


def test(label, method, path, json_body=None, expect_status=None):
    global passed, failed
    url = f"{BASE}{path}"
    try:
        if method == "GET":
            r = requests.get(url)
        else:
            r = requests.post(url, json=json_body)

        status_ok = True
        if expect_status and r.status_code != expect_status:
            status_ok = False

        data = r.json()
        tag = "PASS" if status_ok else "FAIL"
        if status_ok:
            passed += 1
        else:
            failed += 1
        print(f"[{tag}] {label}")
        print(f"       {method} {path} -> {r.status_code}")
        print(f"       Response: {json.dumps(data, indent=2)[:500]}")
        print()
        return data
    except Exception as e:
        failed += 1
        print(f"[FAIL] {label}")
        print(f"       ERROR: {e}")
        print()
        return None


print("=" * 60)
print("  HostelOut API Endpoint Tests")
print("=" * 60)
print()

# 1. POST /students — create a new student
test("POST /students — create student",
     "POST", "/students",
     {"name": "Test Kumar", "roll_no": "TU2023099",
      "room_id": 1, "hostel_id": 1, "contact_no": "9999999999"},
     expect_status=201)

# 2. POST /outpasses — student submits outpass
test("POST /outpasses — new outpass request",
     "POST", "/outpasses",
     {"student_id": 3, "reason": "Shopping",
      "destination": "City Market",
      "requested_departure": "2026-08-22T10:00:00",
      "requested_return": "2026-08-22T18:00:00"},
     expect_status=201)

# 3. GET /outpasses/student/1 — Rahul's outpass history
test("GET /outpasses/student/1 — student history",
     "GET", "/outpasses/student/1",
     expect_status=200)

# 4. GET /outpasses/pending/1 — pending outpasses for hostel 1
test("GET /outpasses/pending/1 — pending requests",
     "GET", "/outpasses/pending/1",
     expect_status=200)

# 5. POST /outpasses/1/approve — approve the pending outpass
test("POST /outpasses/1/approve — approve outpass",
     "POST", "/outpasses/1/approve",
     {"warden_id": 1, "remark": "Approved via test"},
     expect_status=200)

# 6. POST /outpasses/1/approve — try re-approving (should fail 409)
test("POST /outpasses/1/approve — re-approve (expect 409)",
     "POST", "/outpasses/1/approve",
     {"warden_id": 1},
     expect_status=409)

# 7. POST /outpasses/4/reject — reject the new outpass (id=4)
test("POST /outpasses/4/reject — reject outpass",
     "POST", "/outpasses/4/reject",
     {"warden_id": 1, "remark": "Not allowed today"},
     expect_status=200)

# 8. POST /gatelog/1/exit — log exit for approved outpass 1
test("POST /gatelog/1/exit — log exit",
     "POST", "/gatelog/1/exit",
     {"staff_id": 1},
     expect_status=201)

# 9. POST /gatelog/4/exit — try exit on rejected outpass (should fail 403)
test("POST /gatelog/4/exit — exit on rejected (expect 403)",
     "POST", "/gatelog/4/exit",
     {"staff_id": 1},
     expect_status=403)

# 10. POST /gatelog/1/return — log return
test("POST /gatelog/1/return — log return",
     "POST", "/gatelog/1/return",
     {"staff_id": 1},
     expect_status=200)

# 11. POST /gatelog/1/return — try double return (should fail 409)
test("POST /gatelog/1/return — double return (expect 409)",
     "POST", "/gatelog/1/return",
     {"staff_id": 1},
     expect_status=409)

# 12. GET /reports/overdue/1 — overdue students
test("GET /reports/overdue/1 — overdue report",
     "GET", "/reports/overdue/1",
     expect_status=200)

print("=" * 60)
print(f"  Results: {passed} passed, {failed} failed out of {passed + failed}")
print("=" * 60)

if failed > 0:
    sys.exit(1)
