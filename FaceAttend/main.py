"""
main.py — FaceAttend Pro
Face-Recognition Attendance System  |  Prototype v1.0  |  File-based storage

Run:  python main.py
"""

import customtkinter as ctk
import cv2
import os
import threading
import time
from datetime import datetime
from PIL import Image

from database    import StudentDB, AttendanceDB
from face_engine import FaceEngine

# ════════════════════════════════════════════════════════════════════
#  THEME
# ════════════════════════════════════════════════════════════════════
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

C = {
    "bg":      "#0d0d1a",
    "sidebar": "#13132b",
    "card":    "#1a1a35",
    "accent":  "#1e2048",
    "blue":    "#4f8ef7",
    "green":   "#27ae60",
    "red":     "#c0392b",
    "yellow":  "#d4a017",
    "white":   "#e8e8f0",
    "sub":     "#7a7a99",
    "border":  "#2a2a50",
}

FONT_TITLE  = ("Segoe UI", 26, "bold")
FONT_SECT   = ("Segoe UI", 15, "bold")
FONT_BODY   = ("Segoe UI", 13)
FONT_SMALL  = ("Segoe UI", 11)
FONT_BADGE  = ("Segoe UI", 11, "bold")


# ════════════════════════════════════════════════════════════════════
#  SHARED WIDGET HELPERS
# ════════════════════════════════════════════════════════════════════
def card(parent, **kw) -> ctk.CTkFrame:
    return ctk.CTkFrame(parent, fg_color=C["card"], corner_radius=14, **kw)


def section_title(parent, text: str):
    ctk.CTkLabel(parent, text=text, font=ctk.CTkFont(*FONT_SECT),
                 text_color=C["white"]).pack(anchor="w", padx=20, pady=(18, 4))


def divider(parent):
    ctk.CTkFrame(parent, height=1, fg_color=C["border"]).pack(fill="x", padx=15, pady=6)


def stat_card(parent, icon: str, label: str, value: str, color: str) -> ctk.CTkLabel:
    f = ctk.CTkFrame(parent, fg_color=C["card"], corner_radius=14)
    ctk.CTkLabel(f, text=icon, font=ctk.CTkFont(size=30)).pack(pady=(16, 2))
    val_lbl = ctk.CTkLabel(f, text=value, font=ctk.CTkFont(size=22, weight="bold"),
                           text_color=color)
    val_lbl.pack()
    ctk.CTkLabel(f, text=label, font=ctk.CTkFont(*FONT_SMALL),
                 text_color=C["sub"]).pack(pady=(2, 16))
    return val_lbl


def table_header(parent, columns: list[tuple[str, int]]):
    """columns = [(text, col_weight), ...]"""
    for j, (h, w) in enumerate(columns):
        ctk.CTkLabel(parent, text=h, font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=C["blue"]).grid(row=0, column=j, padx=16, pady=10, sticky="w")
        parent.grid_columnconfigure(j, weight=w)


def table_row(parent, row_idx: int, values: list[str]):
    bg = C["accent"] if row_idx % 2 == 0 else C["card"]
    for j, val in enumerate(values):
        ctk.CTkLabel(parent, text=str(val), font=ctk.CTkFont(*FONT_BODY),
                     text_color=C["white"], fg_color="transparent"
                     ).grid(row=row_idx, column=j, padx=16, pady=6, sticky="w")


