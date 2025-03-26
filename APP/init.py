# APP/__init__.py
from flask import Flask
from flask_login import LoginManager
import os
from pathlib import Path
from config import Config
from Database.db import db

# Create the Flask app instance
templates_directory = os.path.join(os.path.dirname(__file__), 'templates')
static_directory = os.path.join(os.path.dirname(__file__), 'static')

app = Flask(__name__, template_folder=templates_directory, static_folder=static_directory)

# Get the base directory
BASE_DIR = Path(__file__).parent.parent

# Configure database path - creates instance folder if it doesn't exist
DB_DIR = BASE_DIR / 'Database'
DB_PATH = DB_DIR / 'app.db'

# Ensure the Database directory exists
os.makedirs(DB_DIR, exist_ok=True)

# Update the config with proper database URI
app.config.from_object(Config)
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_PATH}'

# Initialize extensions
db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Import models after db initialization to avoid circular imports
from Database.db import User

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Create tables - with error handling
with app.app_context():
    try:
        db.create_all()
        print(f"Database created at: {DB_PATH}")  # Debug output
    except Exception as e:
        print(f"Error creating database: {str(e)}")
        # Try with absolute path as fallback
        try:
            app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.abspath(DB_PATH)}'
            db.create_all()
        except Exception as fallback_error:
            print(f"Fallback failed: {str(fallback_error)}")
            raise