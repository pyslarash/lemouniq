from flask import Flask
from flask_cors import CORS
from image_processing import *
from user import *
from models import db, migrate
import os
from dotenv import load_dotenv
from urllib.parse import quote_plus
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
load_dotenv()

# Configure the Flask app with the JWT secret key
app.config["JWT_SECRET_KEY"] = quote_plus(os.getenv('JWT_SECRET_KEY'))

# Initialize the Flask JWT extension
jwt = JWTManager(app)

# Database configuration - Retrieve values from environment variables
db_name = os.getenv('DB_NAME')
username = os.getenv('DB_USERNAME')
password = quote_plus(os.getenv('DB_PASSWORD'))  # Encode the password with special characters
host = os.getenv('DB_HOST')
port = os.getenv('DB_PORT')

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = f"postgresql://{username}:{password}@{host}:{port}/{db_name}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database with the app
db.init_app(app)
migrate.init_app(app, db)

# API ENDPOINTS

# Test if API is working
@app.route('/test')
def index():
    return "The backend is reachable"

# Image processing

app.route('/upload', methods=['POST'])(upload_file)  # Endpoint to upload images

# User processing

app.route('/register', methods=['POST'])(register)  # Endpoint to register a user
app.route('/check_mail_connection', methods=['GET'])(check_mail_connection)  # Endpoint to check email connection
app.route('/verify_code', methods=['POST'])(verify_code)  # Endpoint to register a user
app.route('/send_new_verification_code', methods=['POST'])(send_new_verification_code)  # Endpoint to send a new verification code

# SCHEDULED TASKS
scheduler = BackgroundScheduler()

# Functions for scheduled tasks
def remove_expired_verification_codes():
    with app.app_context():
        expired_users = User.query.filter(
            User.verification_code_created_at < datetime.utcnow() - timedelta(minutes=10),
            User.verification_code.isnot(None)
        ).all()

        for user in expired_users:
            user.verification_code = None
            user.verification_code_created_at = None

        db.session.commit()

scheduler.add_job(remove_expired_verification_codes, 'interval', minutes=1)

if __name__ == '__main__':
    # Run the scheduler
    scheduler.start()
    # Start the Flask app
    app.run(debug=True)