from flask import Flask, jsonify
import json
import random
from pathlib import Path

app = Flask(__name__)

def load_apps():
    """Load apps from cache"""
    cache_file = Path(__file__).parent.parent / 'cache' / 'apps.json'
    with open(cache_file, 'r', encoding='utf-8') as f:
        return json.load(f)

@app.route('/api/random')
def get_random_app():
    """Get a random app"""
    apps = load_apps()
    
    if not apps:
        return jsonify({"error": "No apps available"}), 404
    
    random_app = random.choice(apps)
    return jsonify(random_app)

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Endpoint not found"}), 404
