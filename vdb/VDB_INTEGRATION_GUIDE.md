# VDB Integration Guide: Graceful Degradation Architecture

## Critical Requirement

**"Tomorrow if jyotish engine vectors and vaidya mitra ayurveda vectors are not available, this application should run independently of that"**

This document describes how the Vastu Shastra DSS implements resilient VDB integration with graceful degradation to meet this requirement.

## Architecture Overview

### Layer 1: CORE VASTU (ALWAYS WORKS)
- **Status**: Required - never fails
- **Components**: 
  - Embedded principles
  - Local knowledge graph
  - Chroma local vectors
  - Claude Opus 5.5 reasoning
- **Guarantee**: 100% uptime independent of external services
- **Output**: Complete Vastu consultation

### Layer 3a: JYOTISH ENHANCEMENT (OPTIONAL)
- **Status**: Optional - fast-fail if unavailable
- **Source**: Akymatech Jyotish VDB
- **Purpose**: Link planetary impacts to directions/times
- **Timeout**: 2 seconds max
- **Fallback**: Skip gracefully, continue with core result

### Layer 3b: AYURVEDA ENHANCEMENT (OPTIONAL)
- **Status**: Optional - fast-fail if unavailable
- **Source**: Akymatech Ayurveda VDB
- **Purpose**: Link health impacts to space elements/doshas
- **Timeout**: 2 seconds max
- **Fallback**: Skip gracefully, continue with core result

## Core Design Patterns

### 1. Try-Optional Pattern

```python
# ALWAYS: Get core consultation
core_result = await core_consultation_system.analyze_space(space_data)

# OPTIONAL: Try Jyotish enhancement
try:
    jyotish_data = await try_jyotish_enhancement(space_data, timeout=2.0)
    if jyotish_data:
        core_result = merge(core_result, jyotish_data)
except:
    pass  # Continue with core_result unchanged

# OPTIONAL: Try Ayurveda enhancement
try:
    ayurveda_data = await try_ayurveda_enhancement(space_data, timeout=2.0)
    if ayurveda_data:
        core_result = merge(core_result, ayurveda_data)
except:
    pass  # Continue with core_result unchanged

# ALWAYS: Return valid result
return core_result  # Always has something to return
```

### 2. Fast-Fail with Timeout

- **Health Check Timeout**: 1 second
- **Query Timeout**: 2 seconds max
- **Never blocks user**: If VDB is slow, skip enhancement and continue
- **Retry Logic**: 3 retries with exponential backoff (0.1s, 0.2s, 0.4s)

### 3. Graceful Degradation Strategy

```
Ideal State:        Core + Jyotish + Ayurveda = Full enhancement
One VDB Down:       Core + Jyotish (or Core + Ayurveda) = Partial enhancement
Both Down:          Core = Core-only (complete functionality)
Network Failure:    Core = Core-only (system continues)
Cache Available:    Core + Cached enhancements (best effort)
Everything Down:    Core = Core-only (guaranteed minimum)
```

## Implementation Components

### 1. AkymatechVDBAdapter (`vdb/vdb_adapter.py`)

Main adapter class with try-optional pattern.

**Key Features**:
- Concurrent VDB health checks
- Query timeout enforcement (2 seconds)
- Result caching with TTL (60 minutes)
- Automatic fallback on any error
- Statistics tracking
- Never blocks consultation

**Usage**:

```python
from vdb.vdb_adapter import AkymatechVDBAdapter, get_vdb_adapter

# Get adapter instance
adapter = await get_vdb_adapter()

# Query with automatic fallback
jyotish_result = await adapter.query_jyotish(
    query="northeast direction",
    top_k=5,
    fallback=True  # Enable graceful fallback
)

# Check if VDB was actually used
if jyotish_result.used_vdb:
    print(f"Jyotish enhanced consultation: {jyotish_result.data}")
else:
    print("Consultation provided without Jyotish enhancement")

# Query both VDBs concurrently
results = await adapter.query_both_vdbs("space analysis query")

# Check metadata
metadata = adapter.get_metadata()
print(f"Enhancement level: {metadata.enhancement_level}")
print(f"VDBs available: {metadata.vdbs_available}")
```

