from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_mysqldb import MySQL
from flask_bcrypt import Bcrypt
import MySQLdb.cursors
import os
from dotenv import load_dotenv
import json
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from flask import send_file

from ml_models.predict_model import predict_admission
from ml_models.eligibility_check import check_eligibility

load_dotenv()

app = Flask(__name__)
bcrypt = Bcrypt(app)

app.secret_key = os.getenv("SECRET_KEY", "mysecretkey")

# MySQL config
app.config["MYSQL_HOST"] = os.getenv("MYSQL_HOST")
app.config["MYSQL_USER"] = os.getenv("MYSQL_USER")
app.config["MYSQL_PASSWORD"] = os.getenv("MYSQL_PASSWORD")
app.config["MYSQL_DB"] = os.getenv("MYSQL_DB")
app.config["MYSQL_CURSORCLASS"] = "DictCursor"

mysql = MySQL(app)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/admission_info')
def admission_info():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM admission_timeline ORDER BY start_date ASC")
    timeline = cursor.fetchall()
    cursor.close()
    return render_template('admission_info.html', timeline=timeline)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if not (name and email and password and confirm_password):
            flash('All fields are required!', 'error')
            return render_template('register.html')

        if password != confirm_password:
            flash('Passwords do not match!', 'error')
            return render_template('register.html')

        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM students WHERE email=%s", (email,))
        existing_user = cursor.fetchone()

        if existing_user:
            flash('Email already registered. Please log in.', 'error')
            return redirect(url_for('login'))

        hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')
        cursor.execute("INSERT INTO students (name, email, password) VALUES (%s, %s, %s)", (name, email, hashed_pw))
        mysql.connection.commit()
        cursor.close()
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM students WHERE email=%s", (email,))
        user = cursor.fetchone()
        cursor.close()

        if user and bcrypt.check_password_hash(user['password'], password):
            session['student_id'] = user['id']
            session['student_name'] = user['name']
            session['email'] = user['email']
            return redirect(url_for('predictor'))
        else:
            flash('Invalid email or password.', 'error')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('login'))

@app.route('/predictor', methods=['GET', 'POST'])
def predictor():
    if 'student_id' not in session:
        flash('Please log in to check eligibility.', 'error')
        return redirect(url_for('login'))
    student_id = session.get('student_id')
    if request.method == 'POST':
        name = session.get('student_name')
        physics = float(request.form['physics'])
        chemistry = float(request.form['chemistry'])
        math = float(request.form['math'])
        category = request.form['category']
        percentile = float(request.form['percentile'])

        #Check eligibility
        eligible, message = check_eligibility(physics, chemistry, math, category)

        if not eligible:
            return render_template('predictor.html', message=message, category='error')

        cursor = mysql.connection.cursor()
        pcm_percentage = (physics + chemistry + math) / 3

        # cursor.execute(
        #     "INSERT INTO students (name, category, pcm_percentage, percentile) VALUES (%s, %s, %s, %s)",
        #     (name, category, pcm_percentage, percentile)
        # )
        cursor.execute("""
            UPDATE students 
            SET category=%s, pcm_percentage=%s, percentile=%s 
            WHERE id=%s
        """, (category, pcm_percentage, percentile, student_id))
        mysql.connection.commit()

        results = predict_admission(percentile, category) 
        if not isinstance(results, list):
            results = results.to_dict(orient='records') 
        # results_df = predict_admission(percentile, category)
        # results = results_df.to_dict(orient='records')
        import json
        cursor.execute(
            "INSERT INTO predictions (student_id, input_pcm, input_percentile, input_category, prediction_json) VALUES (%s, %s, %s, %s, %s)",
            (student_id, pcm_percentage, percentile, category, json.dumps(results))
        )
        mysql.connection.commit()
        cursor.close()

        return render_template('predicted_colleges.html', name=name, percentile=percentile, category=category, predictions=results)

    return render_template('predictor.html')
   
@app.route('/save_colleges', methods=['POST'])
def save_colleges():
    if 'student_id' not in session:
        return jsonify({"status": "error", "message": "Not logged in"})

    data = request.get_json()
    student_id = session['student_id']
    colleges = data.get('colleges', [])

    cursor = mysql.connection.cursor()

    for college in colleges:
        institute = college['institute']
        department = college.get('department', '-')
        best_chance = float(college.get('best_chance', 0))

        cursor.execute("SELECT id FROM colleges WHERE institute_name=%s AND department=%s", (institute, department))
        result = cursor.fetchone()

        if result:
            college_id = result['id']
        else:
            cursor.execute(
                "INSERT INTO colleges (institute_name, department, best_chance) VALUES (%s, %s, %s)",
                (institute, department, best_chance)
            )
            mysql.connection.commit()
            college_id = cursor.lastrowid

        cursor.execute(
            "INSERT IGNORE INTO student_selections (student_id, college_id) VALUES (%s, %s)",
            (student_id, college_id)
        )

    mysql.connection.commit()
    cursor.close()

    return jsonify({"status": "success", "message": "Colleges saved successfully!"})

