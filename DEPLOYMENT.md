# Vercel Deployment Guide

## Overview
This project is configured for automatic deployment on Vercel's serverless platform.

## Configuration

### Files
- `vercel.json` - Vercel deployment configuration
- `.vercelignore` - Files to exclude from deployment
- `.gitignore` - Files to exclude from git
- `requirements.txt` - Python dependencies
- `api/index.py` - Main Flask application (serverless function)
- `data/apps.json` - Application data (8.8MB)

### Vercel Configuration
The `vercel.json` uses the modern rewrite format:
```json
{
  "rewrites": [
    {
      "source": "/(.*)",
      "destination": "/api/index"
    }
  ]
}
```

All requests are routed to the Flask app at `api/index.py`, which Vercel automatically detects and deploys as a Python serverless function.

## Deployment Steps

### First Time Setup
1. Install Vercel CLI: `npm i -g vercel`
2. Login: `vercel login`
3. Link project: `vercel link`
4. Deploy: `vercel --prod`

### Environment Variables
Set in Vercel Dashboard or via CLI:
```bash
vercel env add PYTHONUNBUFFERED
# Value: 1
```

### Runtime Settings (Vercel Dashboard)
Recommended settings for this project:
- **Runtime**: Python 3.9+ (auto-detected)
- **Memory**: 1024 MB (default)
- **Max Duration**: 10s (sufficient for most endpoints)
- **Region**: Auto (or select based on your users)

## Troubleshooting

### Issue: 500 Internal Server Error
**Solution**: Check function logs in Vercel dashboard
- Ensure `data/apps.json` exists and is valid JSON
- Verify all dependencies in `requirements.txt` are installed
- Check that file paths are absolute (already configured)

### Issue: Build Cache Not Working
**Solution**: Vercel automatically caches dependencies
- The `.vercelignore` excludes unnecessary files
- Build cache is handled automatically by Vercel

### Issue: Data File Not Found
**Solution**: Verify data file is committed to git
```bash
git add data/apps.json
git commit -m "Add data file"
git push
```

### Issue: Deployment Timeout
**Solution**: The API should respond quickly
- Most endpoints respond in < 100ms
- The `/all` endpoint might be slower with large datasets
- Consider pagination for large responses if needed

## Local Development

### Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
python api/index.py
```

### Testing
```bash
# Test specific endpoint
curl http://localhost:5000/health

# Test with Python
python -c "from api.index import app; app.test_client().get('/health')"
```

## API Endpoints
All endpoints are documented at the root path:
```bash
curl https://your-app.vercel.app/
```

## Data Updates
The `data/apps.json` file is automatically updated daily via GitHub Actions workflow.
See `.github/workflows/main.yml` for details.

## Performance Optimization

### Current Optimizations
- Absolute file paths for serverless environment
- No external database dependencies
- In-memory data loading (fast access)
- CORS enabled for all origins
- Comprehensive caching headers

### Monitoring
- Check function invocations in Vercel dashboard
- Monitor response times via `_response_time_ms` field
- Review error logs for issues

## Support
For issues related to:
- Vercel deployment: Check Vercel documentation
- API functionality: Check repository issues
- Data updates: Check GitHub Actions workflow logs