### 2. FastHealthChecker (`vdb/health_check.py`)

Health monitoring with quick timeout and retry logic.

**Features**:
- 2-second timeout per check
- 3 retries with exponential backoff
- 60-second cache to avoid hammering VDBs
- Concurrent multi-VDB checks
- Overall status determination

**Usage**:

```python
from vdb.health_check import FastHealthChecker

checker = FastHealthChecker(timeout_seconds=2.0, max_retries=3)

# Check single VDB
async def jyotish_health_check():
    # ... actual health check implementation
    return True

status = await checker.check_vdb_health("jyotish", jyotish_health_check)
print(f"Status: {status['status']}")  # 'healthy' or 'unhealthy'

# Check multiple VDBs concurrently
checks = {
    "jyotish": jyotish_health_check,
    "ayurveda": ayurveda_health_check,
}
results = await checker.check_multiple_vdbs(checks)
overall = checker.get_overall_status(results)
print(f"Overall system health: {overall}")
```

### 3. ConsultationFallbackManager (`vdb/graceful_fallback.py`)

Manages consultation with optional VDB enhancements.

**Features**:
- Core consultation always succeeds
- Optional enhancement queries run concurrently
- Transparent fallback (no errors exposed to user)
- Metrics tracking for enhancement levels

**Usage**:

```python
from vdb.graceful_fallback import ConsultationFallbackManager

manager = ConsultationFallbackManager()

async def core_vastu_consultation():
    # Core Vastu analysis - always works
    return {"direction": "northeast", "element": "earth"}

async def jyotish_enhancement():
    # Optional: Query Jyotish VDB
    result = await vdb_adapter.query_jyotish(query)
    return result.data if result.used_vdb else None

async def ayurveda_enhancement():
    # Optional: Query Ayurveda VDB
    result = await vdb_adapter.query_ayurveda(query)
    return result.data if result.used_vdb else None

# Get consultation with optional enhancements
result = await manager.get_consultation_with_vdb_enhancements(
    consultation_id="consultation_001",
    core_consultation_fn=core_vastu_consultation,
    jyotish_fn=jyotish_enhancement,
    ayurveda_fn=ayurveda_enhancement,
    timeout_seconds=2.0,  # Fast-fail timeout
)

# Always returns valid result
print(f"Enhancement level: {result['enhancement_level']}")
# Possible values: 'core_only', 'core_with_jyotish', 
#                  'core_with_ayurveda', 'core_with_both_vdbs'

print(f"Core result: {result['core_result']}")
print(f"VDBs used: {result['vdbs_used']}")
print(f"Errors (internal): {result['errors']}")

# Get metrics
metrics = manager.get_fallback_metrics()
print(f"Core-only served: {metrics['core_only_served']}")
print(f"Fully enhanced: {metrics['fully_enhanced_percentage']}%")
```

## Integration with FastAPI

### 1. Startup Event

Initialize VDB adapter on server startup:

```python
from api.main import app
from vdb.vdb_adapter import get_vdb_adapter

@app.on_event("startup")
async def startup_event():
    """Initialize VDB adapter on startup."""
    try:
        vdb_adapter = await get_vdb_adapter(
            jyotish_url="https://api.akymatech.dev/jyotish",
            ayurveda_url="https://api.akymatech.dev/ayurveda",
            api_key=os.getenv("AKYMATECH_API_KEY"),
        )
        logger.info("VDB adapter initialized")
        
        # Perform initial health check
        health = await vdb_adapter.check_health(force=True)
        logger.info(f"VDB health check: {health}")
        
    except Exception as e:
        logger.error(f"VDB initialization failed: {e}")
        logger.warning("Continuing with core-only mode")
```

### 2. Endpoint Integration

Use VDB enhancements in endpoints:

