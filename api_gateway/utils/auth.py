import jwt  # Import JWT library
from functools import wraps
from flask import request, jsonify

SECRET_KEY = 'your_secret_key'

# Decorator to authenticate request
def authenticate_request(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get("Authorization")
        if not token or not is_token_valid(token):
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated_function

# Validate JWT token.
def is_token_valid(token):
    try:
        if token.startswith('Bearer '):
            token = token.split(" ")[1]
        jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return True
    except jwt.ExpiredSignatureError:
        return False
    except jwt.InvalidTokenError:
        return False
