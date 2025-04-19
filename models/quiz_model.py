from config import db
from bson.objectid import ObjectId

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
