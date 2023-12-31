"""
File: Server.py
Programmer: Ali Rahbar
Date: December 16, 2023
Description: This file is incharge of starting up the calendarium backend server.
"""
import time

from flask import Flask
from flask_cors import CORS
from app import app
from database.db import db

import os
from flask import Flask, request, g

# Set the status of the debugger
DEBUG = True
PORT = int(os.getenv('PORT', 44000))

# Start the app
flask_app = Flask(__name__, static_url_path='', template_folder='templates')
flask_app.config.from_pyfile('config.py')
flask_app.secret_key = "flask rocks!"  # ToDo: Move to an environment variable

db.init_app(flask_app)

CORS(flask_app)
print('this is server', id(db))


# def background_task():
#
#     time.sleep(5)
#
#     with flask_app.app_context():
#         start_sync()



def run_flask():
    """
    Run the flask webserver and prepares the database
    """
    global flask_app

    # Start the flaks app
    flask_app.register_blueprint(app.api_bp, url_prefix='/api')
    flask_app.run(host='0.0.0.0', port=PORT, debug=True)


if __name__ == '__main__':
    # synchronization_thread = threading.Thread(target=background_task)
    # synchronization_thread.start()

    run_flask()


