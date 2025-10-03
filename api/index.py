"""
DroidX - Production-Ready F-Droid Repository API
====================================================

A high-performance, production-grade API for accessing F-Droid repository data.
Features unlimited requests, full CORS support, and millisecond response times.

Author: DroidX Team
Version: 1.0.0
License: MIT
"""

from flask import Flask, jsonify, request, Response
from flask_cors import CORS
from functools import wraps
from typing import Dict, List, Any, Optional, Tuple
import json
import os
import time
import logging
from datetime import datetime

# =============================================================================
# APPLICATION SETUP
# =============================================================================

app = Flask(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Enable CORS for all origins with comprehensive configuration
CORS(app, resources={
    r"/*": {
        "origins": "*",
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization", "Accept", "Origin"],
        "expose_headers": ["Content-Type", "X-Response-Time"],
        "supports_credentials": False,
        "max_age": 3600
    }
})

# =============================================================================
# CONFIGURATION
# =============================================================================

class Config:
    """Application configuration"""
    # Use absolute path for data file to work in serverless environment
    DATA_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'apps.json')
    API_VERSION = '1.0.0'
    API_NAME = 'DroidX'
    MAX_SEARCH_RESULTS = None
    CACHE_CONTROL = 'no-cache, no-store, must-revalidate'


# =============================================================================
# DATA STORE
# =============================================================================

class DataStore:
    """
    Thread-safe data store for application data.
    Loads data from JSON file on initialization.
    """
    
    def __init__(self, data_file: str):
        """
        Initialize data store with data file path.
        
        Args:
            data_file: Path to the JSON data file
        """
        self.data_file = data_file
        self._apps: List[Dict[str, Any]] = []
        self._metadata: Dict[str, Any] = {}
        self._last_loaded: Optional[float] = None
        self.load_data()
    
    def load_data(self) -> None:
        """
        Load application data from JSON file.
        
        Raises:
            FileNotFoundError: If data file doesn't exist
            JSONDecodeError: If data file is not valid JSON
        """
        try:
            if not os.path.exists(self.data_file):
                logger.error(f"Data file not found: {self.data_file}")
                raise FileNotFoundError(f"Data file not found: {self.data_file}")
            
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self._apps = data.get('apps', [])
            self._metadata = {
                'last_updated': data.get('last_updated'),
                'apps_count': len(self._apps),
                'loaded_at': datetime.utcnow().isoformat() + 'Z'
            }
            self._last_loaded = time.time()
            
            logger.info(f"Successfully loaded {len(self._apps)} apps from {self.data_file}")
            
        except FileNotFoundError as e:
            logger.error(f"Data file not found: {e}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in data file: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error loading data: {e}")
            raise
    
    def get_all_apps(self) -> List[Dict[str, Any]]:
        """Get all applications."""
        return self._apps
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get metadata about the data store."""
        return self._metadata
    
    def find_app_by_id(self, app_id: str) -> Optional[Dict[str, Any]]:
        """
        Find an application by its ID.
        
        Args:
            app_id: The application ID to search for
            
        Returns:
            Application data if found, None otherwise
        """
        return next((app for app in self._apps if app.get('id') == app_id), None)
    
    def search_apps(self, query: str) -> List[Dict[str, Any]]:
        """
        Search applications by query string.
        Searches in name, summary, description, and ID fields.
        
        Args:
            query: Search query string
            
        Returns:
            List of matching applications
        """
        query_lower = query.lower()
        results = []
        
        for app in self._apps:
            name = (app.get('name') or '').lower()
            summary = (app.get('summary') or '').lower()
            description = (app.get('description') or '').lower()
            app_id = (app.get('id') or '').lower()
            
            if (query_lower in name or 
                query_lower in summary or 
                query_lower in description or 
                query_lower in app_id):
                results.append(app)
        
        return results
    
    def get_apps_by_category(self, category: str) -> List[Dict[str, Any]]:
        """
        Get all applications in a specific category.
        
        Args:
            category: Category name
            
        Returns:
            List of applications in the category
        """
        return [
            app for app in self._apps 
            if category in app.get('categories', [])
        ]
    
    def get_all_categories(self) -> List[Dict[str, Any]]:
        """
        Get all categories with application counts.
        
        Returns:
            List of category dictionaries with name and count
        """
        categories: Dict[str, int] = {}
        
        for app in self._apps:
            for cat in app.get('categories', []):
                if cat:
                    categories[cat] = categories.get(cat, 0) + 1
        
        return [
            {'name': cat, 'count': count}
            for cat, count in sorted(
                categories.items(), 
                key=lambda x: x[1], 
                reverse=True
            )
        ]


# Initialize data store
try:
    data_store = DataStore(Config.DATA_FILE)
except Exception as e:
    logger.critical(f"Failed to initialize data store: {e}")
    # Create empty data store to prevent crashes
    data_store = None


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def is_game(app: Dict[str, Any]) -> bool:
    """
    Determine if an application is a game based on its categories.
    
    Args:
        app: Application dictionary
        
    Returns:
        True if application is a game, False otherwise
    """
    game_categories = {'Games', 'Game'}
    return any(cat in game_categories for cat in app.get('categories', []))


def timing_decorator(f):
    """
    Decorator to measure and add response time to API responses.
    
    Args:
        f: Function to decorate
        
    Returns:
        Wrapped function with timing measurement
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = f(*args, **kwargs)
        elapsed_ms = round((time.time() - start_time) * 1000, 2)
        
        # Add timing to response
        if isinstance(result, tuple):
            data, status = result
            if isinstance(data, dict):
                data['_response_time_ms'] = elapsed_ms
            return data, status
        
        return result
    
    return wrapper


