# Vastu Shastra DSS - FastAPI v4.0 Complete Endpoint Reference

## Overview

The Vastu Shastra Decision Support System API v4.0 is a comprehensive FastAPI backend providing consultation, analysis, and guidance for Vastu Shastra principles. It operates in **standalone mode** (no external VDBs required) with optional integration of vector databases and knowledge graphs.

**Base URL:** `http://localhost:8000`

**API Prefix:** `/api/v1`

**Documentation:** `/docs` (Swagger UI), `/redoc` (ReDoc)

## Table of Contents

1. [Health & Status Endpoints](#health--status-endpoints)
2. [Main Consultation Endpoints](#main-consultation-endpoints)
3. [Direction & Room Consultation](#direction--room-consultation)
4. [Space Analysis Endpoints](#space-analysis-endpoints)
5. [Reference Endpoints](#reference-endpoints)
6. [Response Schemas](#response-schemas)
7. [Error Handling](#error-handling)
8. [Examples](#examples)

---

## Health & Status Endpoints

### 1. GET /api/v1/health

**Description:** Quick health check for system status

**Method:** GET

**Response:**
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
  "message": "System is healthy. API started at 2026-10-08T17:25:00.000000"
}
```

**Status Codes:**
- `200 OK` - System healthy
- `503 Service Unavailable` - System degraded or failed

---

### 2. GET /api/v1/status

**Description:** Detailed system status with performance metrics

**Method:** GET

**Response:**
```json
{
  "status": "operational",
  "components": {
    "api": "operational",
    "consultation": "operational",
    "kg": "operational",
    "chroma_db": "operational",
    "startup_time": "2026-10-08T17:25:00.000000",
    "last_check": "2026-10-08T17:30:00.000000"
  },
  "performance": {
    "total_requests": 42,
    "total_consultations": 15,
    "avg_response_time_ms": 125.5
  },
  "uptime_seconds": 300.5,
  "timestamp": "2026-10-08T17:30:00.123456"
}
```

---

### 3. GET /api/v1/system-info

**Description:** Get system configuration and available features

**Method:** GET

**Response:**
```json
{
  "api_version": "1.0.0",
  "system_name": "Vastu Shastra DSS v4.0",
  "capabilities": [
    "standalone_consultation",
    "direction_analysis",
    "room_placement_guidance",
    "defect_diagnosis",
    "space_analysis",
    "batch_operations",
    "graceful_degradation",
    "vector_search",
    "knowledge_graph_reasoning"
  ],
  "embedded_components": {
    "directions": 9,
    "vastu_doshas": 20,
    "room_types": 10,
    "remedy_categories": 6,
    "kg_nodes": 138,
    "kg_edges": 213
  },
  "configuration": {
    "enable_rag": true,
    "enable_kg_reasoning": true,
    "enable_hybrid_search": true,
    "enable_degradation": true,
    "debug_mode": false
  }
}
```

---

## Main Consultation Endpoints

### 1. POST /api/v1/consult

**Description:** Main consultation endpoint for natural language queries

**Method:** POST

**Request Body:**
```json
{
  "query": "I have a bedroom in the northeast direction, what remedies?",
  "force_standalone": false,
  "include_remedies": true,
  "include_references": false
}
```

**Parameters:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| query | string | Yes | Consultation query (3-2000 chars) |
| force_standalone | boolean | No | Force standalone mode (default: false) |
| include_remedies | boolean | No | Include remedy suggestions (default: true) |
| include_references | boolean | No | Include classical text references (default: false) |

**Response:**
```json
{
  "query": "I have a bedroom in the northeast direction, what remedies?",
  "recommendation": {
    "type": "room",
    "status": "success",
    "room_type": "bedroom",
    "primary_optimal": "southwest",
    "secondary_optimal": ["south", "west"],
    "avoid": ["northeast", "center", "southeast"],
    "colors": {
      "best": "Soft pastels: cream, light pink, pale yellow",
      "avoid": "Bright red, black, dark colors"
    },
    "key_recommendations": [
      "Best direction: southwest",
      "Avoid directions: northeast, center, southeast",
      "Recommended colors: Soft pastels: cream, light pink, pale yellow"
    ],
    "remedies": [
      "Move bed to southwest corner",
      "Install mirrors on east and north walls",
      "Paint walls light colors",
      "Use cool tones for peaceful sleep"
    ]
  },
  "metadata": {
    "timestamp": "2026-10-08T17:30:00.123456",
    "consultation_type": "room",
    "confidence": 0.95,
    "mode": "hybrid"
  },
  "sources_used": [
    "embedded_principles",
    "room_analysis"
  ],
  "processing_time_ms": 45.3
}
```

**Status Codes:**
- `200 OK` - Consultation successful
- `400 Bad Request` - Invalid query format
- `422 Unprocessable Entity` - Validation error
- `503 Service Unavailable` - Consultation system not available

---

### 2. POST /api/v1/batch-consult

**Description:** Process multiple consultation queries in batch

**Method:** POST

**Request Body:**
```json
{
  "queries": [
    "Best direction for kitchen?",
    "What is northeast dosha?",
    "How to fix blocked entry?"
  ],
  "include_remedies": true
}
```

**Parameters:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| queries | array[string] | Yes | List of queries (1-10 items) |
| include_remedies | boolean | No | Include remedies for all (default: true) |

**Response:**
```json
{
  "results": [
    {
      "query": "Best direction for kitchen?",
      "recommendation": { ... },
      "metadata": { ... },
      "sources_used": [ ... ],
      "processing_time_ms": 42.1
    },
    { ... },
    { ... }
  ],
  "summary": {
    "total_queries": 3,
    "successful": 3,
    "avg_processing_time_ms": 41.8
  },
  "total_processing_time_ms": 125.4
}
```

---

## Direction & Room Consultation

### 1. POST /api/v1/directions/consult

**Description:** Get detailed consultation for a specific direction

**Method:** POST

**Request Body:**
```json
{
  "direction": "northeast"
}
```

**Response:**
```json
{
  "direction": "northeast",
  "principle_name": "Northeast (Ishanya)",
  "description": "The Northeast is governed by Ishana (Shiva)",
  "key_points": [
    "Spiritual growth and wisdom",
    "Divine connection and purity",
    "Health and healing"
  ],
  "elements": ["ether/space"],
  "colors": ["light yellow", "light blue", "white"],
  "remedies": [
    "Keep clear and clean",
    "Install bright light",
    "Place deity idol"
  ]
}
```

**Available Directions:**
- north
- northeast
- east
- southeast
- south
- southwest
- west
- northwest
- center

---

### 2. POST /api/v1/rooms/consult

**Description:** Get placement guidelines for a specific room type

**Method:** POST

**Request Body:**
```json
{
  "room_type": "kitchen"
}
```

**Response:**
```json
{
  "room_type": "kitchen",
  "best_directions": ["southeast", "east"],
  "directions_to_avoid": ["northeast", "center", "northwest"],
  "ideal_shape": "Square or rectangular",
  "window_placement": "East or North for morning light",
  "recommended_color": "White, light yellow, light green",
  "furniture_guidelines": "Place heavy items in South and West"
}
```

**Available Room Types:**
- bedroom
- kitchen
- living_room
- puja_room
- office
- entrance
- bathroom
- storage_room
- garage
- outdoor_garden

---

### 3. POST /api/v1/defects/diagnose

**Description:** Diagnose a Vastu defect and get remedies

**Method:** POST

**Request Body:**
```json
{
  "defect_type": "northeast_toilet"
}
```

**Response:**
```json
{
  "defect": "northeast_toilet",
  "problem": "Toilet or waste in northeast direction",
  "impact": "Severe health decline",
  "severity": "CRITICAL",
  "remedies": [
    "Complete relocation or permanent closure",
    "Move toilet to Southeast corner only",
    "Perform purification rituals daily for 40 days"
  ],
  "detailed_remedies": [
    {
      "remedy": "Complete relocation or permanent closure",
      "details": "Apply as needed for northeast_toilet"
    },
    { ... }
  ]
}
```

---

## Space Analysis Endpoints

### 1. POST /api/v1/spaces/analyze

**Description:** Analyze a space for Vastu compliance

**Method:** POST

**Request Body:**
```json
{
  "space_name": "Master Bedroom",
  "space_type": "bedroom",
  "direction": "northeast",
  "area_sqft": 250,
  "features": ["window", "mirror", "bed"],
  "issues": ["northeast_facing", "dark_corner"],
  "purpose": "sleeping"
}
```

**Parameters:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| space_name | string | Yes | Name of the space |
| space_type | string | Yes | Type of room |
| direction | string | Yes | Primary direction |
| area_sqft | number | No | Area in square feet |
| features | array | No | Space features |
| issues | array | No | Perceived issues |
| purpose | string | Yes | Primary purpose |

**Response:**
```json
{
  "space_name": "Master Bedroom",
  "compliance_score": 65.5,
  "issues": ["northeast_facing", "dark_corner"],
  "recommendations": [
    "Relocate bed to southwest corner",
    "Install additional lighting on north wall",
    "Paint walls soft pastel colors"
  ],
  "suggested_color": "Light pink or pale yellow",
  "element_association": "water",
  "remedies": [
    "Mirror placement for light reflection",
    "Element balancing with earth tones",
    "Strategic color correction"
  ]
}
```

---

### 2. POST /api/v1/spaces/analyze-batch

**Description:** Analyze multiple spaces in batch

**Method:** POST

**Request Body:**
```json
{
  "spaces": [
    {
      "space_name": "Master Bedroom",
      "space_type": "bedroom",
      "direction": "southwest",
      "area_sqft": 250,
      "features": ["window", "bed"],
      "issues": [],
      "purpose": "sleeping"
    },
    {
      "space_name": "Kitchen",
      "space_type": "kitchen",
      "direction": "southeast",
      "area_sqft": 150,
      "features": ["stove", "sink"],
      "issues": ["water_retention"],
      "purpose": "cooking"
    }
  ]
}
```

**Response:**
```json
{
  "analyses": [
    { ... space analysis 1 ... },
    { ... space analysis 2 ... }
  ],
  "overall_score": 75.2,
  "summary": "Analyzed 2 spaces. Overall compliance score: 75.2/100."
}
```

---

## Reference Endpoints

### 1. GET /api/v1/directions

**Description:** List all available directions

**Method:** GET

**Response:**
```json
["north", "northeast", "east", "southeast", "south", "southwest", "west", "northwest", "center"]
```

---

### 2. GET /api/v1/rooms

**Description:** List all available room types

**Method:** GET

**Response:**
```json
["bedroom", "kitchen", "living_room", "puja_room", "office", "entrance", "bathroom", "storage_room", "garage", "outdoor_garden"]
```

---

### 3. GET /api/v1/doshas

**Description:** List all known Vastu doshas

**Method:** GET

**Response:**
```json
[
  "brahma_sthana_violation",
  "northeast_toilet",
  "central_pit",
  "southeast_kitchen",
  "northwest_toilet",
  "blocked_entry",
  "central_staircase",
  "sloped_foundation",
  "missing_quadrant",
  "poison_beam",
  "sharp_corner_projection",
  "water_retention",
  "open_southwest",
  "electromagnetic_stress"
]
```

---

### 4. GET /api/v1/principles

**Description:** List all Vastu principles

**Method:** GET

**Response:**
```json
{
  "directions": ["north", "northeast", "east", "southeast", "south", "southwest", "west", "northwest", "center"],
  "sacred_geometry": ["vastu_purusha_mandala", "sacred_proportions", "chakra_correspondences"],
  "health_correlations": ["vata_dosha", "pitta_dosha", "kapha_dosha", "directional_health"]
}
```

---

## Response Schemas

### HealthCheckResponse

```typescript
{
  status: "healthy" | "degraded" | "unhealthy"
  components: {
    api: "operational" | "initializing" | "unavailable" | "failed"
    consultation_system: "operational" | "initializing" | "unavailable" | "failed"
    local_kg: "operational" | "unavailable" | "degraded"
    chroma_db: "operational" | "unavailable" | "degraded"
  }
  timestamp: string (ISO 8601)
  message?: string
}
```

### ConsultationResponse

```typescript
{
  query: string
  recommendation: {
    type: "direction" | "room" | "defect" | "general" | "error"
    status: "success" | "error"
    [key: string]: any
  }
  metadata: {
    timestamp: string
    consultation_type: string
    confidence: number (0-1)
    mode: "standalone" | "hybrid"
  }
  sources_used: string[]
  processing_time_ms: number
}
```

### ErrorResponse

```typescript
{
  error: string
  error_code: string
  details?: {
    [key: string]: any
  }
  timestamp: string (ISO 8601)
}
```

---

## Error Handling

### Standard Error Codes

| Code | Status | Description |
|------|--------|-------------|
| VALIDATION_ERROR | 422 | Request validation failed |
| NOT_FOUND | 404 | Resource not found |
| SERVICE_UNAVAILABLE | 503 | Service not available |
| INTERNAL_ERROR | 500 | Internal server error |
| INVALID_QUERY | 400 | Invalid query format |
| SYSTEM_ERROR | 500 | System error |

### Example Error Response

```json
{
  "error": "Request validation failed",
  "error_code": "VALIDATION_ERROR",
  "details": {
    "field": "query",
    "message": "Query must be at least 3 characters"
  },
  "timestamp": "2026-10-08T17:30:00.123456"
}
```

---

## Examples

### Example 1: Simple Direction Query

```bash
curl -X POST http://localhost:8000/api/v1/consult \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What should I know about the northeast direction?",
    "include_remedies": true
  }'
```

### Example 2: Room Placement Analysis

```bash
curl -X POST http://localhost:8000/api/v1/rooms/consult \
  -H "Content-Type: application/json" \
  -d '{
    "room_type": "kitchen"
  }'
```

### Example 3: Batch Space Analysis

```bash
curl -X POST http://localhost:8000/api/v1/spaces/analyze-batch \
  -H "Content-Type: application/json" \
  -d '{
    "spaces": [
      {
        "space_name": "Master Bedroom",
        "space_type": "bedroom",
        "direction": "southwest",
        "area_sqft": 250,
        "features": ["window"],
        "issues": [],
        "purpose": "sleeping"
      }
    ]
  }'
```

### Example 4: Get System Status

```bash
curl http://localhost:8000/api/v1/status
```

---

## Rate Limiting & Performance

- **Max Batch Size:** 10 queries per batch request
- **Query Timeout:** 30 seconds
- **Average Response Time:** 40-150ms (standalone mode)
- **Max Concurrent Requests:** No limit (async handling)

---

## Authentication

Currently, the API does not require authentication. For production deployment, consider:

1. Adding API key authentication
2. Implementing JWT tokens
3. Rate limiting by IP or user

---

## CORS & Access Control

The API is configured with permissive CORS:
- **Allow Origins:** `*`
- **Allow Methods:** `GET, POST, PUT, DELETE, OPTIONS`
- **Allow Headers:** `*`

For production, restrict to specific origins.

---

## Version History

### v4.0.0 (Current)
- Complete async/await implementation
- Standalone operation without external VDBs
- Graceful degradation support
- Comprehensive health checks
- Batch operation support
- Full endpoint documentation

### v3.0.0
- Initial hybrid RAG implementation
- Vector DB integration

### v2.0.0
- Basic consultation endpoints

---

## Support & Issues

For issues, questions, or feature requests, please refer to the project documentation or contact support.

**Documentation:** `/docs` (Swagger UI)

**OpenAPI Schema:** `/openapi.json`
