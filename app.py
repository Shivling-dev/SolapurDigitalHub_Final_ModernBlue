from flask import Flask, render_template, request, redirect, session, flash, send_file
from werkzeug.security import generate_password_hash, check_password_hash
from db import get_connection
import random, csv, io
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

app = Flask(__name__)
app.secret_key = 'replace_this_with_a_strong_secret'

# ----------------------- Helper Functions -----------------------
def get_student_by_email(email):
    conn = get_connection()
    if not conn:
        print("⚠️ DB failed in get_student_by_email")
        return None
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM students WHERE email=%s', (email,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return user

# ----------------------- Routes -----------------------
@app.route('/')
def index():
    return render_template('index.html')

# -------- Student Registration --------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        dob = request.form.get('dob')

        if get_student_by_email(email):
            flash('Email already registered', 'danger')
            return redirect('/register')

        hashed = generate_password_hash(password)
        conn = get_connection()
        if not conn:
            flash('Database connection failed!', 'danger')
            return redirect('/register')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO students (name, email, password, dob) VALUES (%s,%s,%s,%s)',
                       (name, email, hashed, dob))
        conn.commit()
        cursor.close()
        conn.close()
        flash('Registration successful. Please login.', 'success')
        return redirect('/login')
    return render_template('register.html')

# -------- Student Login --------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = get_student_by_email(email)
        if user and check_password_hash(user['password'], password):
            session['student_id'] = user['student_id']
            session['student_name'] = user['name']
            return redirect('/dashboard')
        flash('Invalid credentials', 'danger')
        return redirect('/login')
    return render_template('login.html')

# -------- Student Dashboard --------
@app.route('/dashboard')
def dashboard():
    if 'student_id' not in session:
        return redirect('/login')
    return render_template('student_dashboard.html')

# -------- Student: Upcoming Exams --------
@app.route('/exam')
def exam():
    if 'student_id' not in session:
        return redirect('/login')
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM exams WHERE exam_date >= CURDATE() ORDER BY exam_date ASC')
    upcoming_exams = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('exam.html', exams=upcoming_exams)

# -------- Student: Start Exam + AI Feedback --------
@app.route('/exam/start/<int:exam_id>', methods=['GET', 'POST'])
def start_exam(exam_id):
    if 'student_id' not in session:
        return redirect('/login')
    
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    # sirf us exam ke questions fetch
    cursor.execute('SELECT * FROM questions WHERE exam_id=%s', (exam_id,))
    questions = cursor.fetchall()
    cursor.close()
    conn.close()
    
    if request.method == 'POST':
        total = len(questions)
        score = 0
        feedback = []

        for q in questions:
            ans = request.form.get(f'ans_{q["q_id"]}')
            correct = q['correct_ans'].strip()
            is_correct = ans.strip() == correct if ans else False
            feedback.append({
                'question': q['question'],
                'your_answer': ans,
                'correct_answer': correct,
                'is_correct': is_correct
            })
            if is_correct:
                score += 1
        
        # Save result
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO results (student_id, exam_id, score, total, taken_at) VALUES (%s,%s,%s,%s,NOW())',
            (session['student_id'], exam_id, score, total)
        )
        conn.commit()
        cursor.close()
        conn.close()

        return render_template('result.html', score=score, total=total, feedback=feedback)

    random.shuffle(questions)
    return render_template('exam_questions.html', questions=questions, exam_id=exam_id)

# -------- Admin Login --------
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_connection()
        if not conn:
            flash('Database connection failed!', 'danger')
            return redirect('/admin/login')

        cursor = conn.cursor(dictionary=True, buffered=True)
        cursor.execute('SELECT * FROM admin WHERE username=%s', (username,))
        admin = cursor.fetchone()
        cursor.close()
        conn.close()

        if admin and (check_password_hash(admin['password'], password) or admin['password'] == password):
            session['admin'] = admin['username']
            return redirect('/admin/dashboard')

        flash('Invalid admin credentials', 'danger')
        return redirect('/admin/login')
    return render_template('admin_login.html')

# -------- Admin Dashboard --------
@app.route('/admin/dashboard')
def admin_dashboard():
    if 'admin' not in session:
        return redirect('/admin/login')
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM students')
    total_students = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM questions')
    total_q = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM exams')
    total_exams = cursor.fetchone()[0]
    cursor.execute('SELECT score, COUNT(*) FROM results GROUP BY score')
    score_data = cursor.fetchall()
    cursor.close()
    conn.close()

    labels = [str(row[0]) for row in score_data]
    values = [row[1] for row in score_data]
    return render_template('admin_dashboard.html', total_students=total_students,
                           total_q=total_q, total_exams=total_exams, labels=labels, values=values)

# -------- Admin: Manage Exams --------
@app.route('/admin/exams')
def admin_exams():
    if 'admin' not in session:
        return redirect('/admin/login')
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM exams ORDER BY exam_date ASC')
    exams = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('admin_exams.html', exams=exams)

