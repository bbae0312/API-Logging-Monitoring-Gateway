import sys
from flask import Flask, request, jsonify, g
import time
import logging
import requests
import redis
import os
from utils.auth import authenticate_request
from utils.rate_limit import rate_limiter
from config import USER_SERVICE_URL, DOCUMENT_SERVICE_URL, LOG_FILE_PATH

app = Flask(__name__)

# Initialize logging
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
    logging.error("Failed to connect to Redis. Ensure Redis is running on localhost:6379.")
    r = None  # Fallback if Redis is unavailable

# Helper function: sanitize sensitive fields
def sanitize_request_body(body):
    sanitized_body = body.copy()  # Create a copy of the request body
    if "password" in sanitized_body:
        sanitized_body["password"] = "********"  # Mask the password in the copy
    return sanitized_body

# Log request details
@app.before_request
def log_request_info():
    g.start_time = time.time()  # Track start time
    sanitized_body = sanitize_request_body(request.json)
    logging.info(
        {
            "event": "Incoming Request",
            "endpoint": request.path,
            "method": request.method,
            "client_ip": request.remote_addr,
            "headers": dict(request.headers),
            "body": sanitized_body,
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

# Helper function: validate request payload
def validate_fields(data, required_fields):
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        return False, {"error": f"Missing fields: {', '.join(missing_fields)}"}
    return True, None

# Default route
@app.route('/')
def index():
    return jsonify({"message": "API Gateway is running"}), 200

# Gateway route: login
@app.route('/login', methods=['POST'])
@rate_limiter
def login():
    try:
        request_payload = request.json
        is_valid, error_response = validate_fields(request_payload, ["username", "password"])
        if not is_valid:
            logging.warning(f"Invalid login request from {request.remote_addr}")
            return jsonify(error_response), 400

        # Forward request to user service
        response = requests.post(f"{USER_SERVICE_URL}/login", json=request_payload)
        return jsonify(response.json()), response.status_code
    except Exception as e:
        logging.error(f"Error in login: {e}")
        return jsonify({"error": "Service Unavailable"}), 503

# Gateway route: add user
@app.route('/add_user', methods=['POST'])
@rate_limiter
def add_user():
    try:
        response = requests.post(f"{USER_SERVICE_URL}/add_user", json=request.json)
        return jsonify(response.json()), response.status_code
    except Exception as e:
        logging.error(f"Error in adding user: {e}")
        return jsonify({"error": "Service Unavailable"}), 503

# Gateway route: delete user
@app.route('/delete_user', methods=['DELETE'])
@rate_limiter
def delete_user():
    try:
        response = requests.delete(f"{USER_SERVICE_URL}/delete_user", json=request.json)
        return jsonify(response.json()), response.status_code
    except Exception as e:
        logging.error(f"Error in deleting user: {e}")
        return jsonify({"error": "Service Unavailable"}), 503

# Gateway route: create document
@app.route('/documents', methods=['POST'])
@authenticate_request
@rate_limiter
def create_document():
    try:
        response = requests.post(f"{DOCUMENT_SERVICE_URL}/documents", json=request.json, headers=request.headers)
        return jsonify(response.json()), response.status_code
    except Exception as e:
        logging.error(f"Error in creating document: {e}")
        return jsonify({"error": "Service Unavailable"}), 503

# Gateway route: manage document
@app.route('/documents/<document_id>', methods=['GET', 'PUT', 'DELETE'])
@rate_limiter
@authenticate_request
def manage_document(document_id):
    try:
        method_map = {
            "GET": requests.get,
            "PUT": requests.put,
            "DELETE": requests.delete,
        }
        response = method_map[request.method](
            f"{DOCUMENT_SERVICE_URL}/documents/{document_id}", json=request.json, headers=request.headers
        )
        return jsonify(response.json()), response.status_code
    except Exception as e:
        logging.error(f"Error in managing document {document_id}: {e}")
        return jsonify({"error": "Service Unavailable"}), 503

# Reset rate limit
@app.route('/reset_rate_limit', methods=['POST'])
def reset_rate_limit():
    if not r:
        return jsonify({"error": "Redis is unavailable"}), 503
    client_ip = request.remote_addr
    redis_key = f"rate_limit:{client_ip}"
    r.delete(redis_key)
    return jsonify({"message": "Rate limit reset for this IP"}), 200

if __name__ == "__main__":
    # Check for port as command-line argument
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print("Invalid port number provided. Falling back to default port 5000.")
            port = 5000
    else:
        # Fallback to default port
        port = int(os.getenv("PORT", 5000))  # Allow configurable port via environment variable

    debug_mode = os.getenv("DEBUG", "True").lower() in ["true", "1"]
    app.run(port=port, debug=debug_mode)
