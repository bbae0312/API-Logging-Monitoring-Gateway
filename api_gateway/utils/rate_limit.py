import redis
from flask import request, jsonify
from functools import wraps

# Connect to Redis
try:
    r = redis.Redis(host='localhost', port=6379, db=0)
    r.ping()
    print("Connected to Redis for rate limiting!")
except redis.ConnectionError:
    print("Failed to connect to Redis for rate limiting. Ensure Redis is running on localhost:6379.")

# Rate limit settings
MAX_REQUESTS = 20 # no. of requests
TIME_WINDOW = 300 # seconds = 5 minutes

# Decorator for rate limiting
def rate_limiter(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        client_ip = request.remote_addr
        redis_key = f"rate_limit:{client_ip}"
        try:
            current_count = r.incr(redis_key)
        except redis.exceptions.ResponseError:
            r.delete(redis_key)
            current_count = r.incr(redis_key)
        if current_count == 1:
            r.expire(redis_key, TIME_WINDOW)
        # Check if the request count exceeds the rate limit
        if current_count > MAX_REQUESTS:
            print(f"Rate limit exceeded for IP: {client_ip}")
            return jsonify({"error": "Rate limit exceeded"}), 429
        print(f"Request count for IP {client_ip}: {current_count}/{MAX_REQUESTS}")
        return f(*args, **kwargs)
    return decorated_function