@app.route('/admin/exams/add', methods=['GET','POST'])
def admin_add_exam():
    if 'admin' not in session:
        return redirect('/admin/login')
    if request.method == 'POST':
        title = request.form['title']
        description = request.form.get('description')
        exam_date = request.form['exam_date']
        total_questions = request.form['total_questions']
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO exams (title, description, exam_date, total_questions) VALUES (%s,%s,%s,%s)',
                       (title, description, exam_date, total_questions))
        conn.commit()
        cursor.close()
        conn.close()
        flash('Exam added successfully!', 'success')
        return redirect('/admin/exams')
    return render_template('admin_add_exam.html')

@app.route('/admin/exams/delete/<int:exam_id>')
def admin_delete_exam(exam_id):
    if 'admin' not in session:
        return redirect('/admin/login')
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM exams WHERE exam_id=%s', (exam_id,))
    conn.commit()
    cursor.close()
    conn.close()
    flash('Exam deleted successfully!', 'success')
    return redirect('/admin/exams')

# -------- Add Question to Specific Exam --------
@app.route('/admin/add_question', methods=['GET','POST'])
def admin_add_question():
    if 'admin' not in session:
        return redirect('/admin/login')
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM exams ORDER BY exam_date ASC')
    exams = cursor.fetchall()
    cursor.close()
    conn.close()

    if request.method == 'POST':
        exam_id = request.form['exam_id']
        question = request.form['question']
        option1 = request.form['option1']
        option2 = request.form['option2']
        option3 = request.form.get('option3')
        option4 = request.form.get('option4')
        correct_ans = request.form['correct_ans']
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO questions (exam_id, question, option1, option2, option3, option4, correct_ans) VALUES (%s,%s,%s,%s,%s,%s,%s)',
                       (exam_id, question, option1, option2, option3, option4, correct_ans))
        conn.commit()
        cursor.close()
        conn.close()
        flash('Question added', 'success')
        return redirect('/admin/add_question')

    return render_template('add_question.html', exams=exams)

# -------- View & Export Results --------
@app.route('/admin/view_results')
def admin_view_results():
    if 'admin' not in session:
        return redirect('/admin/login')
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT r.*, s.name, s.email FROM results r JOIN students s ON r.student_id = s.student_id ORDER BY r.taken_at DESC')
    res = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('admin_view_results.html', results=res)

@app.route('/admin/export_results')
def admin_export_results():
    if 'admin' not in session:
        return redirect('/admin/login')
    fmt = request.args.get('format', 'csv').lower()
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT r.*, s.name, s.email FROM results r JOIN students s ON r.student_id = s.student_id ORDER BY r.taken_at DESC')
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    if fmt == 'csv':
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['#','student_id','name','email','score','total','taken_at'])
        for i, r in enumerate(rows, start=1):
            writer.writerow([i, r['student_id'], r.get('name'), r.get('email'), r.get('score'), r.get('total'), r.get('taken_at')])
        output.seek(0)
        mem = io.BytesIO()
        mem.write(output.getvalue().encode('utf-8'))
        mem.seek(0)
        filename = f'results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        return send_file(mem, mimetype='text/csv', download_name=filename, as_attachment=True)
    elif fmt == 'pdf':
        mem = io.BytesIO()
        c = canvas.Canvas(mem, pagesize=letter)
        width, height = letter
        y = height - 40
        c.setFont('Helvetica-Bold', 14)
        c.drawString(40, y, 'Solapur Digital Hub - Results Export')
        y -= 30
        c.setFont('Helvetica', 10)
        for i, r in enumerate(rows, start=1):
            line = f"{i}. {r.get('name')} ({r.get('email')}) - Score: {r.get('score')}/{r.get('total')} - {r.get('taken_at')}"
            c.drawString(40, y, line[:100])
            y -= 14
            if y < 60:
                c.showPage()
                y = height - 40
        c.save()
        mem.seek(0)
        filename = f'results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
        return send_file(mem, mimetype='application/pdf', download_name=filename, as_attachment=True)
    else:
        flash('Invalid export format', 'danger')
        return redirect('/admin/view_results')

# -------- ABOUT --------
@app.route('/about')
def about_page():
    return render_template('about.html')

# -------- Admin: View Students --------
@app.route('/admin/students')
def admin_students():
    if 'admin' not in session:
        return redirect('/admin/login')
    
    conn = get_connection()
    if not conn:
        flash('Database connection failed!', 'danger')
        return redirect('/admin/dashboard')
    
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM students ORDER BY created_at DESC')
    students = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return render_template('admin_students.html', students=students)

# -------- Logout --------
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# ----------------------- Run App -----------------------
if __name__ == '__main__':
    app.run(debug=True)