@app.route('/my_list')
def my_list():
    if 'student_id' not in session:
        flash('Please log in to view your list.', 'error')
        return redirect(url_for('login'))

    student_id = session['student_id']
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("""
        SELECT c.institute_name, c.department, c.best_chance
        FROM student_selections ss
        JOIN colleges c ON ss.college_id = c.id
        WHERE ss.student_id = %s
    """, (student_id,))
    colleges = cursor.fetchall()
    cursor.close()
    return render_template('my_list.html', colleges=colleges)

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM admin WHERE username=%s", (username,))
        admin = cursor.fetchone()
        cursor.close()

        if admin and bcrypt.check_password_hash(admin['password'], password):
            session['admin_id'] = admin['id']
            session['admin_username'] = admin['username']
            flash(f'Welcome, {admin["username"]}!', 'success')
            return redirect(url_for('admission_timeline'))
        else:
            flash('Invalid username or password', 'error')

    return render_template('admin/admin_login.html')

@app.route('/admin/admission_timeline')
def admission_timeline():
    if 'admin_id' not in session:
        flash('Please log in as admin.', 'error')
        return redirect(url_for('admin_login'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM admission_timeline ORDER BY start_date ASC")
    timelines = cursor.fetchall()
    cursor.close()

    return render_template('admin/admin_admission_timeline.html', timelines=timelines)

@app.route('/admin/add_timeline', methods=['POST'])
def add_timeline():
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))

    process_name = request.form['process_name']
    start_date = request.form['start_date']
    end_date = request.form['end_date']
    description = request.form['description']

    cursor = mysql.connection.cursor()
    cursor.execute("""
        INSERT INTO admission_timeline (process_name, start_date, end_date, description)
        VALUES (%s, %s, %s, %s)
    """, (process_name, start_date, end_date, description))
    mysql.connection.commit()
    cursor.close()
    return redirect(url_for('admission_timeline'))

@app.route('/admin/edit_timeline/<int:id>', methods=['POST'])
def edit_timeline(id):
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))

    process_name = request.form['process_name']
    start_date = request.form['start_date']
    end_date = request.form['end_date']
    description = request.form['description']

    cursor = mysql.connection.cursor()
    cursor.execute("""
        UPDATE admission_timeline
        SET process_name=%s, start_date=%s, end_date=%s, description=%s
        WHERE id=%s
    """, (process_name, start_date, end_date, description, id))
    mysql.connection.commit()
    cursor.close()

    flash('Admission Timeline updated successfully!', 'success')
    return redirect(url_for('admission_timeline'))

@app.route('/admin/delete_timeline/<int:id>', methods=['POST'])
def delete_timeline(id):
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))

    cursor = mysql.connection.cursor()
    cursor.execute("DELETE FROM admission_timeline WHERE id=%s", (id,))
    mysql.connection.commit()
    cursor.close()

    flash('Admission Timeline deleted successfully!', 'success')
    return redirect(url_for('admission_timeline'))

@app.route('/admin/students')
def admin_students():
    if 'admin_id' not in session:
        flash('Please log in as admin.', 'error')
        return redirect(url_for('admin_login'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT id, name, email, category, pcm_percentage, percentile FROM students ORDER BY id ASC")
    students = cursor.fetchall()
    cursor.close()

    return render_template('admin/admin_students.html', students=students)

@app.route('/admin/edit_student/<int:id>', methods=['POST'])
def edit_student(id):
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))

    name = request.form['name']
    email = request.form['email']
    category = request.form['category']
    pcm_percentage = request.form['pcm_percentage']
    percentile = request.form['percentile']

    cursor = mysql.connection.cursor()
    cursor.execute("""
        UPDATE students
        SET name=%s, email=%s, category=%s, pcm_percentage=%s, percentile=%s
        WHERE id=%s
    """, (name, email, category, pcm_percentage, percentile, id))
    mysql.connection.commit()
    cursor.close()

    flash('Student details updated successfully!', 'success')
    return redirect(url_for('admin_students'))

@app.route('/admin/delete_student/<int:id>', methods=['POST'])
def delete_student(id):
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))

    cursor = mysql.connection.cursor()
    cursor.execute("DELETE FROM students WHERE id=%s", (id,))
    mysql.connection.commit()
    cursor.close()

    flash('Student record deleted successfully!', 'success')
    return redirect(url_for('admin_students'))

@app.route('/admin/statistics')
def admin_statistics():
    if 'admin_id' not in session:
        flash('Please log in as admin.', 'error')
        return redirect(url_for('admin_login'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("""
        SELECT 
            c.institute_name, 
            c.department, 
            COUNT(ss.student_id) AS total_students
        FROM student_selections ss
        JOIN colleges c ON ss.college_id = c.id
        GROUP BY c.institute_name, c.department
        ORDER BY total_students DESC;
    """)
    summary = cursor.fetchall()
    cursor.close()

    return render_template('admin/admin_statistics.html', summary=summary)

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_id', None)
    session.pop('admin_username', None)
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('admin_login'))

if __name__ == "__main__":
    app.run(debug=True)
