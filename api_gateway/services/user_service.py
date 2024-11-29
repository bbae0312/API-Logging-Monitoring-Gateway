from flask import Flask, request, jsonify
from pymongo import MongoClient
import bcrypt
import jwt
import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'  # Set this to a strong secret key

# MongoDB configuration
client = MongoClient("mongodb://localhost:27017/")
db = client['mydatabase']
users_collection = db['users']

# Helper function to create a JWT token
def generate_token(username):
    token = jwt.encode({
        'username': username,
        'exp': datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1)
    }, app.config['SECRET_KEY'], algorithm="HS256")
    return token

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    user = users_collection.find_one({"username": data.get("username")})
    print(user)
    print(data.get("password").encode('utf-8'))

    # Check if user exists and if password matches
    if user and bcrypt.checkpw(data.get("password").encode('utf-8'), user["password"]):
        token = generate_token(user["username"])
        return jsonify({"message": "Login successful", "token": token}), 200
    return jsonify({"error": "Invalid credentials"}), 401

# Endpoint to add a new user
@app.route('/add_user', methods=['POST'])
def add_user():
    new_user = request.json
    if users_collection.find_one({"username": new_user.get("username")}):
        return jsonify({"error": "User already exists"}), 400
    
    hashed_password = bcrypt.hashpw(new_user.get("password").encode('utf-8'), bcrypt.gensalt())
    new_user_data = {
        "username": new_user.get("username"),
        "password": hashed_password
    }
    users_collection.insert_one(new_user_data)
    return jsonify({"message": "User added successfully"}), 201

# Endpoint to delete a user (for testing purposes)
@app.route('/delete_user', methods=['DELETE'])
def delete_user():
    data = request.json
    username = data.get("username")

    # Ensure the username is provided
    if not username:
        return jsonify({"error": "Username is required"}), 400

    # Find and delete the user
    result = users_collection.delete_one({"username": username})

    if result.deleted_count > 0:
        return jsonify({"message": "User deleted successfully"}), 200
    else:
        return jsonify({"error": "User not found"}), 404

# Status endpoint to check if the service is running
@app.route('/status', methods=['GET'])
def status():
    return jsonify({"status": "User Service is running"}), 200

if __name__ == "__main__":
    app.run(port=5001)
