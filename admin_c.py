from werkzeug.security import generate_password_hash
from pymongo import MongoClient

client = MongoClient("mongodb+srv://plusonemate:i1fSauSG2uJ9YsWQ@instant-ink.te2pr.mongodb.net/?retryWrites=true&w=majority&appName=instant-ink")
db = client['quiz_db']
db.admins.insert_one({
    'username': 'admin',
    'password': generate_password_hash('admin123')
})
