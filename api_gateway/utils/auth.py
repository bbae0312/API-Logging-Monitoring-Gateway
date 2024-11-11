from functools import wraps
from flask import request, jsonify

# Simple token-based auth
def authenticate_request(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get("Authorization")
        if not token:
            return jsonify({"error": "Token required"}), 401
        return f(*args, **kwargs)
    return decorated_function

def authorize_request(token):
    # Basic authorization check (replace with actual authorization logic)
    return token == "abc123"
