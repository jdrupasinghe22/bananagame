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
