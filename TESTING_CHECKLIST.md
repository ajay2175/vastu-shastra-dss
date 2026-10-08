# Vastu Shastra DSS - Testing Checklist for 20 Testers

## Testing Overview

This checklist provides 20+ comprehensive test cases for validating the Vastu Shastra DSS deployment. Each test includes:
- Endpoint to test
- Sample request payload
- Expected response format
- Success criteria

## Getting Started

1. **Access the deployed Space:** https://huggingface.co/spaces/YOUR_USERNAME/vastu-shastra-dss
2. **Use Swagger UI:** Click the public link, then go to `/docs`
3. **Or use cURL:** Follow the cURL commands in each test

## System Endpoints (Tests 1-3)

### Test 1: Health Check - Basic System Status

**Endpoint:** `GET /health`

**cURL:**
```bash
curl https://YOUR_SPACE_URL/health
```

**Expected Response:**
```json
{
  "status": "operational",
  "timestamp": "2024-10-08T...",
  "version": "4.0.0"
}
```

**Success Criteria:**
- ✅ HTTP 200 status
- ✅ "status" field is "operational"
- ✅ Response time < 1 second

---

### Test 2: System Status - Full Details

**Endpoint:** `GET /health/detailed`

**cURL:**
```bash
curl https://YOUR_SPACE_URL/health/detailed
```

**Expected Response:**
```json
{
  "api": {
    "status": "operational",
    "response_time_ms": 45
  },
  "consultation_system": {
    "status": "operational"
  },
  "knowledge_graph": {
    "status": "operational",
    "nodes_count": 570,
    "edges_count": 1994
  },
  "timestamp": "2024-10-08T..."
}
```

**Success Criteria:**
- ✅ All systems show "operational"
- ✅ KG has 570+ nodes and 1900+ edges
- ✅ Response time < 2 seconds

---

### Test 3: API Documentation

**Endpoint:** `GET /docs`

**Manual Test:**
1. Visit the public Space URL
2. Click on the Swagger UI link
3. You should see all available endpoints listed

**Success Criteria:**
- ✅ Swagger UI loads without errors
- ✅ At least 10 endpoints visible
- ✅ Can see request/response schemas

---

## Direction-Based Consultation (Tests 4-9)

### Test 4: North Direction - Bedroom Advice

**Endpoint:** `POST /api/v1/consult/direction`

**Payload:**
```json
{
  "direction": "north",
  "space_type": "bedroom",
  "query": "What are the best practices for a bedroom facing north?",
  "context": {
    "current_state": "needs_improvement",
    "priority": "energy_flow"
  }
}
```

**Success Criteria:**
- ✅ HTTP 200 status
- ✅ Response contains "recommendations" array
- ✅ At least 3 recommendations provided
- ✅ Response time < 15 seconds

---

### Test 5: East Direction - Living Room Advice

**Endpoint:** `POST /api/v1/consult/direction`

**Payload:**
```json
{
  "direction": "east",
  "space_type": "living_room",
  "query": "How to optimize living room energy for east-facing entrance?",
  "context": {
    "current_state": "well_organized"
  }
}
```

**Success Criteria:**
- ✅ Recommendations include placement suggestions
- ✅ References to Vastu principles
- ✅ Actionable advice provided

---

### Test 6: South Direction - Kitchen Advice

**Endpoint:** `POST /api/v1/consult/direction`

**Payload:**
```json
{
  "direction": "south",
  "space_type": "kitchen",
  "query": "Fire element placement and stove position for south-facing kitchen",
  "context": {
    "current_state": "under_renovation"
  }
}
```

**Success Criteria:**
- ✅ Response addresses fire element properties
- ✅ Includes stove/cooking appliance positioning
- ✅ Mentions safety considerations

---

### Test 7: West Direction - Office Advice

**Endpoint:** `POST /api/v1/consult/direction`

**Payload:**
```json
{
  "direction": "west",
  "space_type": "office",
  "query": "Workspace layout and focus optimization for west-facing office",
  "context": {
    "current_state": "business_office"
  }
}
```

**Success Criteria:**
- ✅ Includes productivity recommendations
- ✅ Addresses sun exposure concerns
- ✅ Suggests placement for desk/workspace

---

### Test 8: Northeast Direction - Prayer Room Advice

**Endpoint:** `POST /api/v1/consult/direction`

**Payload:**
```json
{
  "direction": "northeast",
  "space_type": "prayer_room",
  "query": "Sacred space alignment and spiritual energy optimization for northeast",
  "context": {
    "current_state": "meditation_space"
  }
}
```

**Success Criteria:**
- ✅ Addresses spiritual/sacred aspects
- ✅ Includes element balancing recommendations
- ✅ Mentions purification practices

---

### Test 9: Central (Center) Direction - Home Center

