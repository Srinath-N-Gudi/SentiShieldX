from flask import Flask

# Create the Flask app instance
app = Flask(__name__)

# Load configuration from config.py
app.config.from_object('config.Config')

# Import routes to register them with the app
from app import routes