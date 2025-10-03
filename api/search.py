from flask import Flask, request, jsonify
import json
from pathlib import Path

app = Flask(__name__)

def load_apps():
    """Load apps from cache"""
    cache_file = Path(__file__).parent.parent / 'cache' / 'apps.json'
    with open(cache_file, 'r', encoding='utf-8') as f:
        return json.load(f)

@app.route('/api/search')
def search_apps():
    """Search apps by name or summary with unlimited results"""
    query = request.args.get('q', '').lower()
    
    if not query:
        return jsonify({"error": "Search query 'q' is required"}), 400
    
    try:
        limit = int(request.args.get('limit', 20)) if request.args.get('limit') else None
        offset = int(request.args.get('offset', 0))
        categories = [cat.strip() for cat in request.args.get('categories', '').split(',') if cat.strip()] if request.args.get('categories') else None
        sort_by = request.args.get('sort', 'name')
        order = request.args.get('order', 'asc')
    except ValueError:
        return jsonify({"error": "Invalid limit, offset, or sort parameters"}), 400
    
    if sort_by not in ['name', 'version', 'versionCode', 'id']:
        return jsonify({"error": "Invalid sort field. Use: name, version, versionCode, or id"}), 400
    
    if order not in ['asc', 'desc']:
        return jsonify({"error": "Invalid order. Use: asc or desc"}), 400
    
    apps = load_apps()
    
    filtered_apps = [
        app for app in apps
        if query in app['name'].lower() or query in app['summary'].lower()
    ]
    
    if categories:
        filtered_apps = [
            app for app in filtered_apps
            if any(cat in app.get('categories', []) for cat in categories)
        ]
    
    sorted_apps = sorted(filtered_apps, key=lambda x: x.get(sort_by, ''), reverse=(order == 'desc'))
    
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

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Endpoint not found"}), 404
