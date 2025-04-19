from pymongo import MongoClient

client = MongoClient("mongodb+srv://plusonemate:i1fSauSG2uJ9YsWQ@instant-ink.te2pr.mongodb.net/?retryWrites=true&w=majority&appName=instant-ink")
db = client['quiz_db']