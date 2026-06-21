import traceback
from flask import jsonify

def register_error_handlers(app):
    @app.errorhandler(Exception)
    def handle_exception(e):
        # pass through HTTP errors
        if hasattr(e, 'code') and isinstance(e.code, int) and e.code < 500:
            return e
            
        return jsonify({
            "error": "Internal Server Error",
            "message": str(e),
            "traceback": traceback.format_exc().split('\n')
        }), 500
