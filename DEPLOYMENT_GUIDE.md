# Vastu Shastra DSS - FastAPI v4.0 Deployment Guide

## Quick Start

### Prerequisites

- Python 3.9+
- pip or conda
- Virtual environment (recommended)
- Git (optional, for version control)

### 1. Environment Setup

```bash
# Clone or navigate to project directory
cd /Users/ajaynawale/vastu_shastra_dss

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Configuration

Create a `.env` file in the project root:

```bash
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_TITLE="Vastu Shastra Decision Support System"
API_VERSION=1.0.0
DEBUG=False

# Anthropic API (Required for enhanced features)
ANTHROPIC_API_KEY=sk-ant-... # Your Anthropic API key

# Optional: Vector Database Configuration
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=your-api-key

# Optional: Chroma DB Configuration
CHROMA_DB_PATH=./vdb/chroma_vastu_db
CHROMA_COLLECTION_NAME=vastu_shastra

# Logging
LOG_LEVEL=INFO
```

### 3. Verify Installation

```bash
# Check dependencies
python -c "import fastapi; import uvicorn; print('✓ FastAPI and Uvicorn installed')"

# Verify data files exist
ls -la data/kg/vastu_knowledge_graph_final.json
ls -la vdb/chroma_vastu_db/

# Verify embedded principles
python -c "from vastu.embedded_principles import DIRECTIONS; print(f'✓ {len(DIRECTIONS)} directions loaded')"
```

---

## Running the API

### Method 1: Direct Python

```bash
# Navigate to project directory
cd /Users/ajaynawale/vastu_shastra_dss

# Activate virtual environment
source venv/bin/activate

# Run the API
python -m api.enhanced_api_v4
```

Expected output:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

### Method 2: Using Uvicorn Directly

```bash
uvicorn api.enhanced_api_v4:app --host 0.0.0.0 --port 8000 --reload
```

### Method 3: Using run_server.py (if updated)

```bash
python run_server.py
```

### Method 4: Docker (Optional)

Create a `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "-m", "api.enhanced_api_v4"]
```

Build and run:

```bash
docker build -t vastu-dss-api .
docker run -p 8000:8000 -e ANTHROPIC_API_KEY=your-key vastu-dss-api
```

---

## Accessing the API

### 1. Swagger Documentation

Open in browser: `http://localhost:8000/docs`

Features:
- Interactive API explorer
- Try requests directly
- View request/response schemas
- See example responses

### 2. ReDoc Documentation

Open in browser: `http://localhost:8000/redoc`

Alternative documentation format.

### 3. OpenAPI Schema

Get raw OpenAPI schema: `http://localhost:8000/openapi.json`

### 4. Health Check

```bash
curl http://localhost:8000/api/v1/health
```

Expected response:
```json
{
  "status": "healthy",
  "components": {
    "api": "operational",
    "consultation_system": "operational",
    "local_kg": "operational",
    "chroma_db": "operational"
  },
  "timestamp": "2026-10-08T17:30:00.123456",
  "message": "System is healthy..."
}
```

---

## System Components & Startup

### Component Initialization Order

1. **FastAPI App Creation** (< 1s)
   - CORS middleware setup
   - Exception handlers registered

2. **Consultation System** (< 1s)
   - StandaloneConsultation initialized
   - Embedded principles loaded

3. **Local Knowledge Graph** (1-3s)
   - KG JSON file loaded
   - Metadata parsed
   - Nodes/edges counted

4. **Chroma Vector DB** (2-5s)
   - Persistent client initialized
   - Collection retrieved
   - Document count verified

**Total Startup Time:** 5-10 seconds

### Monitoring Startup

```bash
# Watch logs during startup
tail -f venv/lib/python3.11/site-packages/...

# Or run with verbose logging
python -m api.enhanced_api_v4 2>&1 | grep -E "✓|✗|ERROR"
```

### Graceful Degradation

If optional components fail:
- **KG unavailable** → System continues with embedded principles
- **Chroma DB unavailable** → System continues without vector search
- **Consultation system fails** → Startup fails (CRITICAL component)

Check status:
```bash
curl http://localhost:8000/api/v1/system-info
```

---

## Testing the API

