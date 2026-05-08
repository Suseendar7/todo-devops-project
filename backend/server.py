from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
import subprocess
import shutil
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

client = MongoClient("mongodb://mongo:27017/")
db = client["devops_db"]
collection = db["builds"]

REPO_DIR = "repo"

@app.route("/")
def home():
    return {
        "service": "DevOps Build System",
        "status": "running",
        "version": "1.0"
    }

@app.route("/build", methods=["POST"])
def build_repo():

    data = request.json
    repo_url = data.get("repo")

    if not repo_url:
        return jsonify({"error": "Repository URL required"}), 400

    # Delete old repo folder
    if os.path.exists(REPO_DIR):
        shutil.rmtree(REPO_DIR)

    logs = ""

    try:

        # Clone repo
        clone = subprocess.run(
            ["git", "clone", repo_url, REPO_DIR],
            capture_output=True,
            text=True
        )

        logs += clone.stdout + clone.stderr

        if clone.returncode != 0:
            raise Exception("Clone failed")

        # Build docker image
        build = subprocess.run(
            ["docker", "build", "-t", "ci-build", REPO_DIR],
            capture_output=True,
            text=True
        )

        logs += build.stdout + build.stderr

        if build.returncode == 0:
            status = "SUCCESS"
        else:
            status = "FAILED"

    except Exception as e:
        status = "FAILED"
        logs += str(e)

    # Save build history
    collection.insert_one({
        "repo": repo_url,
        "status": status,
        "logs": logs,
        "time": str(datetime.now())
    })

    return jsonify({
        "status": status,
        "logs": logs[-1000:]
    })

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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)