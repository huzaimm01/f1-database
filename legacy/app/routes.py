# app/routes.py

from flask import Blueprint, render_template, request, redirect, url_for, session
from .mongo_helper import insert_race, get_existing_races
import os
from dotenv import load_dotenv

load_dotenv()

main = Blueprint('main', __name__)

@main.route('/', methods=['GET', 'POST'])
def dashboard():
    if request.method == 'POST':
        # Manually adding a race
        session['new_race'] = {
            'season': int(request.form['season']),
            'grandPrix': request.form['grandPrix'],
            'date': request.form['date'],
            'winner': {
                'driverName': request.form['winnerName'],
                'teamName': request.form['teamName']
            },
            'winningConstructor': request.form['teamName'],
            'laps': int(request.form['laps']),
            'raceTime': request.form['raceTime'],
            'fastestLap': {
                'driverName': request.form['fastestLapDriver'],
                'lapTime': request.form['fastestLapTime']
            }
        }
        return redirect(url_for('main.preview_race'))

    # Fetch the existing races
    existing_races = get_existing_races()

    # Get the latest race (if any)
    latest_race = sorted(existing_races, key=lambda x: x.get('date', ''), reverse=True)
    latest_race = latest_race[0] if latest_race else None  # If there's no race, latest_race will be None

    # Static calendar for now (you can add a more dynamic solution later)
    calendar = [
        {'date': '2024-03-10', 'grandPrix': 'Bahrain Grand Prix'},
        {'date': '2024-03-24', 'grandPrix': 'Saudi Arabian Grand Prix'},
        {'date': '2024-04-07', 'grandPrix': 'Australian Grand Prix'}
    ]

    query_result = session.pop('query_result', None)

    return render_template('dashboard.html', latest_race=latest_race, calendar=calendar, query_result=query_result)

@main.route('/preview')
def preview_race():
    new_race = session.get('new_race')
    if not new_race:
        return redirect(url_for('main.dashboard'))
    return render_template('preview.html', race=new_race)

@main.route('/approve')
def approve_race():
    new_race = session.get('new_race')
    if new_race:
        insert_race(new_race)
        session.pop('new_race', None)
    return redirect(url_for('main.dashboard'))

@main.route('/cancel')
def cancel_race():
    session.pop('new_race', None)
    return redirect(url_for('main.dashboard'))

@main.route('/query', methods=['POST'])
def query():
    query_text = request.form['query']

    if "driver" in query_text.lower():
        result = project_driver_standings()
    elif "constructor" in query_text.lower():
        result = project_constructor_standings()
    else:
        result = "Sorry, I couldn't understand your query."

    session['query_result'] = result
    return redirect(url_for('main.dashboard'))

# --- HELPER FUNCTIONS BELOW ---

def project_driver_standings():
    existing_races = get_existing_races()
    driver_points = {}

    for race in existing_races:
        winner = race.get('winner', {}).get('driverName')
        if winner:
            driver_points[winner] = driver_points.get(winner, 0) + 25  # winner points

    projected = []
    for driver, points in driver_points.items():
        projected_points = points + (3 * (points / len(existing_races)))  # simple avg projection
        projected.append((driver, projected_points))

    top5 = sorted(projected, key=lambda x: x[1], reverse=True)[:5]

    output = "🏎️ Projected Top 5 Drivers:\n"
    for driver, pts in top5:
        output += f"{driver}: {int(pts)} pts\n"
    return output

def project_constructor_standings():
    existing_races = get_existing_races()
    team_points = {}

    for race in existing_races:
        team = race.get('winner', {}).get('teamName')
        if team:
            team_points[team] = team_points.get(team, 0) + 25  # constructor points = winner points

    projected = []
    for team, points in team_points.items():
        projected_points = points + (3 * (points / len(existing_races)))
        projected.append((team, projected_points))

    output = "🏁 Projected Constructors:\n"
    for team, pts in sorted(projected, key=lambda x: x[1], reverse=True):
        output += f"{team}: {int(pts)} pts\n"
    return output
