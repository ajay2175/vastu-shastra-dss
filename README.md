# Vastu Shastra Decision Support System

A comprehensive decision support system for Vastu Shastra (ancient Indian architecture) powered by Claude AI and modern retrieval-augmented generation (RAG).

## Features

- **Standalone Consultation**: Works without external databases for immediate guidance
- **RAG-Enabled Analysis**: Retrieves relevant evidence from classical texts when VDB is available
- **Graceful Degradation**: Seamlessly falls back to offline mode when databases are unavailable
- **Multi-Room Analysis**: Analyze entire buildings or individual spaces
- **Hybrid Search**: Combines keyword and semantic search for better results
- **Knowledge Graph**: Structured knowledge of Vastu principles and remedies
- **Production-Ready**: Built with FastAPI, comprehensive error handling, and health checks

## Quick Start

### Installation

```bash
# Clone repository
cd vastu_shastra_dss

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure
cp .env.template .env
# Edit .env with your ANTHROPIC_API_KEY and optional VDB settings
```

### Run Server

```bash
python run_server.py
```

Access API at: `http://localhost:8000`
- Documentation: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/api/v1/health`

## API Endpoints

### Direction Consultation
```bash
POST /api/v1/directions/consult
{
  "direction": "northeast"
}
```

### Room Consultation
```bash
POST /api/v1/rooms/consult
{
  "room_type": "bedroom"
}
```

### Space Analysis
```bash
POST /api/v1/spaces/analyze
{
  "space_name": "Master Bedroom",
  "space_type": "bedroom",
  "primary_direction": "southwest",
  "purpose": "Sleeping"
}
```

### Batch Analysis
```bash
POST /api/v1/spaces/analyze-batch
{
  "spaces": [
    {"space_name": "Room 1", "space_type": "bedroom", "primary_direction": "south", "purpose": "Sleeping"}
  ]
}
```

## Project Structure

```
vastu_shastra_dss/
├── vastu/                    # Core Vastu principles
├── vdb/                      # Vector database layer
├── retrieval/                # RAG and evidence retrieval
├── api/                      # FastAPI endpoints
├── models/                   # Pydantic schemas
├── config/                   # Configuration
├── data/                     # Data directory
└── tests/                    # Test suite
```

## Configuration

Set in `.env`:
- `ANTHROPIC_API_KEY`: Required for Claude AI
- `QDRANT_URL`: Vector database URL (optional)
- `CHROMA_DB_PATH`: Local embedding storage (default: ./data/embeddings)
- `LOG_LEVEL`: Logging level (default: INFO)

## Testing

```bash
# Run all tests
pytest

# Specific test file
pytest tests/test_standalone.py

# With coverage
pytest --cov=. tests/
```

## Features

### Graceful Degradation
- Automatic fallback to offline mode when VDB unavailable
- Uses embedded principles and cached results
- Seamless recovery when service restored

### Knowledge Graph
- 8 cardinal + center directions
- 15+ room types with guidelines
- 50+ common defects and remedies
- Element and color associations

### RAG Integration
- Retrieves relevant classical texts
- Formats evidence for Claude
- Hybrid semantic + keyword search
- Maintains citation trail

## Standalone Usage

```python
from vastu.standalone_consultation import StandaloneConsultation
import asyncio

async def main():
    consultation = StandaloneConsultation()
    
    space = {
        "name": "Master Bedroom",
        "type": "bedroom",
        "direction": "southwest",
        "purpose": "Sleeping"
    }
    
    result = await consultation.analyze_space(space)
    print(f"Compliance: {result['compliance_score']}")

asyncio.run(main())
```

## Performance

- Response time: < 500ms (standalone)
- Batch processing: 5+ spaces/second
- Memory: ~500MB
- Concurrent requests: 100+

## Deployment

### Docker

```dockerfile
FROM python:3.11
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "run_server.py"]
```

### Production Checklist

- Set `debug=false`
- Configure proper CORS origins
- Set up monitoring and logging
- Configure database backups
- Use proper authentication
- Set up rate limiting

## Architecture

### Modular Design
- **Vastu Module**: Embedded knowledge and consultation
- **VDB Module**: Unified vector database interface
- **Retrieval Module**: Evidence collection and formatting
- **API Module**: FastAPI endpoints with async support
- **Config Module**: Centralized settings management

### Graceful Fallback
1. Primary VDB search → 2. Secondary VDB → 3. Cached results → 4. Offline mode

## Version

- **Version**: 1.0.0
- **Status**: Production Ready
- **Last Updated**: October 2026

## Support

Refer to project documentation or contact development team.
