import sys
import os
import traceback

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, jsonify

# Define 'app' at the absolute top-level so Vercel's static parser finds it
app = Flask(__name__)

try:
    from app import create_app
    # Overwrite the dummy app with our real app
    app = create_app()
except Exception as e:
    # If startup fails, surface the error on all routes
    _error = traceback.format_exc()
    
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def catch_all(path):
        return jsonify({
            "error": "Application startup failed",
            "message": str(e),
            "traceback": _error.split('\n')
        }), 500
