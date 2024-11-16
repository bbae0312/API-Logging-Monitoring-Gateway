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
        )

        # Return the response from the instance
        return (response.content, response.status_code, response.headers.items())
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Failed to connect to {target_instance}. Error: {str(e)}"}), 503

if __name__ == "__main__":
    app.run(port=8000, debug=True)
