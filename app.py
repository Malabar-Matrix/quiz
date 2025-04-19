from flask import Flask, render_template, request, redirect, session, url_for
from models import quiz_model as model
from werkzeug.security import generate_password_hash, check_password_hash
import random

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Replace with a secure key in production

# ------------ ADMIN ROUTES ------------

@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        admin = model.get_admin(request.form['username'])
        if admin and check_password_hash(admin['password'], request.form['password']):
            session['admin'] = True
            return redirect('/admin/dashboard')
        else:
            return render_template('admin_login.html', error='Invalid credentials')
    return render_template('admin_login.html')

@app.route('/admin/dashboard')
def dashboard():
    if not session.get('admin'):
        return redirect('/admin')
    quizzes = list(model.db.quizzes.find())
    return render_template('admin_dashboard.html', quizzes=quizzes)

@app.route('/admin/create_quiz', methods=['GET', 'POST'])
def create_quiz():
    if not session.get('admin'):
        return redirect('/admin')
    if request.method == 'POST':
        name = request.form['name']
        desc = request.form['desc']
        quiz_id = model.create_quiz(name, desc).inserted_id
        return redirect(f'/admin/add_question/{quiz_id}')
    return render_template('create_quiz.html')

@app.route('/admin/add_question/<quiz_id>', methods=['GET', 'POST'])
def add_question(quiz_id):
    if not session.get('admin'):
        return redirect('/admin')
    quiz = model.get_quiz_by_id(quiz_id)
    if not quiz:
        return redirect('/admin/dashboard')
    if request.method == 'POST':
        question = {
            'question': request.form['question'],
            'options': [
                request.form['opt1'],
                request.form['opt2'],
                request.form['opt3'],
                request.form['opt4']
            ],
            'answer': request.form['answer']
        }
        model.add_question(quiz_id, question)
    return render_template('create_quiz.html', quiz=quiz)

@app.route('/admin/activate/<quiz_id>')
def activate_quiz(quiz_id):
    if not session.get('admin'):
        return redirect('/admin')
    model.set_active_quiz(quiz_id)
    return redirect('/admin/dashboard')

@app.route('/admin/results/<quiz_id>')
def view_results(quiz_id):
    if not session.get('admin'):
        return redirect('/admin')
    results = model.get_results(quiz_id)
    quiz = model.get_quiz_by_id(quiz_id)
    return render_template('view_results.html', results=results, quiz=quiz)

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin', None)
    return redirect('/admin')

@app.route('/admin/delete_quiz/<quiz_id>')
def delete_quiz_admin(quiz_id):
    if not session.get('admin'):
        return redirect('/admin')
    model.delete_quiz(quiz_id)
    return redirect('/admin/dashboard')


# ------------ STUDENT ROUTES ------------

@app.route('/')
def index():
    quiz = model.get_active_quiz()
    return render_template('index.html', quiz=quiz)

@app.route('/start_quiz', methods=['POST'])
def start_quiz():
    quiz = model.get_active_quiz()
    if not quiz:
        return redirect('/')
    student_name = request.form['student_name']
    session['student_name'] = student_name
    questions = quiz['questions']
    random.shuffle(questions)
    return render_template('student_quiz.html', questions=questions, quiz_id=str(quiz['_id']))

@app.route('/submit_quiz', methods=['POST'])
def submit_quiz():
    quiz_id = request.form['quiz_id']
    quiz = model.get_quiz_by_id(quiz_id)
    score = 0
    total = len(quiz['questions'])

    for q in quiz['questions']:
        user_answer = request.form.get(q['question'])
        if user_answer and user_answer.strip() == q['answer'].strip():
            score += 1

    model.save_result(quiz_id, session.get('student_name'), score)
    return render_template('result.html', score=score, total=total)



# ------------ MAIN ------------

if __name__ == '__main__':
    app.run(debug=True,host="0.0.0.0", port=5000)
