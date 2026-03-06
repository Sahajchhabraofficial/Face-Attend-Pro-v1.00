# 🎓 FaceAttend Pro — Face Recognition Attendance System
**Prototype v1.0  |  File-based Storage  |  Built with Python + CustomTkinter + OpenCV**

---

## 📁 Project Structure

```
FaceAttend/
├── main.py           ← Entry point + all UI pages
├── database.py       ← File-based student & attendance storage
├── face_engine.py    ← Face detection & recognition (OpenCV LBPH)
├── requirements.txt
└── data/             ← Auto-created on first run
    ├── students.json
    ├── model.yml     ← Trained face model
    ├── faces/        ← Captured face samples (30 per student)
    └── attendance/
        └── YYYY-MM-DD.csv   ← Daily attendance logs
```

---

## ⚡ Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```
> ⚠️ **Important:** Use `opencv-contrib-python` (NOT `opencv-python`).  
> The contrib package includes the `cv2.face` module required for LBPH recognition.

### 2. Run the app
```bash
python main.py
```

---

## 🖥️ Features

| Page | Description |
|------|-------------|
| 📊 Dashboard | Today's stats + live attendance log |
| 📷 Take Attendance | Real-time face recognition via webcam |
| 👤 Register Student | Capture 30 face samples + auto-train model |
| 👥 Students | View all registered students |
| 📋 View Records | Browse attendance by date |

---

## 🔧 How Face Recognition Works

1. **Registration** — 30 grayscale face crops (200×200 px) are saved per student
2. **Training** — OpenCV's LBPH (Local Binary Pattern Histogram) recognizer trains on all saved samples
3. **Recognition** — Each webcam frame is scanned; detected faces are compared to the model
4. **Confidence** — Lower value = better match. Default threshold = **70** (tune in `face_engine.py`)

---

## ⚙️ Configuration

Open `face_engine.py` and adjust:
```python
CONFIDENCE_THRESHOLD = 70   # Lower = stricter matching
```
Open `register_page` in `main.py` and adjust:
```python
SAMPLE_TARGET = 30          # Number of face samples to capture
```

---

## 🗂️ Data Format

**students.json**
```json
{
  "1": { "name": "Arjun Sharma", "roll": "CS2024001", "registered": "2025-01-15T10:30:00" }
}
```

**attendance/2025-01-15.csv**
```
1,Arjun Sharma,09:05:32,2025-01-15
2,Priya Singh,09:07:18,2025-01-15
```

---

## 🚀 Roadmap (Phase 2 — with MySQL)

Replace `database.py` with MySQL while keeping the **same method signatures**:

```python
# Current (prototype)            # Phase 2 (MySQL)
class StudentDB:                  class StudentDB:
    def add_student(...)    →         def add_student(...)   # same API!
    def get_students(...)   →         def get_students(...)  # just different body
```

Tables to create:
```sql
CREATE TABLE students (
    id INT PRIMARY KEY, name VARCHAR(100),
    roll VARCHAR(20) UNIQUE, registered DATETIME
);

CREATE TABLE attendance (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT, name VARCHAR(100),
    time TIME, date DATE,
    FOREIGN KEY (student_id) REFERENCES students(id)
);
```

---

## 🧩 Tips for Good Recognition

- 📡 Ensure **good lighting** during registration and attendance
- 🎭 Capture samples with **slight head movements** (left/right/up/down)
- 👓 Register **with and without glasses** if applicable
- 🌡️ Re-register if accuracy drops (lighting conditions changed)

---

*Built as a collaborative school project prototype. Phase 2 will add MySQL, export to Excel, and admin login.*
