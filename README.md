# DroidX API

A high-performance, production-grade API for accessing F-Droid repository data. Features unlimited requests, full CORS support, and millisecond response times.

## Features

- **No Rate Limits:** Unlimited requests for all endpoints.
- **Full CORS Support:** Access the API from any origin.
- **High Performance:** Sub-millisecond response times for most queries.
- **Comprehensive Error Handling:** Standardized error responses.
- **Daily Updates:** Application data is updated automatically every day.
- **Production-Ready:** Built for reliability and scalability.

## API Endpoints

Here is a list of available endpoints:

| Method | Endpoint                  | Description                                |
|--------|---------------------------|--------------------------------------------|
| GET    | `/`                       | Get API documentation and endpoint list.   |
| GET    | `/health`                 | Check the health status of the API.        |
| GET    | `/apps`                   | Get all applications (excluding games).    |
| GET    | `/games`                  | Get all game applications.                 |
| GET    | `/all`                    | Get a complete list of all apps and games. |
| GET    | `/app/<app_id>`           | Get details for a specific application.    |
| GET    | `/search?q=<query>`       | Search for applications.                   |
| GET    | `/categories`             | Get a list of all categories with counts.  |
| GET    | `/category/<name>`        | Get all apps in a specific category.       |
| GET    | `/latest?limit=<n>`       | Get the most recently updated applications.|
| GET    | `/random`                 | Get a random application.                  |
| GET    | `/stats`                  | Get repository statistics.                 |

## Basic Usage

### Get all apps
```bash
curl https://your-api-domain/apps
```

### Search for an app
```bash
curl https://your-api-domain/search?q=File%20Manager
```

### Get a specific app
```bash
curl https://your-api-domain/app/com.simplemobiletools.filemanager.pro
```