# ════════════════════════════════════════════════════════════════════
#  PAGE: DASHBOARD
# ════════════════════════════════════════════════════════════════════
class DashboardPage(ctk.CTkFrame):
    def __init__(self, parent, sdb: StudentDB, adb: AttendanceDB):
        super().__init__(parent, fg_color="transparent")
        self.sdb, self.adb = sdb, adb
        self._build()

    def _build(self):
        ctk.CTkLabel(self, text="📊  Dashboard",
                     font=ctk.CTkFont(*FONT_TITLE), text_color=C["white"]
                     ).pack(anchor="w", pady=(0, 18))

        # ── stat cards ──
        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", pady=(0, 18))
        stats = [
            ("👥", "Total Students", "0", C["blue"]),
            ("✅", "Present Today",  "0", C["green"]),
            ("❌", "Absent Today",   "0", C["red"]),
            ("📈", "Attendance Rate","0%", C["yellow"]),
        ]
        self._val_lbls = {}
        for i, (icon, label, val, color) in enumerate(stats):
            f = ctk.CTkFrame(row, fg_color=C["card"], corner_radius=14)
            f.grid(row=0, column=i, padx=8, sticky="nsew")
            row.grid_columnconfigure(i, weight=1)
            ctk.CTkLabel(f, text=icon, font=ctk.CTkFont(size=30)).pack(pady=(16, 2))
            vl = ctk.CTkLabel(f, text=val, font=ctk.CTkFont(size=22, weight="bold"),
                              text_color=color)
            vl.pack()
            ctk.CTkLabel(f, text=label, font=ctk.CTkFont(*FONT_SMALL),
                         text_color=C["sub"]).pack(pady=(2, 16))
            self._val_lbls[label] = vl

        # ── today's log ──
        ctk.CTkLabel(self, text="Today's Attendance Log",
                     font=ctk.CTkFont(*FONT_SECT), text_color=C["white"]
                     ).pack(anchor="w", pady=(4, 6))

        self.log_frame = ctk.CTkScrollableFrame(
            self, fg_color=C["card"], corner_radius=14, height=320)
        self.log_frame.pack(fill="both", expand=True)

        self.refresh()

    def refresh(self):
        # Clear log
        for w in self.log_frame.winfo_children():
            w.destroy()

        total   = self.sdb.total()
        records = self.adb.get_today()
        present = len(records)
        absent  = max(total - present, 0)
        rate    = f"{self.adb.attendance_rate(total)}%"

        updates = {
            "Total Students": str(total),
            "Present Today":  str(present),
            "Absent Today":   str(absent),
            "Attendance Rate": rate,
        }
        for k, v in updates.items():
            self._val_lbls[k].configure(text=v)

        cols = [("ID", 1), ("Name", 3), ("Time", 2), ("Date", 2)]
        table_header(self.log_frame, cols)

        if not records:
            ctk.CTkLabel(self.log_frame, text="No attendance recorded today.",
                         text_color=C["sub"]).grid(row=1, column=0, columnspan=4, pady=30)
            return
        for i, row in enumerate(records, 1):
            table_row(self.log_frame, i, row[:4])


