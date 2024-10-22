from flask import Flask, jsonify, request, session
from datetime import timedelta
import uuid
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Set a strong secret key for session management from environment variable
app.secret_key = os.getenv('SECRET_KEY')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)

# In-memory storage for users and sessions (this is for demo purposes, replace with actual DB in production)
users_db = {
    'testuser': {'password': os.getenv('TESTUSER_PASSWORD'), 'devices': []}  # Example user
}

# Basic status check route
@app.route('/')
def index():
    return jsonify({"message": "SignOutSync Backend Running"}), 200

# User authentication function
def authenticate(username, password):
    # Check if user exists in the users_db and the password matches
    user = users_db.get(username)
    if user and user['password'] == password:
        return True
    return False

# User login route
@app.route('/login', methods=['POST'])
def login():
    data = request.json

    # Validate that both username and password are provided
    if 'username' not in data or 'password' not in data:
        return jsonify({"message": "Username and password are required!"}), 400

    username = data['username']
    password = data['password']
    device = str(uuid.uuid4())  # Generate a unique device identifier

    # Perform authentication
    if authenticate(username, password):
        session['user'] = username
        session['device'] = device  # Store the unique device identifier in the session
        session.permanent = True  # Mark the session as permanent (honors session lifetime)

        # Add the device to the user's devices list in the database
        user = users_db.get(username)
        user['devices'].append(device)  # Append new device to user's devices list

        return jsonify({"message": f"Logged in on device {device}"}), 200
    else:
        return jsonify({"message": "Invalid credentials!"}), 401

# User logout route
@app.route('/logout', methods=['POST'])
def logout():
    if 'user' in session and 'device' in session:
        username = session['user']
        device = session['device']  # Get the stored device identifier
        user = users_db.get(username)

        if not user:
            return jsonify({"message": "User not found in the database!"}), 404

        # Remove the device from the user's devices list
        if device in user.get('devices', []):
            user['devices'].remove(device)

        # Clean up the session for the current device
        session.pop('device', None)
        session.pop('user', None)

        return jsonify({"message": f"Logged out from device {device}"}), 200
    else:
        return jsonify({"message": "No active session found!"}), 401

# View active devices
@app.route('/devices', methods=['GET'])
def view_devices():
    if 'user' in session:
        username = session['user']
        user = users_db.get(username)
        if user:
            return jsonify({"devices": user['devices']}), 200
    return jsonify({"message": "No active session found!"}), 401

if __name__ == '__main__':
    app.run(debug=True)