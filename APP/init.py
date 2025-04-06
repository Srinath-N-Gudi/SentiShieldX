# APP/__init__.py
import os
from flask import Flask
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect

from pathlib import Path
from config import Config
from Database.db import db
from Database.db import User
from dotenv import load_dotenv



load_dotenv()

# Create the Flask app instance
templates_directory = os.path.join(os.path.dirname(__file__), 'templates')
static_directory    = os.path.join(os.path.dirname(__file__), 'static')

app = Flask(__name__, template_folder=templates_directory, static_folder=static_directory)

BASE_DIR = Path(__file__).parent.parent

# Configure database path - creates instance folder if it doesn't exist
DB_DIR = BASE_DIR / 'Database'
DB_PATH = DB_DIR / 'app.db'

# Ensure the Database directory exists
os.makedirs(DB_DIR, exist_ok=True)

# Update the config with proper database URI
app.config.from_object(Config)
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_PATH}'
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY') 


csrf = CSRFProtect(app)
db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

    
with app.app_context():
    try:
        db.create_all()
        print(f"Database created at: {DB_PATH}") 
    except Exception as e:
        print(f"Error creating database: {str(e)}")
        try:
            app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.abspath(DB_PATH)}'
            db.create_all()
        except Exception as fallback_error:
            print(f"Fallback failed: {str(fallback_error)}")
            raise