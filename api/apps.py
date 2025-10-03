from flask import Flask, request, jsonify
import json
import os
from pathlib import Path

app = Flask(__name__)

def load_apps():
    """Load apps from cache"""
    cache_file = Path(__file__).parent.parent / 'cache' / 'apps.json'
    with open(cache_file, 'r', encoding='utf-8') as f:
        return json.load(f)

@app.route('/api/apps')
def get_apps():
    """Get paginated list of all apps with sorting options"""
    try:
        limit = int(request.args.get('limit', 20)) if request.args.get('limit') else None
        offset = int(request.args.get('offset', 0))
        sort_by = request.args.get('sort', 'name')
        order = request.args.get('order', 'asc')
    except ValueError:
        return jsonify({"error": "Invalid limit, offset, or sort parameters"}), 400
    
    if sort_by not in ['name', 'version', 'versionCode', 'id']:
        return jsonify({"error": "Invalid sort field. Use: name, version, versionCode, or id"}), 400
    
    if order not in ['asc', 'desc']:
        return jsonify({"error": "Invalid order. Use: asc or desc"}), 400
    
    apps = load_apps()
    
    sorted_apps = sorted(apps, key=lambda x: x.get(sort_by, ''), reverse=(order == 'desc'))
    
    total = len(sorted_apps)
    
    if limit:
        paginated_apps = sorted_apps[offset:offset + limit]
    else:
        paginated_apps = sorted_apps[offset:]
    
    return jsonify({
        "total": total,
        "count": len(paginated_apps),
        "results": paginated_apps
    })

@app.route('/api/apps/<path:app_id>')
def get_app(app_id):
    """Get single app by package name"""
    if not app_id or app_id.strip() == '':
        return jsonify({"error": "App ID is required"}), 400
    
    apps = load_apps()
    
    for app in apps:
        if app['id'] == app_id:
            return jsonify(app)
    
    return jsonify({
        "error": "App not found",
        "message": f"No app with ID '{app_id}' exists in the repository"
    }), 404

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Endpoint not found"}), 404
