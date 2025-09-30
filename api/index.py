import sys
import os
import traceback

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Vercel looks for 'app' variable
# Make sure it's exposed at module level

app = None

try:
    from app import app as flask_app
    print("App imported successfully!")
    app = flask_app
except Exception as e:
    print(f"Error importing app: {e}")
    traceback.print_exc()
    
    # Create a minimal error app
    from flask import Flask, jsonify
    app = Flask(__name__)
    
    @app.route('/')
    def error():
        return jsonify({
            'error': 'Failed to import app',
            'message': str(e),
            'traceback': traceback.format_exc()
        }), 500