# ════════════════════════════════════════════════════════════════════
#  PAGE: REGISTER STUDENT
# ════════════════════════════════════════════════════════════════════
class RegisterPage(ctk.CTkFrame):
    SAMPLE_TARGET = 30

    def __init__(self, parent, sdb: StudentDB, engine: FaceEngine,
                 on_done=None):
        super().__init__(parent, fg_color="transparent")
        self.sdb, self.engine = sdb, engine
        self.on_done = on_done
        self.cap = None
        self._capturing = False
        self._count = 0
        self._sid   = None
        self._build()

    def _build(self):
        ctk.CTkLabel(self, text="👤  Register New Student",
                     font=ctk.CTkFont(*FONT_TITLE), text_color=C["white"]
                     ).pack(anchor="w", pady=(0, 16))

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True)
        body.grid_columnconfigure(0, weight=1)
        body.grid_columnconfigure(1, weight=2)

        # ── LEFT : form ──────────────────────────────────────────────
        left = card(body)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        section_title(left, "Student Information")
        divider(left)

        for label, attr, hint in [
            ("Full Name",   "name_e",  "e.g. Arjun Sharma"),
            ("Roll Number", "roll_e",  "e.g. CS2024042"),
        ]:
            ctk.CTkLabel(left, text=label, font=ctk.CTkFont(*FONT_SMALL),
                         text_color=C["sub"]).pack(anchor="w", padx=20, pady=(8, 0))
            e = ctk.CTkEntry(left, placeholder_text=hint, height=36,
                             font=ctk.CTkFont(*FONT_BODY))
            e.pack(fill="x", padx=20, pady=(4, 0))
            setattr(self, attr, e)

        # Progress
        ctk.CTkFrame(left, height=1, fg_color=C["border"]).pack(fill="x", padx=15, pady=14)

        self.prog_bar = ctk.CTkProgressBar(left, height=10)
        self.prog_bar.pack(fill="x", padx=20, pady=(0, 4))
        self.prog_bar.set(0)

        self.prog_lbl = ctk.CTkLabel(left, text="Samples: 0 / 30",
                                     font=ctk.CTkFont(*FONT_SMALL), text_color=C["sub"])
        self.prog_lbl.pack(anchor="w", padx=20, pady=(0, 10))

        self.status_lbl = ctk.CTkLabel(left, text="", wraplength=240,
                                       font=ctk.CTkFont(*FONT_SMALL))
        self.status_lbl.pack(padx=20, pady=4)

        # Buttons
        self.cap_btn = ctk.CTkButton(
            left, text="📷  Start Capture", height=40,
            fg_color=C["blue"], hover_color="#2d6bcf",
            font=ctk.CTkFont(*FONT_BODY, weight="bold"),
            command=self._start_capture)
        self.cap_btn.pack(fill="x", padx=20, pady=(10, 6))

        self.reg_btn = ctk.CTkButton(
            left, text="✅  Register & Train", height=40,
            fg_color=C["green"], hover_color="#1e8449",
            font=ctk.CTkFont(*FONT_BODY, weight="bold"),
            state="disabled", command=self._save_student)
        self.reg_btn.pack(fill="x", padx=20, pady=(0, 20))

        # ── RIGHT : camera ───────────────────────────────────────────
        right = card(body)
        right.grid(row=0, column=1, sticky="nsew")

        section_title(right, "📸  Camera Preview")
        divider(right)

        self.cam_lbl = ctk.CTkLabel(
            right,
            text="Click  'Start Capture'  to activate the webcam",
            text_color=C["sub"],
            font=ctk.CTkFont(*FONT_BODY),
            width=520, height=380)
        self.cam_lbl.pack(padx=15, pady=(4, 15))

    # ── helpers ──────────────────────────────────────────────────────
    def _status(self, msg, color=C["white"]):
        self.status_lbl.configure(text=msg, text_color=color)

    def _start_capture(self):
        name = self.name_e.get().strip()
        roll = self.roll_e.get().strip()

        if not name or not roll:
            self._status("⚠  Please fill in all fields.", C["yellow"]); return
        if self.sdb.roll_exists(roll):
            self._status("⚠  Roll number already exists.", C["red"]); return

        self._sid   = self.sdb.next_id()
        self._count = 0
        self._capturing = True
        self.prog_bar.set(0)
        self.reg_btn.configure(state="disabled")
        self.cap_btn.configure(text="⏹  Stop", fg_color=C["red"],
                               hover_color="#922b21", command=self._stop_capture)
        self._status("🎥  Look at the camera…", C["blue"])

        self.cap = cv2.VideoCapture(0)
        threading.Thread(target=self._cap_loop, daemon=True).start()

    def _cap_loop(self):
        while self._capturing and self._count < self.SAMPLE_TARGET:
            ret, frame = self.cap.read()
            if not ret:
                break

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.engine.detector.detectMultiScale(
                gray, scaleFactor=1.1, minNeighbors=5, minSize=(80, 80))

            disp = frame.copy()
            for (x, y, w, h) in faces[:1]:          # one face at a time
                self._count += 1
                roi  = cv2.resize(gray[y:y+h, x:x+w], (200, 200))
                path = os.path.join(self.engine.faces_dir,
                                    f"{self._sid}_{self._count}.jpg")
                cv2.imwrite(path, roi)

                cv2.rectangle(disp, (x, y), (x+w, y+h), (39, 174, 96), 2)
                cv2.putText(disp, f"Sample {self._count}/{self.SAMPLE_TARGET}",
                            (x, y - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.55,
                            (39, 174, 96), 2)

            self._push_frame(disp, self._count, self.SAMPLE_TARGET)
            time.sleep(0.1)

        self.cap.release()
        if self._count >= self.SAMPLE_TARGET:
            self.after(0, self._capture_done)

    def _push_frame(self, frame, count, target):
        rgb     = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img     = Image.fromarray(rgb)
        ctkimg  = ctk.CTkImage(light_image=img, size=(520, 380))
        try:
            self.cam_lbl.configure(image=ctkimg, text="")
            self.cam_lbl.image = ctkimg
        except Exception:
            pass
        self.after(0, lambda: self.prog_bar.set(count / target))
        self.after(0, lambda: self.prog_lbl.configure(
            text=f"Samples: {count} / {target}"))

    def _capture_done(self):
        self._capturing = False
        self._status(f"✅  {self.SAMPLE_TARGET} samples captured!", C["green"])
        self.cap_btn.configure(text="📷  Start Capture", fg_color=C["blue"],
                               hover_color="#2d6bcf", command=self._start_capture)
        self.reg_btn.configure(state="normal")

    def _stop_capture(self):
        self._capturing = False
        self.cap_btn.configure(text="📷  Start Capture", fg_color=C["blue"],
                               hover_color="#2d6bcf", command=self._start_capture)
        self._status("Capture stopped.", C["yellow"])

    def _save_student(self):
        name = self.name_e.get().strip()
        roll = self.roll_e.get().strip()
        self._status("⏳  Training model, please wait…", C["yellow"])
        self.reg_btn.configure(state="disabled")

        def _do():
            self.sdb.add_student(self._sid, name, roll)
            ok = self.engine.train()
            def _done():
                if ok:
                    self._status(f"🎉  {name} registered!", C["green"])
                    self.name_e.delete(0, "end")
                    self.roll_e.delete(0, "end")
                    self.prog_bar.set(0)
                    self.prog_lbl.configure(text="Samples: 0 / 30")
                    self.cam_lbl.configure(image=None,
                        text="Click  'Start Capture'  to activate the webcam")
                    self._count = 0
                    if self.on_done:
                        self.on_done()
                else:
                    self._status("❌  Training failed. Try again.", C["red"])
                    self.reg_btn.configure(state="normal")
            self.after(0, _done)

        threading.Thread(target=_do, daemon=True).start()

    def cleanup(self):
        self._capturing = False
        if self.cap and self.cap.isOpened():
            self.cap.release()


# ════════════════════════════════════════════════════════════════════
#  PAGE: TAKE ATTENDANCE
# ════════════════════════════════════════════════════════════════════
class AttendancePage(ctk.CTkFrame):
    def __init__(self, parent, sdb: StudentDB, adb: AttendanceDB,
                 engine: FaceEngine):
        super().__init__(parent, fg_color="transparent")
        self.sdb, self.adb, self.engine = sdb, adb, engine
        self.cap      = None
        self._running = False
        self._marked  = set()
        self._build()

    def _build(self):
        ctk.CTkLabel(self, text="📷  Take Attendance",
                     font=ctk.CTkFont(*FONT_TITLE), text_color=C["white"]
                     ).pack(anchor="w", pady=(0, 14))

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True)
        body.grid_columnconfigure(0, weight=3)
        body.grid_columnconfigure(1, weight=1)

        # ── Camera card ──────────────────────────────────────────────
        cam_card = card(body)
        cam_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        ctrl = ctk.CTkFrame(cam_card, fg_color="transparent")
        ctrl.pack(fill="x", padx=15, pady=12)

        self.start_btn = ctk.CTkButton(
            ctrl, text="▶  Start Camera", width=150, height=36,
            fg_color=C["green"], hover_color="#1e8449",
            font=ctk.CTkFont(*FONT_BODY, weight="bold"),
            command=self._start)
        self.start_btn.pack(side="left", padx=(0, 8))

        self.stop_btn = ctk.CTkButton(
            ctrl, text="⏹  Stop", width=100, height=36,
            fg_color=C["red"], hover_color="#922b21",
            font=ctk.CTkFont(*FONT_BODY),
            state="disabled", command=self._stop)
        self.stop_btn.pack(side="left")

        self.dot_lbl = ctk.CTkLabel(ctrl, text="⬤ Idle",
                                    font=ctk.CTkFont(*FONT_SMALL), text_color=C["sub"])
        self.dot_lbl.pack(side="right")

        self.cam_lbl = ctk.CTkLabel(
            cam_card,
            text="Press  'Start Camera'  to begin attendance",
            text_color=C["sub"],
            font=ctk.CTkFont(*FONT_BODY),
            width=580, height=420)
        self.cam_lbl.pack(padx=15, pady=(0, 15))

        # ── Side panel ───────────────────────────────────────────────
        side = card(body)
        side.grid(row=0, column=1, sticky="nsew")

        section_title(side, "✅  Marked Today")
        divider(side)

        self.mark_list = ctk.CTkScrollableFrame(side, fg_color="transparent")
        self.mark_list.pack(fill="both", expand=True, padx=8, pady=(0, 4))

        self.cnt_lbl = ctk.CTkLabel(side, text="0 students present",
                                    font=ctk.CTkFont(*FONT_SMALL), text_color=C["sub"])
        self.cnt_lbl.pack(pady=8)

    # ── camera control ───────────────────────────────────────────────
    def _start(self):
        if not self.engine.is_trained:
            self.dot_lbl.configure(
                text="⚠ No model — register students first!", text_color=C["yellow"])
            return

        self._running = True
        self.cap = cv2.VideoCapture(0)
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self.dot_lbl.configure(text="⬤ Live", text_color=C["green"])

        # Load already-marked students for today
        for row in self.adb.get_today():
            if row:
                try:
                    self._marked.add(int(row[0]))
                except ValueError:
                    pass
        self._refresh_marks()
        threading.Thread(target=self._loop, daemon=True).start()

    def _loop(self):
        students = self.sdb.get_students()
        while self._running:
            ret, frame = self.cap.read()
            if not ret:
                break

            hits = self.engine.recognize(frame)
            for h in hits:
                x, y, w_, ht = h["bbox"]
                if h["known"]:
                    sid     = h["label"]
                    student = students.get(str(sid))
                    name    = student["name"] if student else f"ID {sid}"
                    color   = (39, 174, 96)
                    label   = f"{name}  ({h['confidence']:.0f})"

                    if sid not in self._marked:
                        if self.adb.mark(sid, name):
                            self._marked.add(sid)
                            self.after(0, self._refresh_marks)
                else:
                    color = (192, 57, 43)
                    label = f"Unknown ({h['confidence']:.0f})"

                cv2.rectangle(frame, (x, y), (x+w_, y+ht), color, 2)
                cv2.putText(frame, label, (x, y - 8),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2)

            rgb    = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img    = Image.fromarray(rgb)
            ctkimg = ctk.CTkImage(light_image=img, size=(580, 420))
            try:
                self.cam_lbl.configure(image=ctkimg, text="")
                self.cam_lbl.image = ctkimg
            except Exception:
                break

        if self.cap:
            self.cap.release()

    def _stop(self):
        self._running = False
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        self.dot_lbl.configure(text="⬤ Stopped", text_color=C["red"])
        self.cam_lbl.configure(image=None,
                               text="Press  'Start Camera'  to begin attendance")

    def _refresh_marks(self):
        for w in self.mark_list.winfo_children():
            w.destroy()
        students = self.sdb.get_students()
        for sid in sorted(self._marked):
            s = students.get(str(sid))
            if s:
                f = ctk.CTkFrame(self.mark_list, fg_color=C["accent"], corner_radius=8)
                f.pack(fill="x", pady=3)
                ctk.CTkLabel(f, text=f"✅  {s['name']}",
                             text_color=C["green"],
                             font=ctk.CTkFont(*FONT_SMALL, weight="bold")
                             ).pack(anchor="w", padx=12, pady=6)
        self.cnt_lbl.configure(
            text=f"{len(self._marked)} student{'s' if len(self._marked) != 1 else ''} present")

    def cleanup(self):
        self._running = False
        if self.cap and self.cap.isOpened():
            self.cap.release()


