from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    if data.get("username") == "user" and data.get("password") == "pass":
        return jsonify({"message": "Login successful", "token": "your_authorization_token"}), 200
    return jsonify({"error": "Invalid credentials"}), 401

# Status endpoint to check if the service is running
@app.route('/status', methods=['GET'])
def status():
    return jsonify({"status": "Server is running"}), 200

if __name__ == "__main__":
    app.run(port=5001)
