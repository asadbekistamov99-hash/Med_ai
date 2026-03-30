import sqlite3

conn = sqlite3.connect("medai.db")
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

print("Database yaratildi!")
