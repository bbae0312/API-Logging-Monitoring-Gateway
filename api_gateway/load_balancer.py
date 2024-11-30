from flask import Flask, request, jsonify
import requests
import itertools

# List of API gateway instances
INSTANCES = ["http://127.0.0.1:4998", "http://127.0.0.1:4999", "http://127.0.0.1:5000"]

# Round-robin iterator for load balancing
instance_cycle = itertools.cycle(INSTANCES)

app = Flask(__name__)

@app.route("/", defaults={"path": ""}, methods=["GET", "POST", "PUT", "DELETE"])
@app.route("/<path:path>", methods=["GET", "POST", "PUT", "DELETE"])
def load_balancer(path):
    # Loop through instances to retry on failure
    for _ in range(len(INSTANCES)):  # Try all instances if needed
        target_instance = next(instance_cycle)  # Get the next instance in the cycle
        target_url = f"{target_instance}/{path}"

        try:
            # Forward the request to the selected instance
            response = requests.request(
                method=request.method,
                url=target_url,
                headers={key: value for key, value in request.headers if key != "Host"},
                json=request.get_json(),
                params=request.args,
                timeout=5  # Set a timeout (5 seconds for example)
            )
            print(response.status_code)
            # If the request is successful, return the response from the instance
            return (response.content, response.status_code, response.headers.items())

        except (requests.exceptions.RequestException, requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            # If the instance fails, print the error and try the next instance
            print(f"Failed to connect to {target_instance}. Error: {str(e)}")

    # If all instances fail, return an error message
    return jsonify({"error": "All instances are unavailable. Please try again later."}), 503

if __name__ == "__main__":
    app.run(port=8000, debug=False)
