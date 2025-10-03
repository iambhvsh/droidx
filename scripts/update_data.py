#!/usr/bin/env python3
"""
F-Droid Cache Update Script
Downloads and parses the F-Droid repository index and saves it as JSON
"""

import requests
import xml.etree.ElementTree as ET
import json
import sys
from datetime import datetime

# F-Droid repository URLs
FDROID_REPO_URL = "https://f-droid.org/repo"
FDROID_INDEX_URL = f"{FDROID_REPO_URL}/index.xml"
FDROID_ICON_BASE = f"{FDROID_REPO_URL}/icons-640"

# Output file
CACHE_FILE = "fdroid_index_cache.json"

def get_text(element, tag):
    """Safely extract text from XML element"""
    child = element.find(tag)
    return child.text if child is not None and child.text else None

def fetch_and_parse_fdroid_index():
    """Fetch and parse F-Droid repository index"""
    print("Fetching F-Droid index from:", FDROID_INDEX_URL)
    
    try:
        response = requests.get(FDROID_INDEX_URL, timeout=60)
        response.raise_for_status()
        print(f"✓ Downloaded index ({len(response.content)} bytes)")
        
        print("Parsing XML...")
        root = ET.fromstring(response.content)
        apps_data = []
        
        total_apps = len(root.findall('application'))
        print(f"Found {total_apps} applications to process")
        
        for idx, app_elem in enumerate(root.findall('application'), 1):
            if idx % 100 == 0:
                print(f"Processing app {idx}/{total_apps}...")
            
            app_id = app_elem.get('id')
            
            app_info = {
                'id': app_id,
                'name': get_text(app_elem, 'name'),
                'summary': get_text(app_elem, 'summary'),
                'description': get_text(app_elem, 'desc'),
                'license': get_text(app_elem, 'license'),
                'categories': [cat.text for cat in app_elem.findall('category') if cat.text],
                'author': get_text(app_elem, 'author'),
                'email': get_text(app_elem, 'email'),
                'website': get_text(app_elem, 'web'),
                'source_code': get_text(app_elem, 'source'),
                'issue_tracker': get_text(app_elem, 'tracker'),
                'changelog': get_text(app_elem, 'changelog'),
                'donate': get_text(app_elem, 'donate'),
                'bitcoin': get_text(app_elem, 'bitcoin'),
                'litecoin': get_text(app_elem, 'litecoin'),
                'flattr': get_text(app_elem, 'flattr'),
                'liberapay': get_text(app_elem, 'liberapay'),
                'opencollective': get_text(app_elem, 'opencollective'),
                'added': get_text(app_elem, 'added'),
                'last_updated': get_text(app_elem, 'lastupdated'),
                'icon': f"{FDROID_ICON_BASE}/{app_id}.png" if app_id else None,
                'packages': []
            }
            
            # Parse package information
            for pkg in app_elem.findall('package'):
                package_info = {
                    'version_name': get_text(pkg, 'version'),
                    'version_code': get_text(pkg, 'versioncode'),
                    'apk_name': get_text(pkg, 'apkname'),
                    'hash': get_text(pkg, 'hash'),
                    'hash_type': get_text(pkg, 'hashtype'),
                    'size': get_text(pkg, 'size'),
                    'min_sdk': get_text(pkg, 'sdkver'),
                    'target_sdk': get_text(pkg, 'targetSdkVersion'),
                    'added': get_text(pkg, 'added'),
                    'permissions': [perm.text for perm in pkg.findall('.//uses-permission') if perm.text],
                    'features': [feat.text for feat in pkg.findall('.//uses-feature') if feat.text],
                    'nativecode': [nc.text for nc in pkg.findall('nativecode') if nc.text],
                }
                app_info['packages'].append(package_info)
            
            # Get latest version info
            if app_info['packages']:
                latest_pkg = app_info['packages'][0]
                app_info['latest_version'] = latest_pkg['version_name']
                app_info['latest_version_code'] = latest_pkg['version_code']
                app_info['apk_size'] = latest_pkg['size']
            
            apps_data.append(app_info)
        
        print(f"✓ Parsed {len(apps_data)} applications successfully")
        return apps_data
        
    except requests.RequestException as e:
        print(f"✗ Error downloading F-Droid index: {e}", file=sys.stderr)
        sys.exit(1)
    except ET.ParseError as e:
        print(f"✗ Error parsing XML: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"✗ Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)

def save_cache(apps_data):
    """Save parsed data to JSON file"""
    print(f"Saving cache to {CACHE_FILE}...")
    
    cache_data = {
        'last_updated': datetime.utcnow().isoformat() + 'Z',
        'apps_count': len(apps_data),
        'apps': apps_data
    }
    
    try:
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, ensure_ascii=False, separators=(',', ':'))
        
        import os
        file_size = os.path.getsize(CACHE_FILE)
        file_size_mb = file_size / (1024 * 1024)
        
        print(f"✓ Cache saved successfully!")
        print(f"  File: {CACHE_FILE}")
        print(f"  Size: {file_size_mb:.2f} MB ({file_size:,} bytes)")
        print(f"  Apps: {len(apps_data):,}")
        print(f"  Updated: {cache_data['last_updated']}")
        
    except Exception as e:
        print(f"✗ Error saving cache: {e}", file=sys.stderr)
        sys.exit(1)

def main():
    """Main execution function"""
    print("=" * 60)
    print("F-Droid Cache Update Script")
    print("=" * 60)
    print(f"Started at: {datetime.utcnow().isoformat()}Z")
    print()
    
    # Fetch and parse the index
    apps_data = fetch_and_parse_fdroid_index()
    
    # Save to cache file
    save_cache(apps_data)
    
    print()
    print("=" * 60)
    print("✓ Cache update completed successfully!")
    print("=" * 60)

if __name__ == '__main__':
    main()
