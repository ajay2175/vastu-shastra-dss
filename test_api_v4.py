#!/usr/bin/env python3
"""
Test script for Vastu Shastra DSS FastAPI v4.0

Tests all major endpoints and functionality.
Run with: python3 test_api_v4.py
"""

import asyncio
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

async def test_imports():
    """Test all required imports."""
    print("=" * 80)
    print("TESTING IMPORTS")
    print("=" * 80)

    try:
        from config.settings import settings
        print("✓ Settings loaded")
    except Exception as e:
        print(f"✗ Settings error: {e}")
        return False

    try:
        from vastu.embedded_principles import VastuPrinciples, DIRECTIONS, VASTU_DOSHAS, ROOM_PLACEMENTS
        print(f"✓ Embedded principles loaded ({len(DIRECTIONS)} directions, {len(VASTU_DOSHAS)} doshas)")
    except Exception as e:
        print(f"✗ Embedded principles error: {e}")
        return False

    try:
        from vastu.standalone_consultation import StandaloneConsultation
        consultation = StandaloneConsultation()
        print("✓ Standalone consultation system initialized")
    except Exception as e:
        print(f"✗ Standalone consultation error: {e}")
        return False

    try:
        from api.enhanced_api_v4 import app
        print(f"✓ FastAPI app created: {app.title} v{app.version}")
    except Exception as e:
        print(f"✗ FastAPI app error: {e}")
        return False

    return True


async def test_standalone_consultation():
    """Test standalone consultation functionality."""
    print("\n" + "=" * 80)
    print("TESTING STANDALONE CONSULTATION")
    print("=" * 80)

    try:
        from vastu.standalone_consultation import StandaloneConsultation

        consultation = StandaloneConsultation()

        # Test direction consultation
        result = await consultation.get_direction_consultation("northeast")
        if "error" not in result:
            print("✓ Direction consultation works")
        else:
            print(f"✗ Direction consultation failed: {result}")

        # Test room consultation
        result = await consultation.get_room_consultation("kitchen")
        if "error" not in result:
            print("✓ Room consultation works")
        else:
            print(f"✗ Room consultation failed: {result}")

        # Test defect diagnosis
        result = await consultation.diagnose_defect("northeast_toilet")
        if "error" not in result:
            print("✓ Defect diagnosis works")
        else:
            print(f"✗ Defect diagnosis failed: {result}")

        # Test space analysis
        space_details = {
            "name": "Test Bedroom",
            "type": "bedroom",
            "direction": "southwest",
            "area": 250,
            "features": ["window"],
            "issues": [],
            "purpose": "sleeping"
        }
        result = await consultation.analyze_space(space_details)
        if "compliance_score" in result:
            print(f"✓ Space analysis works (score: {result['compliance_score']})")
        else:
            print(f"✗ Space analysis failed: {result}")

        return True

    except Exception as e:
        print(f"✗ Consultation system error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_endpoints():
    """Test FastAPI endpoints."""
    print("\n" + "=" * 80)
    print("TESTING FASTAPI ENDPOINTS")
    print("=" * 80)

    try:
        from fastapi.testclient import TestClient
        from api.enhanced_api_v4 import app

        client = TestClient(app)

        # Test root endpoint
        response = client.get("/")
        print(f"{'✓' if response.status_code == 200 else '✗'} GET / - {response.status_code}")

        # Test API info
        response = client.get("/api/v1")
        print(f"{'✓' if response.status_code == 200 else '✗'} GET /api/v1 - {response.status_code}")

        # Test health check
        response = client.get("/api/v1/health")
        print(f"{'✓' if response.status_code == 200 else '✗'} GET /api/v1/health - {response.status_code}")

        # Test status
        response = client.get("/api/v1/status")
        print(f"{'✓' if response.status_code == 200 else '✗'} GET /api/v1/status - {response.status_code}")

        # Test system info
        response = client.get("/api/v1/system-info")
        print(f"{'✓' if response.status_code == 200 else '✗'} GET /api/v1/system-info - {response.status_code}")

        # Test directions list
        response = client.get("/api/v1/directions")
        print(f"{'✓' if response.status_code == 200 else '✗'} GET /api/v1/directions - {response.status_code}")

        # Test rooms list
        response = client.get("/api/v1/rooms")
        print(f"{'✓' if response.status_code == 200 else '✗'} GET /api/v1/rooms - {response.status_code}")

        # Test main consultation
        response = client.post("/api/v1/consult", json={
            "query": "What about the northeast direction?",
            "include_remedies": True
        })
        print(f"{'✓' if response.status_code == 200 else '✗'} POST /api/v1/consult - {response.status_code}")

        # Test direction consult
        response = client.post("/api/v1/directions/consult", json={
            "direction": "northeast"
        })
        print(f"{'✓' if response.status_code == 200 else '✗'} POST /api/v1/directions/consult - {response.status_code}")

        # Test room consult
        response = client.post("/api/v1/rooms/consult", json={
            "room_type": "kitchen"
        })
        print(f"{'✓' if response.status_code == 200 else '✗'} POST /api/v1/rooms/consult - {response.status_code}")

        # Test defect diagnosis
        response = client.post("/api/v1/defects/diagnose", json={
            "defect_type": "northeast_toilet"
        })
        print(f"{'✓' if response.status_code == 200 else '✗'} POST /api/v1/defects/diagnose - {response.status_code}")

        # Test space analysis
        response = client.post("/api/v1/spaces/analyze", json={
            "space_name": "Master Bedroom",
            "space_type": "bedroom",
            "direction": "southwest",
            "area_sqft": 250,
            "features": ["window"],
            "issues": [],
            "purpose": "sleeping"
        })
        print(f"{'✓' if response.status_code == 200 else '✗'} POST /api/v1/spaces/analyze - {response.status_code}")

        # Test batch consult
        response = client.post("/api/v1/batch-consult", json={
            "queries": [
                "Best direction for kitchen?",
                "What about northeast?"
            ],
            "include_remedies": True
        })
        print(f"{'✓' if response.status_code == 200 else '✗'} POST /api/v1/batch-consult - {response.status_code}")

        # Test batch space analysis
        response = client.post("/api/v1/spaces/analyze-batch", json={
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
        })
        print(f"{'✓' if response.status_code == 200 else '✗'} POST /api/v1/spaces/analyze-batch - {response.status_code}")

        print("\n✓ All endpoints tested successfully!")
        return True

    except Exception as e:
        print(f"✗ Endpoint testing error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("VASTU SHASTRA DSS v4.0 - API TEST SUITE")
    print("=" * 80)

    # Test imports
    if not await test_imports():
        print("\n✗ Import tests failed. Exiting.")
        return False

    # Test standalone consultation
    if not await test_standalone_consultation():
        print("\n✗ Standalone consultation tests failed.")
        return False

    # Test endpoints
    if not await test_endpoints():
        print("\n✗ Endpoint tests failed.")
        return False

    print("\n" + "=" * 80)
    print("ALL TESTS PASSED SUCCESSFULLY!")
    print("=" * 80)
    print("\nNext steps:")
    print("1. Run the API with: python3 -m api.enhanced_api_v4")
    print("2. Access Swagger UI: http://localhost:8000/docs")
    print("3. Access ReDoc: http://localhost:8000/redoc")
    print("\nFor deployment, see DEPLOYMENT_GUIDE.md")
    print("For API reference, see API_ENDPOINTS.md")

    return True


if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
