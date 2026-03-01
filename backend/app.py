"""Flask application entry point."""
import os
from flask import Flask, send_from_directory

app = Flask(__name__, static_folder=None)
app.config["JSON_SORT_KEYS"] = False

# Register API blueprint
from backend.api.routes import api
app.register_blueprint(api)

# Serve frontend static files
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")


@app.route("/")
def index():
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.route("/css/<path:filename>")
def css(filename):
    return send_from_directory(os.path.join(FRONTEND_DIR, "css"), filename)


@app.route("/js/<path:filename>")
def js(filename):
    return send_from_directory(os.path.join(FRONTEND_DIR, "js"), filename)


@app.errorhandler(404)
def not_found(e):
    return {"error": "Not found"}, 404


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
