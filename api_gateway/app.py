import sys
from flask import Flask, request, jsonify, g
import time
import logging
import requests
import redis
from utils.auth import authenticate_request
from utils.rate_limit import rate_limiter
from config import USER_SERVICE_URL, DOCUMENT_SERVICE_URL, LOG_FILE_PATH

app = Flask(__name__)

# Initialize logging with configuration from LOG_FILE_PATH
logging.basicConfig(
    filename=LOG_FILE_PATH,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# Initialize Redis connection
try:
    r = redis.Redis(host='localhost', port=6379, db=0)
    r.ping()
    print("Connected to Redis successfully!")
except redis.ConnectionError:
    print("Failed to connect to Redis. Please ensure Redis is running on localhost:6379.")

# Log request and response details
@app.before_request
def log_request_info():
    g.start_time = time.time()  # Track start time
    logging.info(
        {
            "event": "Incoming Request",
            "endpoint": request.path,
            "method": request.method,
            "client_ip": request.remote_addr,
            "headers": dict(request.headers),
            "body": request.json,
        }
    )

@app.after_request
def log_response_info(response):
    duration = time.time() - g.start_time
    logging.info(
        {
            "event": "Outgoing Response",
            "endpoint": request.path,
            "method": request.method,
            "status_code": response.status_code,
            "duration": f"{duration:.2f}s",
        }
    )
    return response

# Helper function for request validation
def validate_login_request(data):
    if "username" not in data or "password" not in data:
        return False, {"error": "Missing username or password"}
    return True, None

# Default route for root URL
@app.route('/')
def index():
    return jsonify({"message": "API Gateway is running"}), 200

# Gateway route to user service (for login)
@app.route('/login', methods=['POST'])
@rate_limiter
def login():
    try:
        request_payload = request.json

        # Validate request payload
        is_valid, error_response = validate_login_request(request_payload)
        if not is_valid:
            logging.warning(f"Invalid login request from {request.remote_addr}")
            return jsonify(error_response), 400

        # Forward request to user service
        response = requests.post(f"{USER_SERVICE_URL}/login", json=request_payload)
        return jsonify(response.json()), response.status_code
    except Exception as e:
        logging.error(f"Error in login: {e}")
        return jsonify({"error": "Service Unavailable"}), 503

# Gateway route to user service (for adding a user)
@app.route('/add_user', methods=['POST'])
@rate_limiter
def add_user():
    try:
        response = requests.post(f"{USER_SERVICE_URL}/add_user", json=request.json)
        return jsonify(response.json()), response.status_code
    except Exception as e:
        logging.error(f"Error in adding user: {e}")
        return jsonify({"error": "Service Unavailable"}), 503

# Other routes
@app.route('/delete_user', methods=['DELETE'])
@rate_limiter
def delete_user():
    try:
        response = requests.delete(f"{USER_SERVICE_URL}/delete_user", json=request.json)
        return jsonify(response.json()), response.status_code
    except Exception as e:
        logging.error(f"Error in deleting user: {e}")
        return jsonify({"error": "Service Unavailable"}), 503

@app.route('/documents', methods=['POST'])
@rate_limiter
def create_document():
    try:
        response = requests.post(f"{DOCUMENT_SERVICE_URL}/documents", json=request.json)
        return jsonify(response.json()), response.status_code
    except Exception as e:
        logging.error(f"Error in creating document: {e}")
        return jsonify({"error": "Service Unavailable"}), 503

@app.route('/documents/<document_id>', methods=['GET', 'PUT', 'DELETE'])
@rate_limiter
def manage_document(document_id):
    try:
        method_map = {
            "GET": requests.get,
            "PUT": requests.put,
            "DELETE": requests.delete,
        }
        response = method_map[request.method](
            f"{DOCUMENT_SERVICE_URL}/documents/{document_id}", json=request.json
        )
        return jsonify(response.json()), response.status_code
    except Exception as e:
        logging.error(f"Error in managing document {document_id}: {e}")
        return jsonify({"error": "Service Unavailable"}), 503

@app.route('/reset_rate_limit', methods=['POST'])
def reset_rate_limit():
    client_ip = request.remote_addr
    redis_key = f"rate_limit:{client_ip}"
    r.delete(redis_key)
    return jsonify({"message": "Rate limit reset for this IP"}), 200

if __name__ == "__main__":
    port = 5000
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print("Invalid port number, using default port 5000.")
    app.run(port=port, debug=True)