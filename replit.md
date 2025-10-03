# F-Droid REST API

## Overview

This is a REST API service that provides access to F-Droid app repository data. The API wraps F-Droid's index data and exposes it through clean, paginated endpoints for searching, browsing, and discovering Android applications. The service is designed to be deployed on Vercel as a serverless function and includes a local development server for testing.

The API provides functionality for:
- Listing and retrieving app information
- Searching apps by name or summary
- Browsing apps by category
- Discovering random apps
- Finding latest updated apps
- Viewing repository statistics

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Architecture

**Framework**: Flask (Python 3.9)
- **Decision**: Flask was chosen for its simplicity and lightweight nature, making it ideal for serverless deployment
- **Rationale**: Minimal overhead, easy to split into individual route handlers for Vercel's function-based deployment model
- **Trade-off**: Limited built-in features compared to larger frameworks, but sufficient for this read-only API

**Deployment Model**: Serverless Functions (Vercel)
- **Decision**: Each API endpoint is a separate serverless function
- **Structure**: Individual route handlers in `/api` directory that can be deployed as isolated functions
- **Rationale**: Cost-effective, auto-scaling, and zero server maintenance
- **Configuration**: `vercel.json` handles routing rewrites to map clean URLs to function paths

**Development Server**: Flask development server (`dev_server.py`)
- **Decision**: Centralized Flask app for local development that mirrors production routing
- **Rationale**: Allows testing all endpoints locally without deploying to Vercel
- **Trade-off**: Development and production environments differ slightly in execution model

### Data Storage Strategy

**Primary Storage**: File-based JSON cache
- **Decision**: Apps data stored in `cache/apps.json` as a flat JSON file
- **Rationale**: F-Droid index updates infrequently; file-based caching is simple and eliminates database costs
- **Performance**: All endpoints load the entire dataset on each request (acceptable for moderate dataset sizes)
- **Update Mechanism**: Manual or scheduled execution of `scripts/update_cache.py`

**Data Source**: F-Droid Repository Index
- **Source URL**: `https://f-droid.org/repo/index-v1.json`
- **Update Script**: `scripts/update_cache.py` downloads and transforms the F-Droid index
- **Transformation**: Extracts relevant fields (id, name, summary, categories, version info, APK URL) from complex nested structure
- **Data Model**: Simplified app objects with essential metadata only
- **Automation**: GitHub Actions workflow runs daily to update cache and commit changes
- **Current Cache**: 3,923 apps across 60 categories (as of last update)

### API Design Patterns

**RESTful Endpoints**:
- `/apps` - List all apps with pagination
- `/apps/:id` - Get single app by package name
- `/search?q=term` - Search functionality
- `/categories` - List all categories
- `/categories/:name` - Filter apps by category
- `/random` - Random app discovery
- `/latest` - Latest updated apps (sorted by versionCode)
- `/stats` - Repository statistics

**Pagination Strategy**:
- **Pattern**: Offset-based pagination with `limit` and `offset` query parameters
- **Defaults**: 20 items per page, no maximum limit (omit `limit` for all results)
- **Response Format**: Includes `total`, `count`, and `results` fields
- **Unlimited Results**: Endpoints support unlimited results when `limit` parameter is omitted
- **Rationale**: Flexible pagination supporting both limited and complete dataset retrieval

**Sorting & Filtering** (Version 2.0):
- **Sorting**: Most endpoints support `sort` (name, version, versionCode, id) and `order` (asc, desc) parameters
- **Category Filtering**: Search endpoint supports multi-category filtering via comma-separated `categories` parameter
- **Whitespace Handling**: Category filters automatically normalize whitespace for flexible queries

**Error Handling**:
- **Approach**: JSON error responses with appropriate HTTP status codes
- **Validation**: Query parameter validation with 400 Bad Request responses
- **Not Found**: 404 responses for missing resources

### Module Organization

**Separation of Concerns**:
- **Decision**: Each endpoint group is a separate module in `/api`
- **Structure**: Each file contains its own Flask app instance and route handlers
- **Code Reuse**: Shared `load_apps()` helper function duplicated across modules
- **Rationale**: Vercel functions require each file to be independently executable
- **Trade-off**: Some code duplication, but enables isolated function deployment

## External Dependencies

### Third-Party Services

**F-Droid Repository**:
- **Service**: F-Droid official repository index
- **Endpoint**: `https://f-droid.org/repo/index-v1.json`
- **Purpose**: Source of truth for all app metadata
- **Update Frequency**: Manual/scheduled updates via update script
- **Data Format**: JSON index with apps and packages dictionaries

### Python Packages

**Flask** (v3.0.0):
- **Purpose**: Web framework for HTTP handling and routing
- **Usage**: Request handling, JSON responses, URL routing

**Requests** (v2.31.0):
- **Purpose**: HTTP client for downloading F-Droid index
- **Usage**: Used exclusively in `scripts/update_cache.py`

### Deployment Platform

**Vercel**:
- **Runtime**: Python 3.9 serverless functions
- **Configuration**: `vercel.json` defines function runtime and URL rewrites
- **Routing**: Path-based rewrites map clean URLs to `/api/*` function paths
- **Execution Model**: Each API module runs as an independent serverless function

### Automation

**GitHub Actions Workflow** (`.github/workflows/update.yml`):
- **Schedule**: Runs daily at midnight UTC (`cron: '0 0 * * *'`)
- **Trigger**: Also supports manual dispatch for on-demand updates
- **Process**:
  1. Checks out repository
  2. Sets up Python 3.11
  3. Installs requests library
  4. Executes `scripts/update_cache.py`
  5. Commits and pushes updated `cache/apps.json` (skips CI to prevent infinite loops)
- **Purpose**: Ensures API always serves fresh F-Droid app data without manual intervention