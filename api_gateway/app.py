from flask import Flask, request, jsonify
import time
import logging
import requests
from utils.auth import authenticate_request, authorize_request
from utils.rate_limit import rate_limiter
from config import USER_SERVICE_URL, ORDER_SERVICE_URL, LOG_FILE_PATH

app = Flask(__name__)

# Initialize logging with configuration from LOG_FILE_PATH
logging.basicConfig(filename=LOG_FILE_PATH, level=logging.INFO)

# Helper function for request validation
def validate_login_request(data):
    if "username" not in data or "password" not in data:
        return False, {"error": "Missing username or password"}
    return True, None

# Helper function for response transformation
def transform_order_response(data):
    return [
        {
            "order_id": order.get("order_id"),
            "user": order.get("user"),
            "items": order.get("items")
        }
        for order in data.get("orders", [])
    ]

# Default route for root URL
@app.route('/')
def index():
    return jsonify({"message": "API Gateway is running"}), 200

# Gateway route to user service (for login)
@app.route('/login', methods=['POST'])
@rate_limiter
def login():
    try:
        start_time = time.time()
        request_payload = request.json

        # Validate request
        is_valid, error_response = validate_login_request(request_payload)
        if not is_valid:
            logging.info(f"Invalid login request from {request.remote_addr}")
            return jsonify(error_response), 400  # Bad Request

        # Redact sensitive information in the logs
        log_payload = {k: v for k, v in request_payload.items() if k != "password"}

        # Forward the request to user service
        response = requests.post(f"{USER_SERVICE_URL}/login", json=request_payload)
        response_time = time.time() - start_time

        # Log request and response details
        logging.info({
            "endpoint": "/login",
            "client_ip": request.remote_addr,
            "request_payload": log_payload,
            "response_status": response.status_code,
            "response_payload": response.json(),
            "start_time": start_time,
            "end_time": time.time(),
            "duration": f"{response_time:.2f}s"
        })

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
        
        # Route based on the presence of `order_id` in GET requests
        if request.method == 'POST':
            response = requests.post(f"{ORDER_SERVICE_URL}/orders", json=request.json)
        elif request.method == 'GET' and 'order_id' in request.args:
            response = requests.get(f"{ORDER_SERVICE_URL}/orders/{request.args.get('order_id')}")
        else:
            response = requests.get(f"{ORDER_SERVICE_URL}/orders")
        
        response_time = time.time() - start_time
        response_data = response.json()

        # Transform response if `Client-Type` is `MobileApp`
        if request.headers.get("Client-Type") == "MobileApp":
            response_data = transform_order_response(response_data)

        # Log request and response details
        logging.info({
            "endpoint": "/orders",
            "client_ip": request.remote_addr,
            "request_method": request.method,
            "request_args": request.args,
            "response_status": response.status_code,
            "response_payload": response_data,
            "start_time": start_time,
            "end_time": time.time(),
            "duration": f"{response_time:.2f}s"
        })

        return jsonify(response_data), response.status_code
    except Exception as e:
        logging.error(f"Error in orders: {e}")
        return jsonify({"error": "Service Unavailable"}), 503

if __name__ == "__main__":
    app.run(port=5000)