**Endpoint:** `POST /api/v1/consult/direction`

**Payload:**
```json
{
  "direction": "center",
  "space_type": "central_area",
  "query": "How to balance central space and create harmony in home center?",
  "context": {
    "current_state": "family_gathering_space"
  }
}
```

**Success Criteria:**
- ✅ Response acknowledges central importance
- ✅ Includes balancing techniques
- ✅ Addresses element harmony

---

## Room-Based Consultation (Tests 10-15)

### Test 10: Bedroom Analysis

**Endpoint:** `POST /api/v1/consult/room`

**Payload:**
```json
{
  "room_type": "bedroom",
  "query": "Complete Vastu analysis for master bedroom improvement",
  "context": {
    "size_category": "medium",
    "occupants": 2,
    "current_issues": ["sleep_problems", "low_energy"]
  }
}
```

**Success Criteria:**
- ✅ Includes sleep quality recommendations
- ✅ Addresses furniture placement
- ✅ Mentions color psychology
- ✅ Suggests energy enhancement techniques

---

### Test 11: Kitchen Analysis

**Endpoint:** `POST /api/v1/consult/room`

**Payload:**
```json
{
  "room_type": "kitchen",
  "query": "Vastu recommendations for kitchen health and prosperity",
  "context": {
    "size_category": "small",
    "has_island": true,
    "current_issues": ["poor_ventilation"]
  }
}
```

**Success Criteria:**
- ✅ Addresses cooking area safety
- ✅ Includes fire element management
- ✅ Suggests water placement
- ✅ Mentions storage organization

---

### Test 12: Living Room Analysis

**Endpoint:** `POST /api/v1/consult/room`

**Payload:**
```json
{
  "room_type": "living_room",
  "query": "Create welcoming space for family gathering and guest comfort",
  "context": {
    "size_category": "large",
    "has_fireplace": false,
    "foot_traffic": "high"
  }
}
```

**Success Criteria:**
- ✅ Addresses social harmony
- ✅ Includes furniture arrangement guidance
- ✅ Suggests seating zone optimization
- ✅ Mentions welcoming energy

---

### Test 13: Office/Workspace Analysis

**Endpoint:** `POST /api/v1/consult/room`

**Payload:**
```json
{
  "room_type": "office",
  "query": "Enhance productivity and focus in home office space",
  "context": {
    "size_category": "small",
    "window_count": 1,
    "current_issues": ["distraction", "low_motivation"]
  }
}
```

**Success Criteria:**
- ✅ Includes desk positioning advice
- ✅ Addresses focus enhancement
- ✅ Suggests lighting optimization
- ✅ Mentions concentration-boosting elements

---

### Test 14: Bathroom Analysis

**Endpoint:** `POST /api/v1/consult/room`

**Payload:**
```json
{
  "room_type": "bathroom",
  "query": "Bathroom cleanliness and negative energy removal protocols",
  "context": {
    "size_category": "medium",
    "has_window": true,
    "current_issues": ["moisture", "odor"]
  }
}
```

**Success Criteria:**
- ✅ Addresses cleansing recommendations
- ✅ Includes moisture management
- ✅ Suggests protective measures
- ✅ Mentions water element management

---

### Test 15: Entrance/Foyer Analysis

**Endpoint:** `POST /api/v1/consult/room`

**Payload:**
```json
{
  "room_type": "entrance",
  "query": "Welcoming entrance that attracts positive energy and good fortune",
  "context": {
    "entrance_type": "main_door",
    "current_state": "ordinary",
    "current_issues": ["lacks_appeal"]
  }
}
```

**Success Criteria:**
- ✅ Addresses first impression importance
- ✅ Includes welcoming elements
- ✅ Suggests symbolic placements
- ✅ Mentions energy flow from entrance

---

## Space Analysis (Tests 16-18)

### Test 16: Full Space Analysis

**Endpoint:** `POST /api/v1/analyze-space`

**Payload:**
```json
{
  "space_type": "residential_apartment",
  "dimensions": {
    "length": 30,
    "width": 25,
    "height": 10
  },
  "direction": "north",
  "current_state": "needs_improvement",
  "context": {
    "occupants": 3,
    "main_issues": ["poor_energy_flow", "financial_stagnation"]
  }
}
```

**Success Criteria:**
- ✅ Returns comprehensive analysis
- ✅ Includes room-by-room recommendations
- ✅ Addresses overall balance
- ✅ Suggests prioritized improvements

---

### Test 17: Space Defect Diagnosis

**Endpoint:** `POST /api/v1/diagnose-defects`

**Payload:**
```json
{
  "space_type": "house",
  "defects": [
    "missing_corner",
    "irregular_shape",
    "blocked_entrance"
  ],
  "description": "L-shaped property with northeast corner cut",
  "context": {
    "severity": "moderate",
    "duration": "since_purchase"
  }
}
```