### 1. Basic Health Check

```bash
curl http://localhost:8000/api/v1/health
```

### 2. Main Consultation

```bash
curl -X POST http://localhost:8000/api/v1/consult \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the northeast direction for?",
    "include_remedies": true
  }'
```

### 3. Direction-Specific Query

```bash
curl -X POST http://localhost:8000/api/v1/directions/consult \
  -H "Content-Type: application/json" \
  -d '{"direction": "northeast"}'
```

### 4. Room Consultation

```bash
curl -X POST http://localhost:8000/api/v1/rooms/consult \
  -H "Content-Type: application/json" \
  -d '{"room_type": "kitchen"}'
```

### 5. Space Analysis

```bash
curl -X POST http://localhost:8000/api/v1/spaces/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "space_name": "Master Bedroom",
    "space_type": "bedroom",
    "direction": "northeast",
    "area_sqft": 250,
    "features": ["window"],
    "issues": [],
    "purpose": "sleeping"
  }'
```

### 6. Batch Consultation

```bash
curl -X POST http://localhost:8000/api/v1/batch-consult \
  -H "Content-Type: application/json" \
  -d '{
    "queries": [
      "Best direction for kitchen?",
      "What about northeast?"
    ],
    "include_remedies": true
  }'
```

---

## Performance Tuning

### 1. Uvicorn Workers

```bash
# Multiple workers (more CPU intensive)
uvicorn api.enhanced_api_v4:app --host 0.0.0.0 --port 8000 --workers 4
```

### 2. Connection Settings

```bash
# Higher limits for concurrency
uvicorn api.enhanced_api_v4:app \
  --host 0.0.0.0 \
  --port 8000 \
  --limit-concurrency 1000 \
  --limit-max-requests 10000
```

### 3. Logging Level

```bash
# In .env or command line
LOG_LEVEL=WARNING  # Reduce verbosity for production
```

### 4. Memory Usage

```bash
# Monitor memory usage
ps aux | grep uvicorn

# Limit memory (Docker)
docker run --memory="1g" vastu-dss-api
```

---

## Production Deployment

### 1. Use Gunicorn with Uvicorn Workers

Install gunicorn:
```bash
pip install gunicorn
```

Run:
```bash
gunicorn api.enhanced_api_v4:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile - \
  --error-logfile -
```

### 2. Reverse Proxy (Nginx)

```nginx
upstream vastu_api {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name api.vastu-dss.example.com;

    location / {
        proxy_pass http://vastu_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /docs {
        proxy_pass http://vastu_api/docs;
    }
}
```

### 3. SSL/TLS with Let's Encrypt

```bash
certbot certonly --standalone -d api.vastu-dss.example.com
```

Update Nginx config:
```nginx
listen 443 ssl;
ssl_certificate /etc/letsencrypt/live/api.vastu-dss.example.com/fullchain.pem;
ssl_certificate_key /etc/letsencrypt/live/api.vastu-dss.example.com/privkey.pem;
```

### 4. Process Management (Systemd)

Create `/etc/systemd/system/vastu-dss.service`:

```ini
[Unit]
Description=Vastu Shastra DSS API
After=network.target

[Service]
Type=notify
User=www-data
WorkingDirectory=/opt/vastu-dss
Environment="PATH=/opt/vastu-dss/venv/bin"
Environment="ANTHROPIC_API_KEY=your-key"
ExecStart=/opt/vastu-dss/venv/bin/gunicorn \
  api.enhanced_api_v4:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 127.0.0.1:8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable vastu-dss
sudo systemctl start vastu-dss
sudo systemctl status vastu-dss
```

### 5. Docker Compose (Complete Stack)

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY}
      LOG_LEVEL: INFO
      DEBUG: "False"
    volumes:
      - ./data:/app/data
      - ./vdb:/app/vdb
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  nginx:
    image: nginx:latest
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - api
    restart: unless-stopped
```

Run:
```bash
docker-compose up -d
```

---

## Monitoring & Logging

### 1. Health Monitoring

```bash
# Check health every 10 seconds
while true; do
  curl -s http://localhost:8000/api/v1/health | jq '.status'
  sleep 10