# ════════════════════════════════════════════════════════════════════
#  PAGE: STUDENTS LIST
# ════════════════════════════════════════════════════════════════════
class StudentsPage(ctk.CTkFrame):
    def __init__(self, parent, sdb: StudentDB):
        super().__init__(parent, fg_color="transparent")
        self.sdb = sdb
        self._build()

    def _build(self):
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", pady=(0, 14))
        ctk.CTkLabel(hdr, text="👥  Registered Students",
                     font=ctk.CTkFont(*FONT_TITLE), text_color=C["white"]
                     ).pack(side="left")
        ctk.CTkButton(hdr, text="🔄  Refresh", width=110, height=34,
                      fg_color=C["accent"], hover_color=C["border"],
                      command=self.refresh).pack(side="right")

        self.table = ctk.CTkScrollableFrame(
            self, fg_color=C["card"], corner_radius=14)
        self.table.pack(fill="both", expand=True)

        self.refresh()

    def refresh(self):
        for w in self.table.winfo_children():
            w.destroy()

        table_header(self.table, [
            ("#", 1), ("Full Name", 3), ("Roll Number", 2), ("Registered On", 2)])

        students = self.sdb.get_students()
        if not students:
            ctk.CTkLabel(self.table, text="No students registered yet.",
                         text_color=C["sub"]).grid(row=1, column=0, columnspan=4, pady=30)
            return
        for i, (sid, d) in enumerate(students.items(), 1):
            table_row(self.table, i, [
                sid, d["name"], d["roll"], d.get("registered", "—")[:10]])