def create_error_response(
    message: str, 
    status_code: int = 400,
    error_code: Optional[str] = None
) -> Tuple[Dict[str, Any], int]:
    """
    Create a standardized error response.
    
    Args:
        message: Error message
        status_code: HTTP status code
        error_code: Optional error code for programmatic handling
        
    Returns:
        Tuple of (response_dict, status_code)
    """
    response = {
        'success': False,
        'error': {
            'message': message,
            'code': error_code or f'ERROR_{status_code}',
            'status': status_code
        },
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }
    return response, status_code


def create_success_response(
    data: Any,
    message: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Create a standardized success response.
    
    Args:
        data: Response data
        message: Optional success message
        **kwargs: Additional fields to include in response
        
    Returns:
        Response dictionary
    """
    response = {
        'success': True,
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        **kwargs
    }
    
    if message:
        response['message'] = message
    
    # Handle different data types
    if isinstance(data, list):
        response['data'] = data
        response['count'] = len(data)
    elif isinstance(data, dict):
        response.update(data)
    else:
        response['data'] = data
    
    return response


# =============================================================================
# ERROR HANDLERS
# =============================================================================

@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors."""
    logger.warning(f"404 error: {request.url}")
    return create_error_response(
        'Endpoint not found',
        404,
        'ENDPOINT_NOT_FOUND'
    )


@app.errorhandler(405)
def method_not_allowed_error(error):
    """Handle 405 errors."""
    logger.warning(f"405 error: {request.method} {request.url}")
    return create_error_response(
        f'Method {request.method} not allowed for this endpoint',
        405,
        'METHOD_NOT_ALLOWED'
    )


@app.errorhandler(500)
def internal_server_error(error):
    """Handle 500 errors."""
    logger.error(f"500 error: {error}")
    return create_error_response(
        'Internal server error occurred',
        500,
        'INTERNAL_SERVER_ERROR'
    )


@app.errorhandler(Exception)
def handle_unexpected_error(error):
    """Handle unexpected errors."""
    logger.error(f"Unexpected error: {error}", exc_info=True)
    return create_error_response(
        'An unexpected error occurred',
        500,
        'UNEXPECTED_ERROR'
    )


# =============================================================================
# MIDDLEWARE
# =============================================================================

@app.before_request
def before_request():
    """Execute before each request."""
    # Log request
    logger.info(f"{request.method} {request.path} from {request.remote_addr}")
    
    # Check if data store is available
    if data_store is None:
        return create_error_response(
            'Service temporarily unavailable - data not loaded',
            503,
            'DATA_NOT_AVAILABLE'
        )


@app.after_request
def after_request(response: Response) -> Response:
    """
    Execute after each request.
    Add additional headers for security and caching.
    
    Args:
        response: Flask response object
        
    Returns:
        Modified response object
    """
    # Add CORS headers
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    
    # Add cache control headers (no caching)
    response.headers['Cache-Control'] = Config.CACHE_CONTROL
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    
    # Add security headers
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    
    return response


# =============================================================================
# API ENDPOINTS
# =============================================================================

@app.route('/', methods=['GET'])
@timing_decorator
def index():
    """
    API root endpoint - provides API documentation.
    
    Returns:
        API information and available endpoints
    """
    return create_success_response({
        'name': Config.API_NAME,
        'version': Config.API_VERSION,
        'description': 'Production-ready F-Droid repository API with unlimited requests',
        'documentation': 'https://github.com/iambhvsh/droidx',
        'endpoints': {
            'GET /': 'API documentation (this page)',
            'GET /health': 'Health check endpoint',
            'GET /apps': 'Get all applications (excluding games)',
            'GET /games': 'Get all games',
            'GET /all': 'Get all apps and games',
            'GET /app/<app_id>': 'Get specific application by ID',
            'GET /search?q=<query>': 'Search applications',
            'GET /categories': 'Get all categories with counts',
            'GET /category/<name>': 'Get apps in specific category',
            'GET /latest?limit=<n>': 'Get recently updated apps',
            'GET /random': 'Get random application',
            'GET /stats': 'Get repository statistics'
        },
        'features': [
            'No rate limits - unlimited requests',
            'Full CORS support for all origins',
            'Sub-millisecond response times',
            'Comprehensive error handling',
            'Daily automated data updates',
            'Production-grade reliability'
        ],
        'metadata': data_store.get_metadata() if data_store else None
    })


@app.route('/health', methods=['GET'])
@timing_decorator
def health_check():
    """
    Health check endpoint for monitoring and load balancers.
    
    Returns:
        Health status and system information
    """
    if data_store is None:
        return create_error_response(
            'Data store not initialized',
            503,
            'UNHEALTHY'
        )
    
    metadata = data_store.get_metadata()
    
    return create_success_response({
        'status': 'healthy',
        'uptime': 'operational',
        'data': {
            'apps_loaded': metadata.get('apps_count', 0),
            'last_updated': metadata.get('last_updated'),
            'loaded_at': metadata.get('loaded_at')
        }
    })


@app.route('/apps', methods=['GET'])
@timing_decorator
def get_apps():
    """
    Get all applications (excluding games).
    
    Returns:
        List of all non-game applications
    """
    if data_store is None:
        return create_error_response('Data not available', 503)
    
    all_apps = data_store.get_all_apps()
    apps = [app for app in all_apps if not is_game(app)]
    
    return create_success_response(
        apps,
        total=len(all_apps),
        games=len(all_apps) - len(apps)
    )


@app.route('/games', methods=['GET'])
@timing_decorator
def get_games():
    """
    Get all games.
    
    Returns:
        List of all game applications
    """
    if data_store is None:
        return create_error_response('Data not available', 503)
    
    all_apps = data_store.get_all_apps()
    games = [app for app in all_apps if is_game(app)]
    
    return create_success_response(
        games,
        total=len(all_apps),
        non_games=len(all_apps) - len(games)
    )


@app.route('/all', methods=['GET'])
@timing_decorator
def get_all():
    """
    Get all applications and games.
    
    Returns:
        Complete list of all applications
    """
    if data_store is None:
        return create_error_response('Data not available', 503)
    
    all_apps = data_store.get_all_apps()
    
    return create_success_response(all_apps)


@app.route('/app/<app_id>', methods=['GET'])
@timing_decorator
def get_app(app_id: str):
    """
    Get detailed information about a specific application.
    
    Args:
        app_id: Application identifier
        
    Returns:
        Application details or 404 error
    """
    if data_store is None:
        return create_error_response('Data not available', 503)
    
    if not app_id or not app_id.strip():
        return create_error_response(
            'App ID cannot be empty',
            400,
            'INVALID_APP_ID'
        )
    
    app = data_store.find_app_by_id(app_id)
    
    if app is None:
        return create_error_response(
            f'Application with ID "{app_id}" not found',
            404,
            'APP_NOT_FOUND'
        )
    
    return create_success_response({'app': app})


@app.route('/search', methods=['GET'])
@timing_decorator
def search():
    """
    Search applications by query string.
    Searches across name, summary, description, and ID fields.
    
    Query Parameters:
        q: Search query (required)
        
    Returns:
        List of matching applications
    """
    if data_store is None:
        return create_error_response('Data not available', 503)
    
    query = request.args.get('q', '').strip()
    
    if not query:
        return create_error_response(
            'Query parameter "q" is required and cannot be empty',
            400,
            'MISSING_QUERY'
        )
    
    if len(query) < 2:
        return create_error_response(
            'Query must be at least 2 characters long',
            400,
            'QUERY_TOO_SHORT'
        )
    
    results = data_store.search_apps(query)
    
    return create_success_response(
        results,
        query=query
    )


@app.route('/categories', methods=['GET'])
@timing_decorator
def get_categories():
    """
    Get all categories with application counts.
    
    Returns:
        List of categories sorted by app count (descending)
    """
    if data_store is None:
        return create_error_response('Data not available', 503)
    
    categories = data_store.get_all_categories()
    
    return create_success_response(
        categories,
        message=f'Found {len(categories)} categories'
    )


@app.route('/category/<category_name>', methods=['GET'])
@timing_decorator
def get_category_apps(category_name: str):
    """
    Get all applications in a specific category.
    
    Args:
        category_name: Name of the category
        
    Returns:
        List of applications in the category
    """
    if data_store is None:
        return create_error_response('Data not available', 503)
    
    if not category_name or not category_name.strip():
        return create_error_response(
            'Category name cannot be empty',
            400,
            'INVALID_CATEGORY'
        )
    
    apps = data_store.get_apps_by_category(category_name)
    
    if not apps:
        # Check if category exists
        all_categories = data_store.get_all_categories()
        category_exists = any(cat['name'] == category_name for cat in all_categories)
        
        if not category_exists:
            return create_error_response(
                f'Category "{category_name}" not found',
                404,
                'CATEGORY_NOT_FOUND'
            )
    
    return create_success_response(
        apps,
        category=category_name
    )


@app.route('/latest', methods=['GET'])
@timing_decorator
def get_latest():
    """
    Get recently updated applications.
    
    Query Parameters:
        limit: Maximum number of apps to return (optional)
        
    Returns:
        List of recently updated applications
    """
    if data_store is None:
        return create_error_response('Data not available', 503)
    
    # Get limit parameter
    limit = request.args.get('limit', type=int)
    
    if limit is not None and limit < 1:
        return create_error_response(
            'Limit must be a positive integer',
            400,
            'INVALID_LIMIT'
        )
    
    all_apps = data_store.get_all_apps()
    
    # Filter apps with last_updated field and sort
    apps_with_dates = [app for app in all_apps if app.get('last_updated')]
    sorted_apps = sorted(
        apps_with_dates,
        key=lambda x: x.get('last_updated', ''),
        reverse=True
    )
    
    # Apply limit if specified
    if limit:
        sorted_apps = sorted_apps[:limit]
    
    return create_success_response(
        sorted_apps,
        limited=limit is not None,
        limit=limit
    )


@app.route('/random', methods=['GET'])
@timing_decorator
def get_random():
    """
    Get a random application.
    
    Returns:
        Random application from the repository
    """
    if data_store is None:
        return create_error_response('Data not available', 503)
    
    import random
    
    all_apps = data_store.get_all_apps()
    
    if not all_apps:
        return create_error_response(
            'No applications available',
            404,
            'NO_APPS'
        )
    
    random_app = random.choice(all_apps)
    
    return create_success_response({'app': random_app})


@app.route('/stats', methods=['GET'])
@timing_decorator
def get_stats():
    """
    Get comprehensive repository statistics.
    
    Returns:
        Statistical information about the repository
    """
    if data_store is None:
        return create_error_response('Data not available', 503)
    
    all_apps = data_store.get_all_apps()
    games = [app for app in all_apps if is_game(app)]
    
    # Gather statistics
    categories = set()
    total_packages = 0
    licenses = {}
    apps_with_source = 0
    apps_with_website = 0
    
    for app in all_apps:
        # Categories
        categories.update(app.get('categories', []))
        
        # Packages
        total_packages += len(app.get('packages', []))
        
        # Licenses
        license_name = app.get('license')
        if license_name:
            licenses[license_name] = licenses.get(license_name, 0) + 1
        
        # Source code availability
        if app.get('source_code'):
            apps_with_source += 1
        
        # Website availability
        if app.get('website'):
            apps_with_website += 1
    
    # Top licenses
    top_licenses = sorted(
        licenses.items(),
        key=lambda x: x[1],
        reverse=True
    )[:10]
    
    return create_success_response({
        'statistics': {
            'total_apps': len(all_apps),
            'total_games': len(games),
            'total_non_games': len(all_apps) - len(games),
            'total_categories': len(categories),
            'total_packages': total_packages,
            'unique_licenses': len(licenses),
            'apps_with_source_code': apps_with_source,
            'apps_with_website': apps_with_website,
            'top_licenses': [
                {'license': lic, 'count': count}
                for lic, count in top_licenses
            ]
        },
        'metadata': data_store.get_metadata()
    })


# =============================================================================
# VERCEL SERVERLESS HANDLER
# =============================================================================

# Export the Flask app for Vercel's Python runtime
# Vercel automatically detects and uses the 'app' variable
# No additional handler wrapper is needed


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

if __name__ == '__main__':
    # Development server
    logger.info(f"Starting {Config.API_NAME} API v{Config.API_VERSION}")
    logger.info(f"Data file: {Config.DATA_FILE}")
    app.run(
        debug=False,
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 5000)),
        threaded=True
    )
