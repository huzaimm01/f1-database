import pandas as pd
from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()
mongo_uri = os.getenv('MONGO_URI')
client = MongoClient(mongo_uri)
db = client['f1_database']
races_collection = db['races']

winners_df = pd.read_csv('f1_data/winners.csv')
fastest_laps_df = pd.read_csv('f1_data/fastest_laps_updated.csv')

winners_df.columns = winners_df.columns.str.strip()
fastest_laps_df.columns = fastest_laps_df.columns.str.strip()

winners_df['year'] = pd.to_datetime(winners_df['Date']).dt.year
fastest_laps_df['year'] = fastest_laps_df['year']

merged_df = pd.merge(
    winners_df,
    fastest_laps_df,
    how='left',
    left_on=['Grand Prix', 'year'],
    right_on=['Grand Prix', 'year'],
    suffixes=('_winner', '_fastestlap')
)

for _, row in merged_df.iterrows():
    race_data = {
        'season': int(row['year']),
        'grandPrix': row['Grand Prix'],
        'date': row['Date'],
        'winner': {
            'driverName': row['Winner'],
            'teamName': row['Car_winner']
        },
        'winningConstructor': row['Car_winner'],
        'laps': row['Laps'],
        'raceTime': row['Time_winner'] if pd.notna(row['Time_winner']) else None,
        'fastestLap': {
            'driverName': row['Driver'] if pd.notna(row['Driver']) else None,
            'lapTime': row['Time_fastestlap'] if pd.notna(row['Time_fastestlap']) else None
        }
    }
    races_collection.insert_one(race_data)
