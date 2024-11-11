from flask import request, jsonify
from functools import wraps
from time import time

# Rate limiting data
user_requests = {}
MAX_REQUESTS = 5  # Max requests per minute per IP
TIME_WINDOW = 60  # Time window in seconds

def rate_limiter(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        ip = request.remote_addr  # Get the IP address of the request
        current_time = time()
        
        # Initialize request tracking for new IP addresses
        if ip not in user_requests:
            user_requests[ip] = []
        
        # Remove outdated requests outside of the TIME_WINDOW
        user_requests[ip] = [req for req in user_requests[ip] if current_time - req < TIME_WINDOW]
        
        # Check if the request count exceeds the limit
        if len(user_requests[ip]) >= MAX_REQUESTS:
            return jsonify({"error": "Rate limit exceeded"}), 429
        
        # Log the current request timestamp and proceed
        user_requests[ip].append(current_time)
        return f(*args, **kwargs)
    
    return decorated_function
