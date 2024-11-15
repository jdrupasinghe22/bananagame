from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import requests
import json
import time
from datetime import timedelta
import sys

# Disable output buffering for print statements
sys.stdout.reconfigure(line_buffering=True)

app = Flask(__name__)
app.secret_key = 'banana_secret_key'

# Load player data from JSON file
def load_players():
    try:
        with open('players.json', 'r') as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

# Save player data to JSON file
def save_players(players):
    with open('players.json', 'w') as file:
        json.dump(players, file, indent=4)

# Initialize player session
def initialize_player_session(player_name):
    session.permanent = True
    app.permanent_session_lifetime = timedelta(days=7)
    session['player_name'] = player_name
    session['logged_in'] = True

# Helper function to fetch a new puzzle from the API
def get_puzzle():
    response = requests.get('http://marcconrad.com/uob/banana/api.php?out=json')
    data = response.json()
    question_url = data['question']
    solution = str(data['solution'])
    print(f"API Request: {response.url}")
    print(f"Puzzle Image URL: {question_url}, Correct Answer: {solution}", flush=True)
    return question_url, solution

# Helper function to get level settings
def get_level_settings(level):
    settings = {
        0: {'time': 90, 'hints': 3, 'attempts': 5},
        1: {'time': 80, 'hints': 2, 'attempts': 4},
        2: {'time': 70, 'hints': 1, 'attempts': 3},
        3: {'time': 60, 'hints': 1, 'attempts': 2},
        4: {'time': 30, 'hints': 1, 'attempts': 1},
        5: {'time': 0, 'hints': 0, 'attempts': 0},
    }
    return settings.get(level, settings[0])

# Route for the landing page
@app.route('/')
def index():
    if 'logged_in' in session and session['logged_in']:
        return redirect(url_for('main_menu'))
    return render_template('index.html')

# Route for the signup page
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    players = load_players()
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        re_password = request.form['re_password']
        if len(password) < 8:
            flash("Password must be at least 8 characters long.")
        elif password != re_password:
            flash("Passwords do not match.")
        elif username in players:
            flash("Username already exists.")
        else:
            players[username] = {'password': password, 'level': 0, 'correct_count': 0}
            save_players(players)
            initialize_player_session(username)
            return redirect(url_for('main_menu'))
    return render_template('signup.html')

# Route for the login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    players = load_players()
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in players and players[username]['password'] == password:
            initialize_player_session(username)
            return redirect(url_for('main_menu'))
        else:
            flash("Invalid username or password. Please try again.")
    return render_template('login.html')

# Route for the main menu
@app.route('/main_menu')
def main_menu():
    if 'logged_in' in session and session['logged_in']:
        return render_template('main_menu.html', player_name=session['player_name'])
    return redirect(url_for('login'))

# Route for the how-to-play page
@app.route('/how_to_play')
def how_to_play():
    return render_template('how_to_play.html')

# Route for the player profile
@app.route('/profile')
def profile():
    if 'logged_in' in session and session['logged_in']:
        player_name = session['player_name']
        players = load_players()
        player_data = players.get(player_name, {})
        level = player_data.get('level', 0)
        return render_template('profile.html', player_name=player_name, level=level)
    return redirect(url_for('login'))

# Route for logging out
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# Route for the game page
@app.route('/game', methods=['GET'])
def game():
    if 'logged_in' not in session or not session['logged_in']:
        return redirect(url_for('login'))
    
    player_name = session['player_name']
    players = load_players()
    player_data = players.get(player_name, {})
    level = player_data.get('level', 0)
    correct_count = player_data.get('correct_count', 0)
    level_settings = get_level_settings(level)

    # Check if the player has already won
    if level == 5:
        return redirect(url_for('you_won'))

    if 'current_puzzle' not in session or session['puzzle_completed']:
        question, solution = get_puzzle()
        session['current_puzzle'] = question
        session['current_solution'] = solution
        session['hints_left'] = level_settings['hints']
        session['attempts_left'] = level_settings['attempts']
        session['time_left'] = level_settings['time']
        session['puzzle_completed'] = False
        session['game_over'] = False

    return render_template(
        'game.html',
        question=session['current_puzzle'],
        level=level,
        attempts_left=session['attempts_left'],
        hints_left=session['hints_left'],
        time_left=session['time_left'],
        correct_count=correct_count
    )


# AJAX route for "Next Puzzle"
@app.route('/next_puzzle', methods=['POST'])
def next_puzzle():
    question, solution = get_puzzle()
    player_name = session.get('player_name')
    players = load_players()
    player_data = players.get(player_name, {})
    level = player_data.get('level', 0)
    correct_count = player_data.get('correct_count', 0)
    level_settings = get_level_settings(level)

    session['current_puzzle'] = question
    session['current_solution'] = solution
    session['hints_left'] = level_settings['hints']
    session['attempts_left'] = level_settings['attempts']
    session['time_left'] = level_settings['time']
    session['puzzle_completed'] = False
    session['game_over'] = False

    return jsonify({
        "status": "success",
        "question": question,
        "attempts_left": level_settings['attempts'],
        "hints_left": level_settings['hints'],
        "time_left": level_settings['time'],
        "correct_count": correct_count,
        "level": level
    })


if __name__ == '__main__':
    app.run(debug=True)