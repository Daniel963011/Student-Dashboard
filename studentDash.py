from flask import Flask, render_template, send_file, request, redirect, url_for
import mysql.connector
import pandas as pd

app = Flask(__name__)

def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",         
        password="hazellnut", 
        database="studentDashboard"
    )

@app.route('/')
def dashboard():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.callproc('get_student_report')

    for result in cursor.stored_results():
        data = result.fetchall()

    df = pd.DataFrame(data, columns=['Name', 'Email', 'Assignment', 'Score', 'Max Score', 'Percentage'])
    conn.close()
    return render_template('student_dashboard.html', tables=[df.to_html(index=False)], titles=df.columns.values)

@app.route('/export')
def export_csv():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.callproc('get_student_report')

    for result in cursor.stored_results():
        data = result.fetchall()

    df = pd.DataFrame(data, columns=['Name', 'Email', 'Assignment', 'Score', 'Max Score', 'Percentage'])
    conn.close()
    df.to_csv('report.csv', index=False)
    return send_file('report.csv', as_attachment=True)

@app.route('/add', methods=['POST', 'GET'])
def add_entry():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        assignment = request.form['assignment']
        max_score = request.form['max_score']
        score = request.form['score']

        conn = get_connection()
        cursor = conn.cursor()

        # Insert student
        cursor.execute("INSERT INTO students (name, email) VALUES (%s, %s)", (name, email))
        student_id = cursor.lastrowid

        # Insert assignment
        cursor.execute("INSERT INTO assignments (title, max_score) VALUES (%s, %s)", (assignment, max_score))
        assignment_id = cursor.lastrowid

        # Insert grade
        cursor.execute("INSERT INTO grades (student_id, assignment_id, score) VALUES (%s, %s, %s)", (student_id, assignment_id, score))

        conn.commit()
        conn.close()

        return redirect(url_for('dashboard'))
    return render_template('add_entry.html')

@app.route('/delete')
def delete_page():
    conn = get_connection()
    cursor = conn.cursor()

    # Join tables to show full info per grade entry
    query = """
        SELECT g.id, s.name, s.email, a.title, g.score, a.max_score
        FROM grades g
        JOIN students s ON g.student_id = s.id
        JOIN assignments a ON g.assignment_id = a.id
        ORDER BY g.id;
    """
    cursor.execute(query)
    grades = cursor.fetchall()
    conn.close()

    return render_template('delete_entry.html', grades=grades)

@app.route('/delete/<int:grade_id>', methods=['POST'])
def delete_grade(grade_id):
    conn = get_connection()
    cursor = conn.cursor()

    # Delete the grade entry
    cursor.execute("DELETE FROM grades WHERE id = %s", (grade_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('delete_page'))


if __name__ == '__main__':
    app.run(debug=True)