done
```

### 2. Performance Metrics

```bash
# Get system status with metrics
curl http://localhost:8000/api/v1/status | jq '.performance'
```

### 3. Log Aggregation

```bash
# Tail logs
tail -f logs/vastu-dss.log

# Filter by level
grep ERROR logs/vastu-dss.log
grep WARNING logs/vastu-dss.log
```

### 4. Application Metrics

Track key metrics:
- Total requests
- Average response time
- Error rate
- Component status

---

## Troubleshooting

### Issue 1: Port 8000 Already in Use

```bash
# Find process using port 8000
lsof -i :8000

# Kill process
kill -9 <PID>

# Or use different port
python -m api.enhanced_api_v4 --port 8001
```

### Issue 2: Chroma DB Not Found

```bash
# Check if Chroma DB exists
ls -la vdb/chroma_vastu_db/

# The system will continue without it (graceful degradation)
# Check logs for confirmation
```

### Issue 3: Missing Dependencies

```bash
# Reinstall all dependencies
pip install -r requirements.txt --force-reinstall

# Check specific dependency
python -c "import fastapi; print(fastapi.__version__)"
```

### Issue 4: High Memory Usage

```bash
# Profile memory
python -m memory_profiler api/enhanced_api_v4.py

# Or use simple monitoring
watch -n 1 'ps aux | grep python'
```

### Issue 5: Slow Startup

Check what's taking time:
1. Embedded principles loading (should be < 1s)
2. KG file loading (1-3s for 138 nodes)
3. Chroma DB initialization (2-5s)

Enable debug logging:
```
LOG_LEVEL=DEBUG
```

---

## Backup & Recovery

### 1. Data Backup

```bash
# Backup KG
cp -r data/kg data/kg.backup

# Backup Chroma DB
cp -r vdb/chroma_vastu_db vdb/chroma_vastu_db.backup

# Backup configuration
cp .env .env.backup
```

### 2. Restore

```bash
# Restore KG
rm -rf data/kg
cp -r data/kg.backup data/kg

# Restore Chroma DB
rm -rf vdb/chroma_vastu_db
cp -r vdb/chroma_vastu_db.backup vdb/chroma_vastu_db
```

---

## Security Considerations

### 1. API Key Protection

```bash
# In .env (never commit to git)
ANTHROPIC_API_KEY=sk-ant-...

# Add to .gitignore
echo ".env" >> .gitignore
```

### 2. CORS Configuration

For production, restrict CORS:

In `api/enhanced_api_v4.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)
```

### 3. Input Validation

All endpoints validate input using Pydantic:
- Query length limits (3-2000 chars)
- Batch size limits (1-10 items)
- Type checking
- Format validation

### 4. Rate Limiting (Optional)

Install slowapi:
```bash
pip install slowapi
```

Add to app:
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/api/v1/consult")
@limiter.limit("10/minute")
async def main_consultation(...):
    ...
```

---

## Updating & Maintenance

### 1. Update Dependencies

```bash
# Check for updates
pip list --outdated

# Update specific package
pip install --upgrade fastapi

# Update all
pip install -r requirements.txt --upgrade
```

### 2. Database Maintenance

```bash
# Clear Chroma cache
rm -rf .chroma*

# Rebuild indexes (if needed)
python scripts/rebuild_indexes.py
```

### 3. Log Rotation

Create `/etc/logrotate.d/vastu-dss`:

```
/opt/vastu-dss/logs/*.log {
    daily
    rotate 14
    compress
    delaycompress
    missingok
    notifempty
}
```

---

## Next Steps

1. Review API_ENDPOINTS.md for complete endpoint reference
2. Test all endpoints using Swagger UI at `/docs`
3. Set up monitoring and alerting
4. Deploy to production using one of the methods above
5. Scale as needed using load balancing

For additional help, refer to:
- FastAPI documentation: https://fastapi.tiangolo.com
- Uvicorn documentation: https://www.uvicorn.org
- Vastu Shastra DSS project documentation

---

## Support

For issues or questions:
1. Check troubleshooting section above
2. Review logs: `tail -f logs/vastu-dss.log`
3. Check health endpoint: `curl http://localhost:8000/api/v1/health`
4. Review API documentation: `http://localhost:8000/docs`
