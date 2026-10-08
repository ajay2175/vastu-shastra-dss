# Vastu Shastra DSS API - Quick Start (5 minutes)

## 1. Install Dependencies (1 min)

```bash
cd /Users/ajaynawale/vastu_shastra_dss

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

## 2. Run the API (30 seconds)

```bash
# Start the API
python3 -m api.enhanced_api_v4
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

## 3. Test the API (2 minutes)

### Option A: Use Swagger UI (Interactive)
Open browser: http://localhost:8000/docs

You can:
- Click on endpoints
- Try requests directly
- See request/response examples

### Option B: Use curl

```bash
# Check health
curl http://localhost:8000/api/v1/health | jq '.'

# Get system status
curl http://localhost:8000/api/v1/status | jq '.'

# Main consultation
curl -X POST http://localhost:8000/api/v1/consult \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What about northeast direction?",
    "include_remedies": true
  }' | jq '.'

# Direction consultation
curl -X POST http://localhost:8000/api/v1/directions/consult \
  -H "Content-Type: application/json" \
  -d '{"direction": "northeast"}' | jq '.'

# Room consultation
curl -X POST http://localhost:8000/api/v1/rooms/consult \
  -H "Content-Type: application/json" \
  -d '{"room_type": "kitchen"}' | jq '.'

# Space analysis
curl -X POST http://localhost:8000/api/v1/spaces/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "space_name": "Master Bedroom",
    "space_type": "bedroom",
    "direction": "southwest",
    "area_sqft": 250,
    "features": ["window"],
    "issues": [],
    "purpose": "sleeping"
  }' | jq '.'
```

### Option C: Run Test Suite

```bash
python3 test_api_v4.py
```

Expected output:
```
✓ Settings loaded
✓ Embedded principles loaded
✓ Standalone consultation system initialized
✓ FastAPI app created
...
ALL TESTS PASSED SUCCESSFULLY!
```

## 4. Key Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | GET | API info |
| `/api/v1/health` | GET | Health check |
| `/api/v1/status` | GET | Detailed status |
| `/api/v1/system-info` | GET | System configuration |
| `/api/v1/consult` | POST | Main consultation |
| `/api/v1/directions/consult` | POST | Direction guidance |
| `/api/v1/rooms/consult` | POST | Room placement |
| `/api/v1/spaces/analyze` | POST | Space analysis |
| `/api/v1/batch-consult` | POST | Batch queries |

## 5. Example Queries

### Query 1: Direction Information
```json
{
  "direction": "northeast"
}
```
Endpoint: `POST /api/v1/directions/consult`

### Query 2: Room Guidelines
```json
{
  "room_type": "kitchen"
}
```
Endpoint: `POST /api/v1/rooms/consult`

### Query 3: Space Analysis
```json
{
  "space_name": "Living Room",
  "space_type": "living_room",
  "direction": "north",
  "area_sqft": 400,
  "features": ["large_window", "high_ceiling"],
  "issues": [],
  "purpose": "gathering"
}
```
Endpoint: `POST /api/v1/spaces/analyze`

### Query 4: Batch Consultation
```json
{
  "queries": [
    "Best direction for kitchen?",
    "What is northeast good for?",
    "Defect remedies?"
  ],
  "include_remedies": true
}
```
Endpoint: `POST /api/v1/batch-consult`

## 6. Documentation Links

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **API Reference:** See `API_ENDPOINTS.md`
- **Deployment:** See `DEPLOYMENT_GUIDE.md`
- **Full Summary:** See `API_IMPLEMENTATION_SUMMARY.md`

## 7. Stop the API

Press `Ctrl+C` in terminal or:
```bash
# Find and kill the process
lsof -i :8000 | grep LISTEN | awk '{print $2}' | xargs kill -9
```

## 8. Next Steps

### For Development
1. Modify code in `api/endpoints_complete.py`
2. Add new endpoints as needed
3. Test with Swagger UI
4. Use `test_api_v4.py` for validation

### For Deployment
1. Follow `DEPLOYMENT_GUIDE.md`
2. Set environment variables
3. Use Docker or Gunicorn
4. Configure reverse proxy (Nginx)
5. Enable SSL/TLS

### For Integration
1. Review `API_ENDPOINTS.md` for all endpoints
2. Use any HTTP client (requests, curl, axios, etc.)
3. Handle responses using provided schemas
4. Implement error handling based on error codes

## Troubleshooting

### API won't start
```bash
# Check Python version (need 3.9+)
python3 --version

# Check dependencies
pip list | grep -E "fastapi|uvicorn"

# Try with verbose output
python3 -m uvicorn api.enhanced_api_v4:app --log-level debug
```

### Port 8000 in use
```bash
# Use different port
uvicorn api.enhanced_api_v4:app --port 8001
```

### Import errors
```bash
# Reinstall requirements
pip install -r requirements.txt --force-reinstall

# Check sys.path
python3 -c "import sys; print(sys.path)"
```

### Endpoints returning 503
This means the consultation system isn't initialized. It's normal with TestClient.
When using uvicorn directly, it will be initialized properly.

## Performance Tips

### Single Worker (Development)
```bash
python3 -m api.enhanced_api_v4
```
Good for: Testing, development

### Multiple Workers (Production)
```bash
gunicorn api.enhanced_api_v4:app --workers 4 --worker-class uvicorn.workers.UvicornWorker
```
Good for: Production, high load

### With Reverse Proxy (Production)
```bash
# Nginx as reverse proxy
# Uvicorn on localhost:8000
# Nginx on port 80/443
```
Good for: SSL/TLS, load balancing, static files

## Security Notes

- Change CORS settings for production
- Add authentication/authorization
- Use API keys for external access
- Enable HTTPS/SSL
- Rate limit requests
- Log and monitor usage

## Support

- Check logs: tail logs/vastu-dss.log (if configured)
- Review docs: API_ENDPOINTS.md
- Check deployment: DEPLOYMENT_GUIDE.md
- Run tests: test_api_v4.py
- Check status: curl http://localhost:8000/api/v1/status | jq

---

**Ready to use!** 🚀

Start with: `python3 -m api.enhanced_api_v4`
Then visit: http://localhost:8000/docs
