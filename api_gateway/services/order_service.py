from flask import Flask, request, jsonify

order_service = Flask(__name__)

# Sample orders data
orders = [
    {"order_id": 1, "user": "testuser", "items": ["item1", "item2"]},
]

@order_service.route('/orders', methods=['GET', 'POST'])
def manage_orders():
    if request.method == 'GET':
        return jsonify(orders)
    elif request.method == 'POST':
        new_order = request.json
        orders.append(new_order)
        return jsonify({"message": "Order added successfully"}), 201

if __name__ == "__main__":
    order_service.run(port=5002)
