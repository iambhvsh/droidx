from flask import Flask, request, jsonify
import json
from pathlib import Path

app = Flask(__name__)

def load_apps():
    """Load apps from cache"""
    cache_file = Path(__file__).parent.parent / 'cache' / 'apps.json'
    with open(cache_file, 'r', encoding='utf-8') as f:
        return json.load(f)

@app.route('/api/categories')
def get_categories():
    """Get list of all unique categories"""
    apps = load_apps()
    
    categories = set()
    for app in apps:
        for category in app.get('categories', []):
            categories.add(category)
    
    categories_list = sorted(list(categories))
    
    return jsonify({
        "count": len(categories_list),
        "categories": categories_list
    })

@app.route('/api/categories/<path:category_name>')
def get_apps_by_category(category_name):
    """Get apps by category with pagination and sorting"""
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
    
    all_categories = set()
    for app in apps:
        all_categories.update(app.get('categories', []))
    
    if category_name not in all_categories:
        return jsonify({
            "error": "Category not found",
            "message": f"Category '{category_name}' does not exist in the repository"
        }), 404
    
    filtered_apps = [
        app for app in apps
        if category_name in app.get('categories', [])
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
        "category": category_name,
        "results": paginated_apps
    })

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Endpoint not found"}), 404
