from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient

app = Flask(__name__)
CORS(app)

client = MongoClient("mongodb://mongo:27017/")
db = client["todo_db"]
collection = db["tasks"]

@app.route("/")
def home():
    return "Todo Backend Running!"

@app.route("/tasks", methods=["GET"])
def get_tasks():
    tasks = []
    for t in collection.find():
        tasks.append(t["task"])
    return jsonify(tasks)

@app.route("/tasks", methods=["POST"])
def add_task():
    data = request.json

    if not data or "task" not in data:
        return jsonify({"error": "Task is required"}), 400

    try:
        collection.insert_one({"task": data["task"]})
        return jsonify({"message": "Task added"})
    except:
        return jsonify({"error": "Failed to add task"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)