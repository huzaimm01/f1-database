# app/hyprace_fetcher.py

import requests
import os
from dotenv import load_dotenv

load_dotenv()

RAPIDAPI_KEY = os.getenv('RAPIDAPI_KEY')

headers = {
    "X-RapidAPI-Key": RAPIDAPI_KEY,
    "X-RapidAPI-Host": "hyprace-api.p.rapidapi.com"
}

def fetch_races_for_year(year):
    url = "https://hyprace-api.p.rapidapi.com/f1/races"
    querystring = {"year": str(year)}
    
    response = requests.get(url, headers=headers, params=querystring)

    if response.status_code != 200:
        print(f"Failed to fetch {year} races")
        return []

    data = response.json()

    races = []
    for race in data.get('response', []):
        race_info = {
            'season': int(race.get('year', year)),
            'raceRound': int(race.get('round', 0)),
            'grandPrix': race.get('race_name', 'Unknown Race'),
            'date': race.get('date', None),
            'winner': {
                'driverName': race.get('winner', {}).get('full_name', 'TBD'),
                'teamName': race.get('winner', {}).get('team', 'TBD')
            },
            'winningConstructor': race.get('winner', {}).get('team', 'TBD'),
            'laps': race.get('laps', 0),
            'raceTime': race.get('winner', {}).get('time', None),
            'fastestLap': {
                'driverName': race.get('fastest_lap', {}).get('driver', 'TBD'),
                'lapTime': race.get('fastest_lap', {}).get('time', None)
            }
        }
        races.append(race_info)

    return races

def fetch_all_latest_races():
    races_2024 = fetch_races_for_year(2024)
    races_2025 = fetch_races_for_year(2025)
    return races_2024 + races_2025
