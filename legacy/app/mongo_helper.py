from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

mongo_uri = os.getenv('MONGO_URI')
client = MongoClient(mongo_uri)
db = client['f1_database']
races_collection = db['races']

def get_existing_races():
    return list(races_collection.find({}, {'season': 1, 'grandPrix': 1, '_id': 0}))

def insert_race(race_data):
    races_collection.insert_one(race_data)