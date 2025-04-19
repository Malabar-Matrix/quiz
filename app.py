from flask import Flask, render_template, request, redirect, session, url_for
from werkzeug.security import  check_password_hash
import random
import os
from pymongo import MongoClient
from bson.objectid import ObjectId
from flask_vercel import Vercel


app = Flask(__name__)
app.secret_key = 'gedebdfdvf'  # Replace with a secure key in production

app = Vercel(app) 

client = MongoClient("mongodb+srv://plusonemate:i1fSauSG2uJ9YsWQ@instant-ink.te2pr.mongodb.net/?retryWrites=true&w=majority&appName=instant-ink")
db = client['quiz_db']
# ------------ ADMIN ROUTES ------------

@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        admin = request.form['username']
        admin = db.admins.find_one({'username': admin})
        print(admin)
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
    quizzes = list(db.quizzes.find())
    return render_template('admin_dashboard.html', quizzes=quizzes)

@app.route('/admin/create_quiz', methods=['GET', 'POST'])
def create_quiz():
    if not session.get('admin'):
        return redirect('/admin')
    if request.method == 'POST':
        name = request.form['name']
        desc = request.form['desc']
        quiz_id = create_quiz(name, desc).inserted_id
        return redirect(f'/admin/edit_quiz/{quiz_id}')
    return render_template('create_quiz.html')

@app.route('/admin/edit_quiz/<quiz_id>', methods=['GET', 'POST'])
def edit_quiz(quiz_id):
    if not session.get('admin'):
        return redirect('/admin')
    quiz = get_quiz_by_id(quiz_id)
    if not quiz:
        return redirect('/admin/dashboard')
    return render_template('edit_quiz.html', quiz=quiz)

@app.route('/admin/update_quiz_info/<quiz_id>', methods=['POST'])
def update_quiz_info(quiz_id):
    if not session.get('admin'):
        return redirect('/admin')
    name = request.form['name']
    desc = request.form['desc']
    update_quiz_details(quiz_id, name, desc)
    return redirect(f'/admin/edit_quiz/{quiz_id}')

@app.route('/admin/delete_question/<quiz_id>/<name>', methods=['POST'])
def delete_question(quiz_id, name):
    if not session.get('admin'):
        return redirect('/admin')
    delete_question(quiz_id,name)
    return redirect(f'/admin/edit_quiz/{quiz_id}')

@app.route('/admin/add_question/<quiz_id>', methods=['GET', 'POST'])
def add_question(quiz_id):
    if not session.get('admin'):
        return redirect('/admin')
    quiz = get_quiz_by_id(quiz_id)
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
        add_question(quiz_id, question)
        return redirect(f'/admin/edit_quiz/{quiz_id}')

@app.route('/admin/activate/<quiz_id>')
def activate_quiz(quiz_id):
    if not session.get('admin'):
        return redirect('/admin')
    set_active_quiz(quiz_id)
    return redirect('/admin/dashboard')

@app.route('/admin/deactivate/<quiz_id>')
def deactivate_quiz(quiz_id):
    if not session.get('admin'):
        return redirect('/admin')
    set_quiz_inactive(quiz_id)
    return redirect('/admin/dashboard')

@app.route('/admin/results/<quiz_id>')
def view_results(quiz_id):
    if not session.get('admin'):
        return redirect('/admin')
    results = get_results(quiz_id)
    results.sort(key=lambda x: x['score'], reverse=True)
    quiz = get_quiz_by_id(quiz_id)
    return render_template('view_results.html', results=results, quiz=quiz)

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin', None)
    return redirect('/admin')

@app.route('/admin/delete_quiz/<quiz_id>')
def delete_quiz_admin(quiz_id):
    if not session.get('admin'):
        return redirect('/admin')
    delete_quiz(quiz_id)
    return redirect('/admin/dashboard')


# ------------ STUDENT ROUTES ------------

@app.route('/')
def index():
    quiz = get_active_quiz()
    return render_template('index.html', quiz=quiz)

@app.route('/start_quiz', methods=['POST'])
def start_quiz():
    quiz = get_active_quiz()
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
    quiz = get_quiz_by_id(quiz_id)
    score = 0
    total = len(quiz['questions'])

    for q in quiz['questions']:
        user_answer = request.form.get(q['question'])
        if user_answer and user_answer.strip() == q['answer'].strip():
            score += 1

    save_result(quiz_id, session.get('student_name'), score)
    return render_template('result.html', score=score, total=total)


def get_admin(username):
    return db.admins.find_one({'username': username})

def create_quiz(name, desc):
    return db.quizzes.insert_one({
        'name': name,
        'description': desc,
        'active': False,
        'questions': []
    })

def add_question(quiz_id, question_data):
    db.quizzes.update_one(
        {'_id': ObjectId(quiz_id)},
        {'$push': {'questions': question_data}}
    )

def set_active_quiz(quiz_id):
    db.quizzes.update_many({}, {'$set': {'active': False}})
    db.quizzes.update_one({'_id': ObjectId(quiz_id)}, {'$set': {'active': True}})

def set_quiz_inactive(quiz_id):
    db.quizzes.update_one({'_id': ObjectId(quiz_id)}, {'$set': {'active': False}})

def get_active_quiz():
    return db.quizzes.find_one({'active': True})

def get_quiz_by_id(quiz_id):
    return db.quizzes.find_one({'_id': ObjectId(quiz_id)})

def save_result(quiz_id, name, score):
    db.results.insert_one({
        'quiz_id': ObjectId(quiz_id),
        'student_name': name,
        'score': score
    })

def get_results(quiz_id):
    return list(db.results.find({'quiz_id': ObjectId(quiz_id)}))

def delete_quiz(quiz_id):
    db.quizzes.delete_one({'_id': ObjectId(quiz_id)})
    db.results.delete_many({'quiz_id': ObjectId(quiz_id)})


def update_quiz_details(quiz_id, name, desc):
    db.quizzes.update_one(
        {'_id': ObjectId(quiz_id)},
        {'$set': {'name': name, 'description': desc}}
    ) 

def delete_question(quiz_id, question_name):
    db.quizzes.update_one(
        {'_id': ObjectId(quiz_id)},
        {'$pull': {'questions': {'question': question_name}}}
    )