# ════════════════════════════════════════════════════════════════════
#  PAGE: VIEW RECORDS
# ════════════════════════════════════════════════════════════════════
class RecordsPage(ctk.CTkFrame):
    def __init__(self, parent, adb: AttendanceDB):
        super().__init__(parent, fg_color="transparent")
        self.adb = adb
        self._build()

    def _build(self):
        ctk.CTkLabel(self, text="📋  Attendance Records",
                     font=ctk.CTkFont(*FONT_TITLE), text_color=C["white"]
                     ).pack(anchor="w", pady=(0, 14))

        # Filter bar
        fbar = card(self)
        fbar.pack(fill="x", pady=(0, 12))

        inner = ctk.CTkFrame(fbar, fg_color="transparent")
        inner.pack(fill="x", padx=15, pady=10)

        ctk.CTkLabel(inner, text="Date:", font=ctk.CTkFont(*FONT_BODY)).pack(
            side="left", padx=(0, 8))

        dates = self.adb.get_all_dates()
        self._date_var = ctk.StringVar(value=dates[0] if dates else "—")
        self.date_menu = ctk.CTkOptionMenu(
            inner,
            values=dates if dates else ["—"],
            variable=self._date_var,
            command=self._load,
            width=170, height=34)
        self.date_menu.pack(side="left", padx=(0, 8))

        ctk.CTkButton(inner, text="🔄  Refresh Dates", width=140, height=34,
                      fg_color=C["accent"], hover_color=C["border"],
                      command=self._refresh_dates).pack(side="left")

        self.count_lbl = ctk.CTkLabel(inner, text="",
                                      font=ctk.CTkFont(*FONT_SMALL), text_color=C["sub"])
        self.count_lbl.pack(side="right")

        # Table
        self.table = ctk.CTkScrollableFrame(
            self, fg_color=C["card"], corner_radius=14)
        self.table.pack(fill="both", expand=True)

        if dates:
            self._load(dates[0])

    def _load(self, date_str: str):
        for w in self.table.winfo_children():
            w.destroy()

        table_header(self.table, [
            ("Student ID", 1), ("Name", 3), ("Time", 2), ("Date", 2)])

        records = self.adb.get_by_date(date_str)
        if not records:
            ctk.CTkLabel(self.table, text="No records for this date.",
                         text_color=C["sub"]).grid(row=1, column=0, columnspan=4, pady=30)
            self.count_lbl.configure(text="0 records")
            return
        for i, row in enumerate(records, 1):
            table_row(self.table, i, row[:4])
        self.count_lbl.configure(text=f"{len(records)} records")

    def _refresh_dates(self):
        dates = self.adb.get_all_dates()
        self.date_menu.configure(values=dates if dates else ["—"])
        if dates:
            self._date_var.set(dates[0])
            self._load(dates[0])


