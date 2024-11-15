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

# Route for the landing page
@app.route('/')
def index():
    if 'logged_in' in session and session['logged_in']:
        return redirect(url_for('main_menu'))
    return render_template('index.html')
