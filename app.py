from flask import Flask, render_template, request, redirect, url_for, flash, send_file
import os, sqlite3, io
from werkzeug.utils import secure_filename
import face_recognition
import numpy as np
from datetime import datetime
from models import init_db, get_db, add_student, get_all_students, save_attendance_for_names

UPLOAD_FOLDER = 'uploads'
STUDENTS_FOLDER = 'students'
ALLOWED_EXT = {'png','jpg','jpeg'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['STUDENTS_FOLDER'] = STUDENTS_FOLDER
app.secret_key = 'dev-key'

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
if not os.path.exists(STUDENTS_FOLDER):
    os.makedirs(STUDENTS_FOLDER)

@app.before_first_request
def setup():
    init_db()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.',1)[1].lower() in ALLOWED_EXT

@app.route('/')
def index():
    students = get_all_students()
    return render_template('index.html', students=students)

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        name = request.form['name'].strip()
        roll = request.form['roll'].strip()
        file = request.files.get('image')
        if not name or not roll or not file:
            flash('All fields required', 'danger')
            return redirect(request.url)
        filename = secure_filename(f\"{roll}_{file.filename}\")
        filepath = os.path.join(app.config['STUDENTS_FOLDER'], filename)
        file.save(filepath)
        # create encoding
        image = face_recognition.load_image_file(filepath)
        encodings = face_recognition.face_encodings(image)
        if not encodings:
            flash('No face found in image', 'danger')
            os.remove(filepath)
            return redirect(request.url)
        encoding = encodings[0].tobytes()
        add_student(name, roll, encoding)
        flash('Student registered', 'success')
        return redirect(url_for('index'))
    return render_template('register.html')

@app.route('/upload', methods=['GET','POST'])
def upload():
    if request.method == 'POST':
        file = request.files.get('image')
        if not file or not allowed_file(file.filename):
            flash('Please upload an image (jpg/png)', 'danger')
            return redirect(request.url)
        filename = secure_filename(file.filename)
        path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(path)
        # process attendance
        known = get_all_students()
        known_enc = [np.frombuffer(row['encoding'], dtype=np.float64) for row in known]
        known_names = [row['name'] for row in known]
        img = face_recognition.load_image_file(path)
        locations = face_recognition.face_locations(img)
        encs = face_recognition.face_encodings(img, locations)
        matched = []
        for enc in encs:
            if not known_enc:
                continue
            distances = face_recognition.face_distance(known_enc, enc)
            idx = int(np.argmin(distances))
            if distances[idx] < 0.55:
                matched.append(known_names[idx])
        save_attendance_for_names(matched)
        flash(f'Attendance processed. Present: {", ".join(sorted(set(matched))) if matched else "None"}', 'info')
        return redirect(url_for('index'))
    return render_template('upload.html')

@app.route('/reports')
def reports():
    conn = get_db()
    cur = conn.cursor()
    cur.execute(\"SELECT a.id, s.roll_no, s.name, a.date, a.time, a.status FROM attendance a JOIN students s ON a.student_id = s.student_id ORDER BY a.date DESC, a.time DESC\")
    rows = cur.fetchall()
    return render_template('reports.html', rows=rows)

if __name__ == '__main__':
    app.run(debug=True)
