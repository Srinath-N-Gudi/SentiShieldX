from flask import Flask
import os
 # Create the Flask app instance
app = Flask(__name__, template_folder=os.path.join(os.getcwd(), 'APP','templates'))
from flask import render_template, request, redirect, url_for
from .init import app
@app.route('/')
@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

from .init import app
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

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt # type: ignore
from flask_login import LoginManager

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'  # Use environment variables in production
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'  # Use PostgreSQL/MySQL in production
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'  # Route for unauthorized users

# Load user for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))