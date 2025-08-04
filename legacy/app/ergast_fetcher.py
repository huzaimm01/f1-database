# app/ergast_fetcher.py

import requests

def fetch_races_for_season(season):
    url = f"https://ergast.com/api/f1/{season}/results.json?limit=1000"
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Failed to fetch {season} season races")
        return []
    
    data = response.json()
    races = data['MRData']['RaceTable']['Races']
    race_list = []

    for race in races:
        race_info = {
            'season': int(race['season']),
            'grandPrix': race['raceName'],
            'date': race['date'],
            'winner': {
                'driverName': f"{race['Results'][0]['Driver']['givenName']} {race['Results'][0]['Driver']['familyName']}",
                'teamName': race['Results'][0]['Constructor']['name']
            },
            'winningConstructor': race['Results'][0]['Constructor']['name'],
            'laps': int(race['Results'][0]['laps']),
            'raceTime': race['Results'][0]['Time']['time'] if 'Time' in race['Results'][0] else None,
            'fastestLap': {
                'driverName': race['Results'][0]['Driver']['familyName'],
                'lapTime': race['Results'][0]['FastestLap']['Time']['time'] if 'FastestLap' in race['Results'][0] else None
            }
        }
        race_list.append(race_info)

    return race_list

def fetch_all_latest_races():
    # Fetch 2024 and 2025 races
    races_2024 = fetch_races_for_season(2024)
    races_2025 = fetch_races_for_season(2025)
    return races_2024 + races_2025
