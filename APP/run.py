from init import app
import os
from flask import render_template, request, redirect, url_for


print(os.getcwd())
# Homepage route
@app.route('/')
def index():
    return render_template('index.html')

# Dashboard route
@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')





if __name__=='__main__':
       app.run(debug=True)