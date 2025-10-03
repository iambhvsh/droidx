from flask import Flask, request, jsonify
import json
from pathlib import Path

app = Flask(__name__)

def load_apps():
    """Load apps from cache"""
    cache_file = Path(__file__).parent.parent / 'cache' / 'apps.json'
    with open(cache_file, 'r', encoding='utf-8') as f:
        return json.load(f)

@app.route('/api/latest')
def get_latest_apps():
    """Get latest updated apps sorted by versionCode with no limit"""
    try:
        limit = int(request.args.get('limit', 10)) if request.args.get('limit') else 10
    except ValueError:
        return jsonify({"error": "Invalid limit"}), 400
    
    apps = load_apps()
    
    sorted_apps = sorted(apps, key=lambda x: x.get('versionCode', 0), reverse=True)
    
    if limit:
        latest_apps = sorted_apps[:limit]
    else:
        latest_apps = sorted_apps
    
    return jsonify({
        "count": len(latest_apps),
        "results": latest_apps
    })

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Endpoint not found"}), 404
