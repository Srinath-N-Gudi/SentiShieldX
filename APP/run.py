from init import app
import os
from flask import render_template, request, redirect, url_for, jsonify
import logging

from features.ytca import CommentAnalyzer
from features.Cyber import Cyber
##### Objects creations 


logging.basicConfig(
level=logging.DEBUG,
    format='[%(asctime)s - %(levelname)s] - %(message)s',
    handlers=[
        logging.FileHandler('LOG.log'),
        logging.StreamHandler()
    ]
)


# Creating Cyber Object
logging.info("Setting up AI Models")
cyber = Cyber('multilingual', device='cpu')
logging.info("Setup Complete")
# Create the CommentAnalyzer object
logging.info("Setting Up Analyzers")
youtube_comment_analyzer = CommentAnalyzer(cyber)  # Replace Cyber with your actual class
logging.info('Setup Complete')
print(os.getcwd())
# Homepage route
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/ytca')
def ytca():
    return render_template('ytca.html')

@app.route('/analyze', methods=['POST'])
def analyze_comments():
    video_url = request.form.get('url')
    
    # Your existing analysis function (modified)
    results = analyze_youtube_comments(video_url)  # Replace with your function
    
    return jsonify({
        'hate': results['hate_percentage'],
        'positive': results['positive_percentage'],
        'neutral': results['neutral_percentage']
    })

# Example analysis function (updated)
def analyze_youtube_comments(url):
    results = youtube_comment_analyzer.analyse_comment(url, num_comments=150) 
    
    return {
        'hate_percentage'    : round(results['hate_comments']     / results['total_comments'] * 100, 2),
        'positive_percentage': round(results['positive_comments'] / results['total_comments'] * 100, 2),
        'neutral_percentage' : round(results['neutral_comments']  / results['total_comments'] * 100, 2) # Add your existing code here  # Replace with your function to calculate percentages of hate, positive
    }


# Dashboard route
@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

if __name__=='__main__':
       app.run(debug=True)