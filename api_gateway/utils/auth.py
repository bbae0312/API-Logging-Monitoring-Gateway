import redis
from functools import wraps
from flask import request, jsonify

# Connect to Redis
try:
    r = redis.Redis(host='localhost', port=6379, db=0)
    r.ping()
    print("Connected to Redis for authentication!")
except redis.ConnectionError:
    print("Failed to connect to Redis for authentication. Ensure Redis is running on localhost:6379.")

# Token expiration time in seconds (default: 1 hour)
TOKEN_EXPIRATION = 3600

def authenticate_request(f):
    """Decorator to check if the request has a valid token."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get("Authorization")
        if not token or not is_token_valid(token):
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated_function

def authorize_request(token):
    """Store token in Redis with expiration, simulating login."""
    try:
        r.set(f"auth_token:{token}", "valid", ex=TOKEN_EXPIRATION)
    except redis.ConnectionError:
        print("Error: Failed to store token in Redis.")

def is_token_valid(token):
    """Check if token exists in Redis."""
    try:
        return r.exists(f"auth_token:{token}") > 0
    except redis.ConnectionError:
        print("Error: Failed to validate token in Redis.")
        return False

def invalidate_token(token):
    """Remove token from Redis, simulating logout."""
    try:
        r.delete(f"auth_token:{token}")
    except redis.ConnectionError:
        print("Error: Failed to invalidate token in Redis.")
