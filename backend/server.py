from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
import subprocess
import shutil
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

# MongoDB connection
client = MongoClient("mongodb://mongo:27017/")
db = client["devops_db"]
collection = db["builds"]

# Folder name for cloned repo
REPO_DIR = "repo"

# Home route
@app.route("/")
def home():
    return {
        "service": "DevOps Build System",
        "status": "running",
        "version": "1.0"
    }

# Build repository route
@app.route("/build", methods=["POST"])
def build_repo():

    data = request.json
    repo_url = data.get("repo")

    if not repo_url:
        return jsonify({
            "error": "Repository URL required"
        }), 400

    # Remove old repo folder
    if os.path.exists(REPO_DIR):
        shutil.rmtree(REPO_DIR)

    logs = ""

    try:

        # Clone GitHub repo
        clone = subprocess.run(
            ["git", "clone", repo_url, REPO_DIR],
            capture_output=True,
            text=True
        )

        logs += clone.stdout + clone.stderr

        # Check clone success
        if clone.returncode != 0:
            raise Exception("Git clone failed")

        # Build Docker image
        build = subprocess.run(
            [
                "docker",
                "build",
                "-t",
                "ci-build",
                f"{REPO_DIR}/backend"
            ],
            capture_output=True,
            text=True
        )

        logs += build.stdout + build.stderr

        # Check build result
        if build.returncode == 0:
            status = "SUCCESS"
        else:
            status = "FAILED"

    except Exception as e:

        status = "FAILED"
        logs += "\n" + str(e)

    # Save build history
    collection.insert_one({
        "repo": repo_url,
        "status": status,
        "logs": logs,
        "time": str(datetime.now())
    })

    # Send response
    return jsonify({
        "status": status,
        "logs": logs[-1500:]
    })

# Build history route
@app.route("/history", methods=["GET"])
def history():

    builds = []

    for b in collection.find().sort("_id", -1):

        builds.append({
            "repo": b["repo"],
            "status": b["status"],
            "time": b["time"]
        })

    return jsonify(builds)

# Run Flask app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)