**Success Criteria:**
- ✅ Identifies each defect correctly
- ✅ Provides remediation strategies
- ✅ Suggests alternative solutions
- ✅ Includes astrological/cosmic reasoning

---

### Test 18: Batch Space Analysis (Multiple Rooms)

**Endpoint:** `POST /api/v1/analyze-spaces-batch`

**Payload:**
```json
{
  "spaces": [
    {
      "room_type": "bedroom",
      "dimensions": {"length": 15, "width": 12},
      "direction": "northwest"
    },
    {
      "room_type": "kitchen",
      "dimensions": {"length": 12, "width": 10},
      "direction": "southeast"
    },
    {
      "room_type": "living_room",
      "dimensions": {"length": 20, "width": 18},
      "direction": "north"
    }
  ]
}
```

**Success Criteria:**
- ✅ Returns analysis for all 3 rooms
- ✅ Each room has independent recommendations
- ✅ Shows cross-room harmony issues
- ✅ Response time < 30 seconds

---

## Advanced Features (Tests 19-20)

### Test 19: Error Handling - Invalid Input

**Endpoint:** `POST /api/v1/consult/direction`

**Payload:**
```json
{
  "direction": "invalid_direction",
  "space_type": "unknown_type",
  "query": ""
}
```

**Success Criteria:**
- ✅ Returns HTTP 422 status (validation error)
- ✅ Provides clear error message
- ✅ Suggests valid direction values
- ✅ Does NOT crash the server

---

### Test 20: Concurrent Requests

**Test Setup:** Send 5-10 simultaneous requests from different clients/terminals

**Command:**
```bash
# Terminal 1
for i in {1..5}; do
  curl -X POST https://YOUR_SPACE_URL/api/v1/consult/direction \
    -H "Content-Type: application/json" \
    -d '{"direction": "north", "space_type": "bedroom", "query": "test '$i'"}' &
done
wait
```

**Success Criteria:**
- ✅ All requests complete successfully
- ✅ No "connection refused" errors
- ✅ Response time remains consistent
- ✅ No duplicate or mixed responses

---

## Performance Benchmarks

### Target Metrics

| Metric | Target | Acceptable |
|--------|--------|-----------|
| Health check response | < 1s | < 2s |
| Detailed health check | < 2s | < 5s |
| Direction consultation | < 15s | < 30s |
| Room consultation | < 15s | < 30s |
| Space analysis | < 20s | < 45s |
| Batch analysis (3 rooms) | < 30s | < 60s |
| Concurrent (10 requests) | < 40s | < 60s |

### Load Testing Guidance

**Light Load (Good Sign):**
- 5-10 concurrent users
- Consistent response times
- No errors or 500 responses

**Moderate Load (Acceptable):**
- 10-20 concurrent users
- Some response time increase (1.2x-1.5x baseline)
- Occasional timeouts are OK

**Heavy Load (Expected Limit):**
- 20+ concurrent users
- Response times increase 2x-3x
- May see occasional 503 (server busy) responses

---

## Tester Feedback Form

For each test, rate on a scale of 1-5:

```
Test Number: __
Endpoint: ______________
Status: (Success / Partial / Failed)
Response Time: __ seconds
Comments: ________________________

Would you recommend deployment? (Yes / No)
Issues encountered: ________________________
Feature requests: ________________________
```

---

## Issue Reporting

If you encounter issues, report with:

1. **Test number** that failed
2. **Exact error message** (copy full response)
3. **Time it occurred**
4. **Your approximate location** (for latency analysis)
5. **Screenshot** if UI-related

Report issues at: https://github.com/ajay2175/vastu-shastra-dss/issues

---

## Success Criteria Summary

**Deployment is successful when:**
- ✅ Tests 1-3 (System endpoints) all pass
- ✅ Tests 4-9 (Direction consultation) average score > 4/5
- ✅ Tests 10-15 (Room consultation) average score > 4/5
- ✅ Tests 16-18 (Space analysis) all complete < 45s
- ✅ Tests 19-20 (Advanced) handle edge cases gracefully
- ✅ At least 15 out of 20 testers report "Yes" to deployment recommendation

---

## Testing Timeline

- **Day 1:** Tests 1-5 (Quick validation)
- **Day 1-2:** Tests 6-15 (Comprehensive room analysis)
- **Day 2:** Tests 16-18 (Advanced features)
- **Day 2-3:** Tests 19-20 + Performance benchmarking
- **Day 3:** Feedback collection and deployment sign-off

---

**Version:** 1.0  
**Last Updated:** October 8, 2024  
**Total Test Cases:** 20+  
**Estimated Testing Time:** 2-3 hours per tester
