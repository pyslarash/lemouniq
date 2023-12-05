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

# Verification code generator
def generate_verification_code():
    return secrets.randbelow(900000) + 100000

# This function checks email connection

def check_mail_connection():
    try:
        # Your email server settings
        mail_server = os.getenv('MAIL_SERVER')
        mail_port = int(os.getenv('MAIL_PORT', 465))
        mail_username = os.getenv('MAIL_USERNAME')
        mail_password = os.getenv('MAIL_PASSWORD')

        # Create the MIMEText object
        message = MIMEMultipart()
        sender_name = os.getenv("MAIL_SENDER_NAME")
        message['From'] = f'{sender_name} <{os.getenv("MAIL_DEFAULT_SENDER")}>'
        message['To'] = ', '.join([os.getenv('MAIL_RECEPIENT')])
        message['Subject'] = "Hi! I'm just running a test!"
        message.attach(MIMEText("This is a test", 'plain'))

        # Connect to the server using SSL
        with smtplib.SMTP_SSL(mail_server, mail_port) as server:
            # Log in to the server
            server.login(mail_username, mail_password)

            # Send the email
            server.sendmail(os.getenv('MAIL_DEFAULT_SENDER'), [os.getenv('MAIL_RECEPIENT')], message.as_string())

        # If the email sends successfully, return a success message
        return jsonify({"message": "Mail connection established successfully."}), 200
    except Exception as e:
        # If there is an exception, print detailed information
        print(f"Exception during email sending: {str(e)}")
        return jsonify({"error": f"Failed to establish mail connection. Error: {str(e)}"}), 500

# Checking if the password is in 100K Most Common Passwords list

password_file = "required_files/100k-most-used-passwords.txt"
with open(password_file, "r", encoding="latin-1") as file:
    rockyou_passwords = set(file.read().split("\n"))
    bloom_filter = BloomFilter(capacity=len(rockyou_passwords), error_rate=0.1)
    for password in rockyou_passwords:
        bloom_filter.add(password)

def is_weak_password(password):
    return password in bloom_filter

# Creating a user

def register():
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
        return jsonify({"error": "Email address is already in use. Please choose another."}), 400
    
    # Generate a verification code
    verification_code = generate_verification_code()

    # Create a new user
    new_user = User(
        first_name=data['first_name'],
        last_name=data['last_name'],
        email=data['email'],
        password=ph.hash(data['password']),  # Hashing the password using Argon2
        user_type=data.get('user_type', 'User'),
        email_list=data.get('email_list', False),  # Default to False if not provided
        verified_email=data.get('verified_email', False),  # Default to False if not provided
        verification_code=verification_code,
        verification_code_created_at = datetime.utcnow(),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    # Add the user to the database
    db.session.add(new_user)
    db.session.commit()
    
    send_verification_code(new_user)
    
    # Generate a bearer token for the new user
    access_token = create_access_token(identity=new_user.email)
    
    return jsonify({
        "message": "Registration successful! Please check your email for verification.",
        "email": new_user.email,
        "verified_email": new_user.verified_email,
        "access_token": access_token
    }), 200

# Function that sends an email with the verification code
def send_verification_code(user):
    verification_code = user.verification_code

    # Save the verification code in your user database or in a cache for validation later
    user.verification_code = verification_code
    db.session.commit()

    # Create the email message
    subject = "Verify Your Email - Lemouniq"
    body = f"Hi {user.first_name}!\n\nYour verification code is: {verification_code}"

    message = MIMEMultipart()
    message['From'] = os.getenv('MAIL_DEFAULT_SENDER')
    message['To'] = user.email
    message['Subject'] = subject
    message.attach(MIMEText(body, 'plain'))

    try:
        # Connect to the server using SSL
        with smtplib.SMTP_SSL(os.getenv('MAIL_SERVER'), int(os.getenv('MAIL_PORT', 465))) as server:
            # Log in to the server
            server.login(os.getenv('MAIL_USERNAME'), os.getenv('MAIL_PASSWORD'))

            # Send the email
            server.sendmail(os.getenv('MAIL_DEFAULT_SENDER'), [user.email], message.as_string())

        print("Verification email sent successfully.")
        return jsonify({"message": "Verification code sent successfully."}), 200
    except Exception as e:
        print(f"Failed to send verification email. Error: {str(e)}")
        return jsonify({"error": f"Failed to send verification code. Error: {str(e)}"}), 500

# Verifying the 6-digit code
@jwt_required()
def verify_code():
    data = request.get_json()
    
    def check_verification_code(email, verification_code):
        user = User.query.filter_by(email=email, verification_code=verification_code).first()

        # Check if the user and verification code match
        if user:
            return True
        
        return False

    if not data or 'email' not in data or 'verification_code' not in data:
        return jsonify({"error": "Invalid JSON data"}), 400

    email = data['email']
    verification_code = data['verification_code']

    if check_verification_code(email, verification_code):
        # Update the user's verified_email status
        user = User.query.filter_by(email=email).first()
        user.verified_email = True
        user.verification_code = None
        user.verification_code_created_at = None
        user.updated_at=datetime.utcnow()
        db.session.commit()

        return jsonify({"message": "Verification code is valid. Email verified successfully!"}), 200
    else:
        return jsonify({"error": "Invalid verification code"}), 400
    
# Generating another verification code
@jwt_required()
def send_new_verification_code():
    data = request.get_json()

    # Check if the required keys are present in the JSON
    if not data or 'email' not in data:
        return jsonify({"error": "Invalid JSON data"}), 400

    # Check if the user exists
    user = User.query.filter_by(email=data['email']).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    # Check if the email is already verified
    if user.verified_email:
        return jsonify({"error": "Email is already verified"}), 400

    # Check if there is an existing verification code
    if user.verification_code:
        # Keep the old code
        return jsonify({"error": "Previous verification code didn't expire yet."}), 400
    else:
        # Generate a new verification code if none exists
        new_verification_code = generate_verification_code()
        user.verification_code = str(new_verification_code)

    # Update the timestamp
    user.verification_code_created_at = datetime.utcnow()

    # Commit changes to the database
    db.session.commit()
    
    # Send the new verification email
    send_verification_code(user)

    return jsonify({"message": "New verification code has been sent"}), 200