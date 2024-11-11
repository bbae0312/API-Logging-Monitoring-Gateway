from flask import Flask, request, jsonify
import time
import logging
import requests
from utils.auth import authenticate_request, authorize_request
from utils.rate_limit import rate_limiter

app = Flask(__name__)

# Initialize logging
logging.basicConfig(filename="logs/api_gateway.log", level=logging.INFO)

# Gateway route to user service (for login)
@app.route('/login', methods=['POST'])
@rate_limiter
def login():
    try:
        start_time = time.time()
        # Forward the request to user service
        response = requests.post("http://localhost:5001/login", json=request.json)
        # Log response details
        response_time = time.time() - start_time
        logging.info(f"Login request from {request.remote_addr} took {response_time:.2f}s with status {response.status_code}")
        return jsonify(response.json()), response.status_code
    except Exception as e:
        logging.error(f"Error in login: {e}")
        return jsonify({"error": "Service Unavailable"}), 503

# Gateway route to order service (for orders)
@app.route('/orders', methods=['GET', 'POST'])
@authenticate_request
@rate_limiter
def orders():
    try:
        if not authorize_request(request.headers.get("Authorization")):
            return jsonify({"error": "Unauthorized"}), 403
        start_time = time.time()
        # Forward the request to order service
        if request.method == 'POST':
            response = requests.post("http://localhost:5002/orders", json=request.json)
        else:
            response = requests.get("http://localhost:5002/orders")
        # Log response details
        response_time = time.time() - start_time
        logging.info(f"Order request from {request.remote_addr} took {response_time:.2f}s with status {response.status_code}")
        return jsonify(response.json()), response.status_code
    except Exception as e:
        logging.error(f"Error in orders: {e}")
        return jsonify({"error": "Service Unavailable"}), 503

if __name__ == "__main__":
    app.run(port=5000)
