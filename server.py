import json
import sqlite3
from pathlib import Path
from typing import Dict, Any, List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "medai.db"
WEB_DIR = BASE_DIR / "web"
DRUGS_JSON = BASE_DIR / "drugs_uz.json"
DISEASES_JSON = BASE_DIR / "diseases_uz.json"

app = FastAPI(title="MedAI 4 Functions Final")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if WEB_DIR.exists():
    app.mount("/web", StaticFiles(directory=str(WEB_DIR), html=True), name="web")


def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def read_json(path: Path):
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def normalize(text: str) -> str:
    t = (text or "").lower().strip()
    repl = {
        "o‘": "o", "g‘": "g", "o'": "o", "g'": "g",
        "’": "", "'": "", "`": "", "ʻ": "", "‘": ""
    }
    for a, b in repl.items():
        t = t.replace(a, b)
    return " ".join(t.split())


@app.on_event("startup")
def startup():
    conn = db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS reminders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        med TEXT,
        hhmm TEXT,
        active INTEGER,
        last_sent_date TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS doses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        med TEXT,
        hhmm TEXT,
        ts TEXT,
        status TEXT
    )
    """)

    conn.commit()
    conn.close()


# =========================
# DRUG
# =========================
def get_drug(text: str):
    data = read_json(DRUGS_JSON)
    t = normalize(text)
    best = None
    best_score = 0

    for item in data.values():
        names = [item.get("name", ""), item.get("active", "")] + item.get("aliases", [])
        for n in names:
            nn = normalize(str(n))
            if not nn:
                continue

            score = 0
            if t == nn:
                score = 1000
            elif t in nn or nn in t:
                score = 700
            else:
                common = len(set(t.split()) & set(nn.split()))
                score = common * 100

            if score > best_score:
                best_score = score
                best = item

    return best if best_score >= 100 else None


def format_drug(d: dict) -> str:
    forms = ", ".join(d.get("forms", []))
    return (
        f"💊 Dori: {d.get('name', 'Noma’lum')}\n\n"
        f"Aktiv modda: {d.get('active', 'Noma’lum')}\n\n"
        f"Dori shakli: {forms or 'Noma’lum'}\n\n"
        f"Kategoriya: {d.get('category', 'Noma’lum')}\n\n"
        f"Ishlatiladi:\n{d.get('use', 'Ma’lumot yo‘q')}\n\n"
        f"Ogohlantirish:\n{d.get('warning', 'Ma’lumot yo‘q')}\n\n"
        f"Qaysi shifokor:\n{d.get('doctor', 'Terapevt')}\n\n"
        f"❗ Bu aniq tashxis emas."
    )


@app.post("/api/pill/identify")
def pill(payload: Dict[str, Any]):
    text = str(payload.get("text", "")).strip()
    if not text:
        return {"answer": "Dori nomi yozilmadi."}

    drug = get_drug(text)
    if drug:
        return {"answer": format_drug(drug)}

    return {"answer": "Bu dori bazada topilmadi.\n\n❗ Bu aniq tashxis emas."}


# =========================
# SYMPTOM
# =========================
def score_alias(text: str, alias: str) -> int:
    text_n = normalize(text)
    alias_n = normalize(alias)
    if not alias_n:
        return 0
    if text_n == alias_n:
        return 100
    if alias_n in text_n:
        return 70
    return len(set(text_n.split()) & set(alias_n.split())) * 10


def find_best_disease(text: str):
    data = read_json(DISEASES_JSON)
    best = None
    best_score = 0

    for disease in data.values():
        score = 0
        for alias in disease.get("aliases", []):
            score += score_alias(text, alias)

        if score > best_score:
            best_score = score
            best = disease

    return best if best_score >= 10 else None


@app.post("/api/symptom/questions")
def symptom_questions(payload: Dict[str, Any]):
    text = str(payload.get("text", "")).strip()
    disease = find_best_disease(text)

    if disease:
        return {
            "ok": True,
            "title": disease.get("simple_name", "Simptom"),
            "medical_name": disease.get("simple_name", "Simptom"),
            "questions": disease.get("questions", [])[:5],
            "doctor": disease.get("doctor", "Terapevt")
        }

    return {
        "ok": True,
        "title": "Aniqlanmagan holat",
        "medical_name": "Umumiy simptomatik holat",
        "questions": [
            "Qachondan beri davom etyapti?",
            "Og‘riq kuchlimi?",
            "Boshqa belgilar bormi?"
        ],
        "doctor": "Terapevt"
    }


@app.post("/api/symptom/analyze")
def symptom_analyze(payload: Dict[str, Any]):
    complaint = str(payload.get("complaint", "") or payload.get("text", "")).strip()
    answers = payload.get("answers", [])

    if isinstance(answers, dict):
        answers = list(answers.values())
    elif not isinstance(answers, list):
        answers = []

    answers = [str(x).strip() if x is not None else "" for x in answers]
    disease = find_best_disease(complaint)

    if not disease:
        return {"ok": True, "result": "Kasallik bazada topilmadi.\n\n❗ Bu aniq tashxis emas."}

    diagnosis = disease.get("simple_name", "Aniqlanmagan holat")
    doctor = disease.get("doctor", "Terapevt")
    advice = disease.get("home_advice", [])
    danger = disease.get("danger_signs", [])

    result = f"1. Ehtimoliy holat:\n{diagnosis}\n\n"

    if answers:
        result += "2. Sizning javoblaringiz:\n"
        for i, ans in enumerate(answers, start=1):
            result += f"- {i}-javob: {ans if ans else 'Javob berilmadi'}\n"
        result += "\n"

    result += "3. Tavsiya:\n"
    for a in advice:
        result += f"- {a}\n"

    result += f"\n4. Qaysi shifokor:\n{doctor}\n\n"
    result += "5. Xavfli belgilar:\n"
    for d in danger:
        result += f"- {d}\n"

    result += "\n❗ Bu aniq tashxis emas."
    return {"ok": True, "result": result}


# =========================
# REMINDER + STATS
# =========================
@app.post("/api/reminder/add")
def add_reminder(payload: Dict[str, Any]):
    user_id = int(payload.get("user_id", 0) or 0)
    med = str(payload.get("med", "")).strip()
    hhmm = str(payload.get("hhmm", "") or payload.get("time", "")).strip()

    if not user_id:
        return {"ok": False, "error": "user_id topilmadi"}
    if not med:
        return {"ok": False, "error": "Dori nomi kiritilmagan"}
    if not hhmm:
        return {"ok": False, "error": "Vaqt kiritilmagan"}

    conn = db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO reminders (user_id, med, hhmm, active, last_sent_date)
        VALUES (?, ?, ?, 1, '')
    """, (user_id, med, hhmm))
    conn.commit()

    rows = cur.execute("""
        SELECT id, user_id, med, hhmm, active, last_sent_date
        FROM reminders
        WHERE user_id=?
        ORDER BY id DESC
    """, (user_id,)).fetchall()

    conn.close()
    return {"ok": True, "reminders": [dict(r) for r in rows]}


