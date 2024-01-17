# app.py

from flask import Flask, request, jsonify, url_for
from models import db, User
import os
from urllib.parse import quote_plus
from dotenv import load_dotenv
from datetime import datetime
from argon2 import PasswordHasher
from pybloom_live import BloomFilter
import secrets
from urllib.parse import quote_plus

# Bearer token import
from flask_jwt_extended import JWTManager
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity

# Importing the SMTP lib
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Create a Flask web application instance
app = Flask(__name__)

# Load environment variables from .env file
load_dotenv()

# Database configuration - Retrieve values from environment variables
db_name = os.getenv('DB_NAME')
username = os.getenv('DB_USERNAME')
password = quote_plus(os.getenv('DB_PASSWORD'))  # Encode the password with special characters
host = os.getenv('DB_HOST')
port = os.getenv('DB_PORT')

# Construct the database URL using the retrieved configuration values
db_url = f"postgresql://{username}:{password}@{host}:{port}/{db_name}"

# Configure the Flask app with the database URL and disable modification tracking
app.config['SQLALCHEMY_DATABASE_URI'] = db_url
db.init_app(app)

# Password hasher instance
ph = PasswordHasher()

# Importing backend URL
backend_url = os.getenv('BACKEND_URL')

# Checking if the password is in 100K Most Common Passwords list

password_file = "required_files/100k-most-used-passwords.txt"
with open(password_file, "r", encoding="latin-1") as file:
    rockyou_passwords = set(file.read().split("\n"))
    bloom_filter = BloomFilter(capacity=len(rockyou_passwords), error_rate=0.1)
    for password in rockyou_passwords:
        bloom_filter.add(password)

def is_weak_password(password):
    return password in bloom_filter
   
# Creating an admin
def register_admin():
    data = request.get_json()

    if not data:
        return jsonify({"error": "Invalid JSON data"}), 400

    # Validate input
    required_fields = ['first_name', 'last_name', 'email', 'password']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"{field} is required"}), 400

    # Check if the password is weak
    if is_weak_password(data['password']):
        return jsonify({"error": "Please choose a more secure password."}), 400

    # Check if the email is already registered
    if User.query.filter_by(email=data['email']).first():
        return jsonify({"error": "Email address is already in use. Please choose another email."}), 400

    # Create a new user
    new_user = User(
        first_name=data['first_name'],
        last_name=data['last_name'],
        email=data['email'],
        password=ph.hash(data['password']),  # Hashing the password using Argon2
        role=data.get('role', 'admin'),
        email_list=data.get('email_list', False),  # Default to False if not provided
        verified_email=data.get('verified_email', True),  # Default to False if not provided
        logged_in=data.get('logged_in', True),
        verification_code_created_at = datetime.utcnow(),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    # Add the user to the database
    db.session.add(new_user)
    db.session.commit()
    
    # Generate a bearer token for the new user
    access_token = create_access_token(identity=new_user.email)
    
    return jsonify({
        "message": "Registration successful! Please check your email for verification.",
        "email": new_user.email,
        "verified_email": new_user.verified_email,
        "access_token": access_token
    }), 200