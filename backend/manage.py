from flask import Flask, jsonify, request, session
from datetime import datetime, timedelta
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
    'testuser': {'password': os.getenv('TESTUSER_PASSWORD'), 'devices': [
        {
            'device_id': 'device1',
            'device_name': 'User’s iPhone',
            'login_time': '2024-10-28 12:30:00',
            'user_agent': 'iPhone User-Agent'
        },
        {
            'device_id': 'device2',
            'device_name': 'User’s iPad',
            'login_time': '2024-10-28 13:00:00',
            'user_agent': 'iPad User-Agent'
        },
        {
            'device_id': 'device3',
            'device_name': 'User’s Laptop',
            'login_time': '2024-10-28 13:30:00',
            'user_agent': 'Laptop User-Agent'
        }
    ]}
}


# Basic status check route
@app.route('/')
def index():
    return jsonify({"message": "SignOutSync Backend Running"}), 200

# User authentication function
def authenticate(username, password):
    user = users_db.get(username)
    if user and user['password'] == password:
        return True
    return False

# User login route
@app.route('/login', methods=['POST'])
def login():
    data = request.json

    # Validate that both username, password, and device name are provided
    if 'username' not in data or 'password' not in data or 'device_name' not in data:
        return jsonify({"message": "Username, password, and device name are required!"}), 400

    username = data['username']
    password = data['password']
    device_name = data['device_name']
    device_id = str(uuid.uuid4())  # Generate a unique device identifier
    login_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Get current time
    user_agent = request.headers.get('User-Agent')  # Get User-Agent from request headers

    # Perform authentication
    if authenticate(username, password):
        session['user'] = username
        session['device'] = device_id  # Store current device ID in the session
        session.permanent = True  # Mark the session as permanent (honors session lifetime)

        # Add the device to the user's devices list in the database
        user = users_db.get(username)
        user['devices'].append({
            'device_id': device_id,
            'device_name': device_name,
            'login_time': login_time,
            'user_agent': user_agent
        })  # Append new device to user's devices list
        return jsonify({
            "message": f"Logged in from {device_name} at {login_time}",
            "device_id": device_id,
            "user_agent": user_agent
        }), 200
    else:
        return jsonify({"message": "Invalid credentials!"}), 401

# User logout route to keep only the most recent device
@app.route('/logout', methods=['POST'])
def logout():
    if 'user' in session:
        username = session['user']
        user = users_db.get(username)

        if not user:
            return jsonify({"message": "User not found in the database!"}), 404

        # Get device_id from the request JSON to specify which device to log out
        data = request.json
        device_id = data.get("device_id")

        if not device_id:
            return jsonify({"message": "Device ID is required for logout!"}), 400

        # Find the device in the user's devices list
        device_info = next((device for device in user.get('devices', []) if device['device_id'] == device_id), None)

        if device_info:
            device_name = device_info['device_name']
            logout_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Get current time

            # Remove only the targeted device from the user's devices list
            user['devices'] = [device for device in user.get('devices', []) if device['device_id'] != device_id]

            # Clean up the session only if it matches the current device being logged out
            if session.get('device') == device_id:
                session.pop('device', None)
                session.pop('user', None)

            return jsonify({
                "message": f"Logged out from {device_name} at {logout_time}",
                "device_id": device_id
            }), 200
        else:
            return jsonify({"message": "Device not found!"}), 404
    else:
        return jsonify({"message": "No active session found!"}), 401


# View active devices
@app.route('/devices', methods=['POST'])
def view_devices():
    data = request.json
    username = data.get('username')
    if not username:
        return jsonify({"message": "Username is required!"}), 400

    user = users_db.get(username)
    if user:
        return jsonify(user), 200
    return jsonify({"message": "User not found!"}), 404

if __name__ == '__main__':
    app.run(debug=True)
