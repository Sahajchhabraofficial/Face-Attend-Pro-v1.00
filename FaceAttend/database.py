"""
database.py — File-based Data Storage (Prototype)

Students  → data/students.json
Attendance → data/attendance/YYYY-MM-DD.csv

When you move to MySQL later, just replace the body of each method
while keeping the same interface.
"""

import json
import csv
import os
from datetime import date, datetime

BASE_DIR        = os.path.dirname(os.path.abspath(__file__))
DATA_DIR        = os.path.join(BASE_DIR, "data")
STUDENTS_FILE   = os.path.join(DATA_DIR, "students.json")
ATTENDANCE_DIR  = os.path.join(DATA_DIR, "attendance")

os.makedirs(ATTENDANCE_DIR, exist_ok=True)


# ════════════════════════════════════════════════════════════════════
# STUDENT DATABASE
# ════════════════════════════════════════════════════════════════════
class StudentDB:
    """
    Schema (students.json):
    {
      "<int_id>": {
        "name":       "Full Name",
        "roll":       "CS2024001",
        "registered": "2025-01-15T10:30:00"
      },
      ...
    }
    """

    def __init__(self):
        if not os.path.exists(STUDENTS_FILE):
            self._write({})

    # ── internal helpers ─────────────────────────────────────────────
    def _read(self) -> dict:
        with open(STUDENTS_FILE, "r") as f:
            return json.load(f)

    def _write(self, data: dict):
        with open(STUDENTS_FILE, "w") as f:
            json.dump(data, f, indent=2)

    # ── public API ───────────────────────────────────────────────────
    def add_student(self, student_id: int, name: str, roll: str):
        data = self._read()
        data[str(student_id)] = {
            "name":       name,
            "roll":       roll,
            "registered": datetime.now().isoformat(timespec="seconds"),
        }
        self._write(data)

    def get_students(self) -> dict:
        """Returns {str_id: {name, roll, registered}, ...}"""
        return self._read()

    def get_student(self, student_id) -> dict | None:
        return self._read().get(str(student_id))

    def delete_student(self, student_id: int):
        data = self._read()
        data.pop(str(student_id), None)
        self._write(data)

    def roll_exists(self, roll: str) -> bool:
        for s in self._read().values():
            if s["roll"].lower() == roll.lower():
                return True
        return False

    def next_id(self) -> int:
        data = self._read()
        if not data:
            return 1
        return max(int(k) for k in data.keys()) + 1

    def total(self) -> int:
        return len(self._read())


# ════════════════════════════════════════════════════════════════════
# ATTENDANCE DATABASE
# ════════════════════════════════════════════════════════════════════
class AttendanceDB:
    """
    Schema (YYYY-MM-DD.csv):
    student_id, name, time, date
    """

    def _path(self, date_str: str) -> str:
        return os.path.join(ATTENDANCE_DIR, f"{date_str}.csv")

    # ── core operations ──────────────────────────────────────────────
    def mark(self, student_id: int, name: str) -> bool:
        """Mark attendance for today.
        Returns True if newly marked, False if already marked.
        """
        today    = date.today().isoformat()
        filepath = self._path(today)

        # Check for duplicate
        if os.path.exists(filepath):
            with open(filepath, "r") as f:
                for row in csv.reader(f):
                    if row and row[0] == str(student_id):
                        return False  # Already present

        # Write new entry
        with open(filepath, "a", newline="") as f:
            csv.writer(f).writerow([
                student_id,
                name,
                datetime.now().strftime("%H:%M:%S"),
                today,
            ])
        return True

    def get_today(self) -> list[list]:
        return self.get_by_date(date.today().isoformat())

    def get_by_date(self, date_str: str) -> list[list]:
        filepath = self._path(date_str)
        if not os.path.exists(filepath):
            return []
        with open(filepath, "r") as f:
            return [r for r in csv.reader(f) if r]

    def get_all_dates(self) -> list[str]:
        files = [f for f in os.listdir(ATTENDANCE_DIR) if f.endswith(".csv")]
        return sorted([f.replace(".csv", "") for f in files], reverse=True)

    def already_marked(self, student_id: int) -> bool:
        today = date.today().isoformat()
        filepath = self._path(today)
        if not os.path.exists(filepath):
            return False
        with open(filepath, "r") as f:
            return any(row and row[0] == str(student_id) for row in csv.reader(f))

    # ── stats helpers ────────────────────────────────────────────────
    def today_count(self) -> int:
        return len(self.get_today())

    def attendance_rate(self, total_students: int) -> int:
        """% present today (0-100)."""
        if total_students == 0:
            return 0
        return int(self.today_count() / total_students * 100)
