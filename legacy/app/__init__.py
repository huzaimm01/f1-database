from flask import Flask
import os  
from .routes import main  

def create_app():
    app = Flask(__name__)

    
    app.secret_key = os.urandom(24)  

    app.register_blueprint(main)

    return app
