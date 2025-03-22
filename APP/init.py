from flask import Flask
import os
# Create the Flask app instance
app = Flask(__name__, template_folder=os.path.join(os.getcwd(), 'APP','templates'))
# Load configuration from config.py
#app.config.from_object('config.Config')

# Import routes to register them with the app