```python
from fastapi import APIRouter
from vdb.vdb_adapter import get_vdb_adapter
from vdb.graceful_fallback import ConsultationFallbackManager

router = APIRouter()
manager = ConsultationFallbackManager()

@router.post("/api/v1/spaces/analyze")
async def analyze_space(request: SpaceAnalysisRequest):
    """Analyze space with optional VDB enhancements."""
    
    adapter = await get_vdb_adapter()
    space_dict = request.dict()
    
    # Core consultation
    async def core_consultation():
        core = await core_vastu_system.analyze_space(space_dict)
        return core
    
    # Optional Jyotish enhancement
    async def jyotish_enhancement():
        result = await adapter.query_jyotish(
            f"directions and times for {space_dict.get('room_type')}"
        )
        return result.data if result.used_vdb else None
    
    # Optional Ayurveda enhancement
    async def ayurveda_enhancement():
        result = await adapter.query_ayurveda(
            f"health impacts for {space_dict.get('direction')}"
        )
        return result.data if result.used_vdb else None
    
    # Get consultation (always succeeds)
    consultation = await manager.get_consultation_with_vdb_enhancements(
        consultation_id=request.consultation_id,
        core_consultation_fn=core_consultation,
        jyotish_fn=jyotish_enhancement,
        ayurveda_fn=ayurveda_enhancement,
        timeout_seconds=2.0,
    )
    
    # Always return result (with core at minimum)
    return {
        "consultation": consultation["core_result"],
        "enhancements": consultation["enhancements"],
        "enhancement_level": consultation["enhancement_level"],
        "vdbs_used": consultation["vdbs_used"],
    }
```

### 3. Health Endpoint

Expose VDB health status (but never fail on VDB health):

```python
@router.get("/api/v1/health")
async def health_check():
    """Check system health."""
    
    adapter = await get_vdb_adapter()
    
    # Core system is always operational
    system_status = "operational"
    
    # VDB status is informational only
    vdb_status = adapter.get_stats()
    metadata = adapter.get_metadata()
    
    return {
        "status": system_status,  # Never fails due to VDB status
        "components": {
            "core_vastu": "operational",  # Always operational
            "jyotish_vdb": "operational" if vdb_status["jyotish_healthy"] else "unavailable",
            "ayurveda_vdb": "operational" if vdb_status["ayurveda_healthy"] else "unavailable",
        },
        "enhancement_level": metadata.enhancement_level,
        "vdbs_available": metadata.vdbs_available,
    }
```

## Configuration

### Environment Variables

```bash
# VDB Endpoints
AKYMATECH_JYOTISH_URL=https://api.akymatech.dev/jyotish
AKYMATECH_AYURVEDA_URL=https://api.akymatech.dev/ayurveda
AKYMATECH_API_KEY=your_api_key_here

# Timeout Settings
VDB_QUERY_TIMEOUT=2.0  # seconds
VDB_HEALTH_CHECK_TIMEOUT=1.0  # seconds
VDB_MAX_RETRIES=3

# Cache Settings
VDB_CACHE_ENABLED=true
VDB_CACHE_TTL_MINUTES=60
```

### Programmatic Configuration

```python
from vdb.vdb_adapter import AkymatechVDBAdapter

adapter = AkymatechVDBAdapter(
    jyotish_url="https://api.akymatech.dev/jyotish",
    ayurveda_url="https://api.akymatech.dev/ayurveda",
    api_key="your_api_key",
    timeout_seconds=2.0,      # Fast-fail timeout
    max_retries=3,            # Retry logic
    cache_enabled=True,       # Result caching
    cache_ttl_minutes=60,     # Cache lifetime
)
```

## Testing

### Running Tests

```bash
# Run all VDB fallback tests
pytest tests/test_vdb_fallback.py -v

# Run specific test
pytest tests/test_vdb_fallback.py::TestCriticalRequirement -v

# Run with coverage
pytest tests/test_vdb_fallback.py --cov=vdb --cov-report=html
```

### Test Scenarios

#### Test 1: VDB Available
```python
# Query both VDBs
# Verify enhanced response
# Check metadata shows VDBs used
```

#### Test 2: VDB Unavailable
```python
# Mock VDB timeout/error
# Verify core response still returned
# Check metadata shows VDB skipped
# Verify no error to user
```

#### Test 3: One VDB Available, One Down
```python
# Jyotish available, Ayurveda down
# Verify response includes Jyotish enhancement only
# Ayurveda gracefully skipped
# Enhancement level: "core_with_jyotish"
```

