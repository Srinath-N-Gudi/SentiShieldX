from flask import render_template, request, redirect, url_for
from .init import app

# Homepage route
@app.route('/')
def index():
    return render_template('index.html')

# Dashboard route
@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')
