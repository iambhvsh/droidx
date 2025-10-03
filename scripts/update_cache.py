#!/usr/bin/env python3
import json
import requests
import os
from pathlib import Path

def download_fdroid_index():
    """Download F-Droid index and extract relevant app data"""
    print("Downloading F-Droid index...")
    response = requests.get("https://f-droid.org/repo/index-v1.json", timeout=60)
    response.raise_for_status()
    
    full_index = response.json()
    apps_data = []
    
    apps_list = full_index.get('apps', [])
    packages_dict = full_index.get('packages', {})
    
    print(f"Processing {len(apps_list)} apps...")
    
    apps_by_id = {}
    for app in apps_list:
        apps_by_id[app.get('packageName')] = app
    
    for package_name, package_info in packages_dict.items():
        app_metadata = apps_by_id.get(package_name, {})
        
        if not package_info or not isinstance(package_info, list):
            continue
            
        latest_version = package_info[0] if package_info else {}
        
        app_entry = {
            "id": package_name,
            "name": app_metadata.get('name', {}).get('en-US', package_name) if isinstance(app_metadata.get('name'), dict) else app_metadata.get('name', package_name),
            "summary": app_metadata.get('summary', {}).get('en-US', '') if isinstance(app_metadata.get('summary'), dict) else app_metadata.get('summary', ''),
            "categories": app_metadata.get('categories', ['Uncategorized']),
            "version": latest_version.get('versionName', ''),
            "versionCode": latest_version.get('versionCode', 0),
            "apkUrl": f"https://f-droid.org/repo/{latest_version.get('apkName', '')}" if latest_version.get('apkName') else ""
        }
        
        apps_data.append(app_entry)
    
    cache_dir = Path(__file__).parent.parent / 'cache'
    cache_dir.mkdir(exist_ok=True)
    
    output_file = cache_dir / 'apps.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(apps_data, f, indent=2, ensure_ascii=False)
    
    print(f"Successfully cached {len(apps_data)} apps to {output_file}")

if __name__ == "__main__":
    download_fdroid_index()
