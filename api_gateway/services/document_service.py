from flask import Flask, request, jsonify
from pymongo import MongoClient
from bson import ObjectId
import jwt

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret_key'

# MongoDB configuration
client = MongoClient("mongodb://localhost:27017/")
db = client['mydatabase']
documents_collection = db['documents']

# Decode Token to get username
def decode_token(token):
    try:
        decoded_data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
        return decoded_data['username']
    except jwt.ExpiredSignatureError:
        return "Token has expired"
    except jwt.InvalidTokenError:
        return "Invalid token"

# Create a document
@app.route('/documents', methods=['POST'])
def create_document():
    data = request.json
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
    else:
        print("Invalid or Missing Authorization Header")
    username = decode_token(token)
    document = {
        "user_id": username,
        "text": data.get("text"),
        "is_public": data.get("is_public", True)
    }
    result = documents_collection.insert_one(document)
    return jsonify({"message": "Document created", "document_id": str(result.inserted_id)}), 201

# Get a document
@app.route('/documents/<document_id>', methods=['GET'])
def get_document(document_id):
    user_id = request.args.get('user_id')
    document = documents_collection.find_one({"_id": ObjectId(document_id)})
    if document:
        # Check if the document is public or belongs to the requesting user
        if document.get("is_public") or document.get("user_id") == user_id:
            document["_id"] = str(document["_id"]) 
            return jsonify(document), 200
        else:
            return jsonify({"error": "Unauthorized access to private document"}), 403
    return jsonify({"error": "Document not found"}), 404

# Update Document
@app.route('/documents/<document_id>', methods=['PUT'])
def update_document(document_id):
    data = request.json
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1] 
    else:
        print("Invalid or Missing Authorization Header")
    username = decode_token(token)
    document = documents_collection.find_one({"_id": ObjectId(document_id)})
    if document and document["user_id"] == username:
        update_data = {
            "text": data.get("text", document["text"]),
            "is_public": data.get("is_public", document["is_public"])
        }
        documents_collection.update_one({"_id": ObjectId(document_id)}, {"$set": update_data})
        return jsonify({"message": "Document updated"}), 200
    return jsonify({"error": "Unauthorized or document not found"}), 403

# Delete a document
@app.route('/documents/<document_id>', methods=['DELETE'])
def delete_document(document_id):
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
    else:
        print("Invalid or Missing Authorization Header")
    username = decode_token(token)
    document = documents_collection.find_one({"_id": ObjectId(document_id)})
    if document and document["user_id"] == username:
        documents_collection.delete_one({"_id": ObjectId(document_id)})
        return jsonify({"message": "Document deleted"}), 200
    return jsonify({"error": "Unauthorized or document not found"}), 403

# Status endpoint
@app.route('/status', methods=['GET'])
def status():
    return jsonify({"status": "Document Service is running"}), 200

if __name__ == "__main__":
    app.run(port=5003)