import sys
import os
import traceback

# Ensure project root is first in path so 'app' package resolves correctly
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

try:
    from app import create_app
    app = create_app()
except Exception as e:
    # Surface the error via a minimal Flask app so we can read logs
    from flask import Flask, jsonify
    app = Flask(__name__)
    _error = traceback.format_exc()

    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def catch_all(path):
        return jsonify({"error": str(e), "traceback": _error}), 500
