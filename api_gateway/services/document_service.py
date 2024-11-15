from flask import Flask, request, jsonify
from pymongo import MongoClient
from bson import ObjectId

app = Flask(__name__)

# MongoDB configuration
client = MongoClient("mongodb://localhost:27017/")
db = client['mydatabase']
documents_collection = db['documents']

@app.route('/documents', methods=['POST'])
def create_document():
    data = request.json
    document = {
        "user_id": data.get("user_id"),
        "text": data.get("text"),
        "is_public": data.get("is_public", True)  # Default to public if not provided
    }
    result = documents_collection.insert_one(document)
    return jsonify({"message": "Document created", "document_id": str(result.inserted_id)}), 201

@app.route('/documents/<document_id>', methods=['GET'])
def get_document(document_id):
    document = documents_collection.find_one({"_id": ObjectId(document_id)})
    if document:
        # Check if the document is public or belongs to the requesting user
        if document.get("is_public") or document.get("user_id") == request.json.get("user_id"):
            document["_id"] = str(document["_id"])  # Convert ObjectId to string for JSON response
            return jsonify(document), 200
        else:
            return jsonify({"error": "Unauthorized access to private document"}), 403
    return jsonify({"error": "Document not found"}), 404

@app.route('/documents/<document_id>', methods=['PUT'])
def update_document(document_id):
    data = request.json
    document = documents_collection.find_one({"_id": ObjectId(document_id)})
    if document and document["user_id"] == data.get("user_id"):
        update_data = {
            "text": data.get("text", document["text"]),
            "is_public": data.get("is_public", document["is_public"])
        }
        documents_collection.update_one({"_id": ObjectId(document_id)}, {"$set": update_data})
        return jsonify({"message": "Document updated"}), 200
    return jsonify({"error": "Unauthorized or document not found"}), 403

@app.route('/documents/<document_id>', methods=['DELETE'])
def delete_document(document_id):
    data = request.json
    document = documents_collection.find_one({"_id": ObjectId(document_id)})
    if document and document["user_id"] == data.get("user_id"):
        documents_collection.delete_one({"_id": ObjectId(document_id)})
        return jsonify({"message": "Document deleted"}), 200
    return jsonify({"error": "Unauthorized or document not found"}), 403

# Status endpoint
@app.route('/status', methods=['GET'])
def status():
    return jsonify({"status": "Document Service is running"}), 200

if __name__ == "__main__":
    app.run(port=5003)