@app.post("/api/stats")
def stats(payload: Dict[str, Any]):
    user_id = int(payload.get("user_id", 0) or 0)
    if not user_id:
        return {"ok": True, "took": 0, "late_took": 0, "missed": 0, "adherence_percent": 0}

    conn = db()
    cur = conn.cursor()

    took = cur.execute("SELECT COUNT(*) AS c FROM doses WHERE user_id=? AND status='took'", (user_id,)).fetchone()["c"]
    late_took = cur.execute("SELECT COUNT(*) AS c FROM doses WHERE user_id=? AND status='late_took'", (user_id,)).fetchone()["c"]
    missed = cur.execute("SELECT COUNT(*) AS c FROM doses WHERE user_id=? AND status='missed'", (user_id,)).fetchone()["c"]
    conn.close()

    total = took + late_took + missed
    adherence_percent = round(((took + late_took) / total) * 100, 1) if total else 0

    return {
        "ok": True,
        "took": took,
        "late_took": late_took,
        "missed": missed,
        "adherence_percent": adherence_percent
    }


@app.get("/health")
def health():
    conn = db()
    cur = conn.cursor()
    reminders_count = cur.execute("SELECT COUNT(*) AS c FROM reminders").fetchone()["c"]
    doses_count = cur.execute("SELECT COUNT(*) AS c FROM doses").fetchone()["c"]
    conn.close()

    return {
        "ok": True,
        "version": "MEDAI_4FUNC_FINAL_V1",
        "drugs_count": len(read_json(DRUGS_JSON)),
        "diseases_count": len(read_json(DISEASES_JSON)),
        "reminders_count": reminders_count,
        "doses_count": doses_count
    }