# ════════════════════════════════════════════════════════════════════
#  MAIN WINDOW
# ════════════════════════════════════════════════════════════════════
class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.sdb    = StudentDB()
        self.adb    = AttendanceDB()
        self.engine = FaceEngine()

        self.title("FaceAttend Pro  —  Smart Attendance System")
        self.geometry("1280x760")
        self.minsize(1050, 660)
        self.configure(fg_color=C["bg"])

        self._build_sidebar()
        self._build_content()
        self._build_pages()
        self.show("dashboard")

    # ── layout ───────────────────────────────────────────────────────
    def _build_sidebar(self):
        sb = ctk.CTkFrame(self, fg_color=C["sidebar"], width=230, corner_radius=0)
        sb.pack(side="left", fill="y")
        sb.pack_propagate(False)
        self.sidebar = sb

        # Logo
        ctk.CTkLabel(sb, text="🎓", font=ctk.CTkFont(size=44)
                     ).pack(pady=(28, 2))
        ctk.CTkLabel(sb, text="FaceAttend Pro",
                     font=ctk.CTkFont(size=18, weight="bold"), text_color=C["white"]
                     ).pack()
        ctk.CTkLabel(sb, text="Smart Attendance System",
                     font=ctk.CTkFont(*FONT_SMALL), text_color=C["sub"]
                     ).pack(pady=(2, 18))

        ctk.CTkFrame(sb, height=1, fg_color=C["border"]).pack(fill="x", padx=18)

        self._nav_btns: dict[str, ctk.CTkButton] = {}
        nav = [
            ("dashboard",  "📊   Dashboard"),
            ("attendance", "📷   Take Attendance"),
            ("register",   "👤   Register Student"),
            ("students",   "👥   Students"),
            ("records",    "📋   View Records"),
        ]
        for pid, label in nav:
            btn = ctk.CTkButton(
                sb, text=label, anchor="w", height=44,
                corner_radius=10, fg_color="transparent",
                hover_color=C["accent"], text_color=C["white"],
                font=ctk.CTkFont(size=13),
                command=lambda p=pid: self.show(p))
            btn.pack(fill="x", padx=12, pady=3)
            self._nav_btns[pid] = btn

        ctk.CTkFrame(sb, height=1, fg_color=C["border"]).pack(
            fill="x", padx=18, pady=12)
        ctk.CTkLabel(sb, text="v1.0  •  Prototype",
                     font=ctk.CTkFont(size=10), text_color=C["sub"]
                     ).pack(pady=2)

    def _build_content(self):
        self.content = ctk.CTkFrame(self, fg_color=C["bg"])
        self.content.pack(side="right", fill="both", expand=True, padx=22, pady=22)

    def _build_pages(self):
        self._pages: dict[str, ctk.CTkFrame] = {
            "dashboard": DashboardPage(self.content, self.sdb, self.adb),
            "attendance": AttendancePage(self.content, self.sdb, self.adb, self.engine),
            "register":  RegisterPage(self.content, self.sdb, self.engine,
                                      on_done=self._after_register),
            "students":  StudentsPage(self.content, self.sdb),
            "records":   RecordsPage(self.content, self.adb),
        }

    def show(self, page_id: str):
        # Cleanup cameras on other pages
        for pid, pg in self._pages.items():
            if pid != page_id and hasattr(pg, "cleanup"):
                pg.cleanup()
        for pg in self._pages.values():
            pg.pack_forget()
        self._pages[page_id].pack(fill="both", expand=True)

        for pid, btn in self._nav_btns.items():
            if pid == page_id:
                btn.configure(fg_color=C["accent"])
            else:
                btn.configure(fg_color="transparent")

    def _after_register(self):
        self._pages["students"].refresh()
        self._pages["dashboard"].refresh()

    def _on_close(self):
        for pg in self._pages.values():
            if hasattr(pg, "cleanup"):
                pg.cleanup()
        self.destroy()


# ════════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    app = App()
    app.protocol("WM_DELETE_WINDOW", app._on_close)
    app.mainloop()