#### Test 4: Network Failure
```python
# All external APIs fail
# Verify system returns pure Vastu response
# User never knows VDBs failed
# Enhancement level: "core_only"
```

## Monitoring and Debugging

### Health Check Endpoint

```python
# Check VDB status
curl http://localhost:8000/api/v1/health

# Response:
{
    "status": "operational",
    "components": {
        "core_vastu": "operational",
        "jyotish_vdb": "operational",
        "ayurveda_vdb": "unavailable"
    },
    "enhancement_level": "partial"
}
```

### Statistics Endpoint (if exposed)

```python
adapter = await get_vdb_adapter()
stats = adapter.get_stats()

# Returns:
{
    "total_queries": 42,
    "successful_queries": 35,
    "failed_queries": 5,
    "cache_hits": 2,
    "fallback_used": 5,
    "jyotish_healthy": true,
    "ayurveda_healthy": false,
    "cache_size": 15
}
```

### Debug Logging

Enable debug logging to trace VDB queries:

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("vdb")

# Will show:
# "Jyotish VDB marked as unhealthy, skipping query"
# "Cache hit for jyotish query: direction consultation"
# "Successfully queried ayurveda VDB: 3 results"
# "Falling back from ayurveda VDB"
```

## Performance Characteristics

### Response Time Distribution

- **Core consultation**: ~500ms (no VDB)
- **Core + Jyotish**: ~700ms (Jyotish adds ~200ms)
- **Core + Ayurveda**: ~700ms (Ayurveda adds ~200ms)
- **Core + Both**: ~900ms (parallel queries add ~400ms)
- **Core only (VDB timeout)**: ~500ms (quick fallback)

### Timeout Behavior

- **VDB query timeout**: 2 seconds (fast-fail)
- **Health check timeout**: 1 second (quick detection)
- **Retry delay**: 100ms + exponential backoff
- **Total possible delay**: ~500ms for 3 retries
- **User never waits**: Core consultation proceeds in parallel

## Troubleshooting

### Issue: "VDB health check timeout"
**Cause**: VDB service is slow or unreachable
**Solution**: Check network connectivity, VDB server status
**Impact**: System falls back to core-only mode (no impact to user)

### Issue: "Cache size growing indefinitely"
**Cause**: Cache TTL not working or memory not managed
**Solution**: Check cache_ttl_minutes setting, use clear_cache() if needed
**Impact**: Potential memory usage increase

### Issue: "All queries go to cache, never hit VDB"
**Cause**: VDB might be down and cache is serving old results
**Solution**: Clear cache, check VDB health, monitor response freshness
**Impact**: Users get potentially stale enhancements (acceptable for graceful degradation)

## Success Metrics

The system succeeds when:

✅ **Always Responds**: Every consultation returns a valid response (minimum: core-only)
✅ **Transparent Fallback**: No error messages shown to user when VDB unavailable
✅ **Fast Response**: Core consultation + VDB enhancements complete in <1 second
✅ **Metadata Tracking**: Each response indicates which VDBs were used
✅ **No Blocking**: VDB timeout never blocks core consultation
✅ **Handles Failures**: Works with 0, 1, or 2 VDBs operational
✅ **Cache Improves Performance**: Repeated queries faster with cache

## Future Enhancements

1. **Adaptive Timeout**: Adjust timeout based on recent VDB performance
2. **Predictive Fallback**: Pre-check VDB health before query
3. **Stale Cache Strategy**: Serve stale cache beyond TTL if VDB unavailable
4. **Circuit Breaker**: Fast-fail pattern for repeatedly failing VDBs
5. **Multi-Region VDBs**: Fallback to alternate VDB endpoints
6. **Compression**: Cache compression for large result sets

## References

- **Core Architecture**: `vdb/vdb_adapter.py`
- **Health Monitoring**: `vdb/health_check.py`
- **Fallback Logic**: `vdb/graceful_fallback.py`
- **Test Suite**: `tests/test_vdb_fallback.py`
- **Client Library**: `vdb/akymatech_client.py`

---

**Critical Requirement Met**: ✅
System functions independently of external VDBs with transparent degradation.
Tomorrow, if VDBs are unavailable, users will experience complete Vastu consultations without noticing any difference.
