import sqlite3, os
DB = 'attendance.db'

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    if os.path.exists(DB):
        return
    conn = get_db()
    cur = conn.cursor()
    cur.execute(\"\"\"\n    CREATE TABLE students(\n        student_id INTEGER PRIMARY KEY AUTOINCREMENT,\n        name TEXT,\n        roll_no TEXT UNIQUE,\n        encoding BLOB\n    )\n    \"\"\")
    cur.execute(\"\"\"\n    CREATE TABLE attendance(\n        id INTEGER PRIMARY KEY AUTOINCREMENT,\n        student_id INTEGER,\n        date TEXT,\n        time TEXT,\n        status TEXT,\n        FOREIGN KEY(student_id) REFERENCES students(student_id)\n    )\n    \"\"\")
    conn.commit()
    conn.close()

def add_student(name, roll, encoding_bytes):
    conn = get_db()
    cur = conn.cursor()
    cur.execute('INSERT OR REPLACE INTO students(name, roll_no, encoding) VALUES(?,?,?)', (name, roll, encoding_bytes))
    conn.commit()
    conn.close()

def get_all_students():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT student_id, name, roll_no, encoding FROM students')
    rows = cur.fetchall()
    conn.close()
    return rows

from datetime import datetime
def save_attendance_for_names(names_list):
    conn = get_db()
    cur = conn.cursor()
    today = datetime.now().strftime('%Y-%m-%d')
    tim = datetime.now().strftime('%H:%M:%S')
    for name in set(names_list):
        cur.execute('SELECT student_id FROM students WHERE name=?',(name,))
        r = cur.fetchone()
        if not r:
            continue
        sid = r[0]
        # avoid duplicates for today
        cur.execute('SELECT id FROM attendance WHERE student_id=? AND date=?',(sid,today))
        if cur.fetchone():
            continue
        cur.execute('INSERT INTO attendance(student_id,date,time,status) VALUES(?,?,?,?)',(sid,today,tim,'Present'))
    conn.commit()
    conn.close()
