from flask import Flask
import os
# Create the Flask app instance

templates_directory  = os.path.join(os.path.dirname(__file__), 'templates'  )
static_directory = os.path.join(os.path.dirname(__file__), 'static')

app = Flask(__name__, template_folder=templates_directory, static_folder=static_directory)
# Load configuration from config.py
#app.config.from_object('config.Config')

# Import routes to register them with the app
