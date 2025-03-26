# APP/run.py
from init import app
from flask import render_template, request, redirect, url_for, jsonify, flash
from flask_login import login_user, logout_user, current_user, login_required
import os
import logging
from Database.db import db, User
from features.ytca import CommentAnalyzer
from features.Cyber import Cyber

# Initialize logging
logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s - %(levelname)s] - %(message)s',
    handlers=[
        logging.FileHandler('LOG.log'),
        logging.StreamHandler()
    ]
)

# Initialize AI models
logging.info("Setting up AI Models")
cyber = Cyber('multilingual', device='cpu')
logging.info("Setup Complete")

logging.info("Setting Up Analyzers")
youtube_comment_analyzer = CommentAnalyzer(cyber)
logging.info('Setup Complete')

# Routes
@app.route('/')
def index():
    if current_user.is_authenticated:  # Check if user is logged in
        return redirect(url_for('dashboard'))  # Redirect to dashboard if logged in
    return render_template('index.html')  # Show index only for guests

@app.route('/ytca')
def ytca():
    return render_template('ytca.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        try:
            # Get raw form data (exactly as user typed it)
            username = request.form['username'].strip()
            email = request.form['email'].strip()  # Preserves original case
            password = request.form['password'].strip()

            # Basic validation
            if not username or not email or not password:
                flash('All fields are required', 'error')
                return redirect(url_for('signup'))

            # Check for existing user (case-sensitive)
            if User.query.filter_by(email=email).first():
                flash('Email already registered', 'error')
                return redirect(url_for('signup'))
                
            if User.query.filter_by(username=username).first():
                flash('Username already taken', 'error')
                return redirect(url_for('signup'))

            # Create user with original-case email
            new_user = User(username=username, email=email)
            new_user.set_password(password)
            
            db.session.add(new_user)
            db.session.commit()
            
            login_user(new_user)  # Auto-login
            return redirect(url_for('dashboard'))

        except Exception as e:
            db.session.rollback()
            flash('Registration failed. Please try again.', 'error')
            return redirect(url_for('signup'))
    
    return render_template('signup.html')



@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']      # Only email, not username
        password = request.form['password']
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password', 'error')
    
    return render_template('login.html')  # Should only have email/password fields

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', user=current_user)

@app.route('/analyze', methods=['POST'])
def analyze_comments():
    video_url = request.form.get('url')
    results = youtube_comment_analyzer.analyse_comment(video_url, num_comments=150) 
    
    return jsonify({
        'hate': round(results['hate_comments'] / results['total_comments'] * 100, 2),
        'positive': round(results['positive_comments'] / results['total_comments'] * 100, 2),
        'neutral': round(results['neutral_comments'] / results['total_comments'] * 100, 2)
    })

@app.route('/comming_soon')
def comming_soon():
    return render_template('under_development.html')


if __name__ == '__main__':
    app.run(debug=True)