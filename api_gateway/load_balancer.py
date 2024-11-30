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
    for i in range(len(INSTANCES)):
        target_instance = next(instance_cycle)
        target_url = f"{target_instance}/{path}"

        try:
            response = requests.request(
                method=request.method,
                url=target_url,
                headers={key: value for key, value in request.headers if key != "Host"},
                json=request.get_json(),
                params=request.args,
                timeout=3
            )
            print(response.status_code)
            return (response.content, response.status_code, response.headers.items())
        except (requests.exceptions.RequestException, requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            print(f"Failed to connect to {target_instance}. Error: {str(e)}")
    return jsonify({"error": "All instances are unavailable. Please try again later."}), 503

if __name__ == "__main__":
    app.run(port=8000, debug=False)
