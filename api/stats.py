from flask import Flask, jsonify
import json
from collections import Counter
from pathlib import Path

app = Flask(__name__)

def load_apps():
    """Load apps from cache"""
    cache_file = Path(__file__).parent.parent / 'cache' / 'apps.json'
    with open(cache_file, 'r', encoding='utf-8') as f:
        return json.load(f)

@app.route('/api/stats')
def get_stats():
    """Get comprehensive API statistics"""
    apps = load_apps()
    
    all_categories = []
    for app in apps:
        all_categories.extend(app.get('categories', []))
    
    category_counts = Counter(all_categories)
    most_popular = category_counts.most_common(3)
    
    apps_with_summary = sum(1 for app in apps if app.get('summary'))
    apps_with_apk = sum(1 for app in apps if app.get('apkUrl'))
    
    return jsonify({
        "totalApps": len(apps),
        "totalCategories": len(set(all_categories)),
        "mostPopularCategories": [{"name": cat, "count": count} for cat, count in most_popular],
        "appsWithSummary": apps_with_summary,
        "appsWithAPK": apps_with_apk,
        "categoryDistribution": dict(category_counts.most_common(10))
    })

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Endpoint not found"}), 404
