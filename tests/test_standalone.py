"""Tests for standalone consultation system."""

import pytest
import asyncio
from vastu.standalone_consultation import StandaloneConsultation


@pytest.fixture
def consultation_system():
    """Create a consultation system for testing."""
    return StandaloneConsultation()


@pytest.mark.asyncio
async def test_analyze_space_basic(consultation_system):
    """Test basic space analysis."""
    space_details = {
        "name": "Master Bedroom",
        "type": "bedroom",
        "direction": "southwest",
        "area": 200,
        "features": ["window", "door"],
        "issues": [],
        "purpose": "Sleeping",
    }

    result = await consultation_system.analyze_space(space_details)

    assert result is not None
    assert "space_name" in result
    assert "compliance_score" in result
    assert result["compliance_score"] >= 0
    assert result["compliance_score"] <= 100


@pytest.mark.asyncio
async def test_direction_consultation(consultation_system):
    """Test direction consultation."""
    result = await consultation_system.get_direction_consultation("northeast")

    assert result is not None
    assert "direction" in result
    assert "principle_name" in result


@pytest.mark.asyncio
async def test_room_consultation(consultation_system):
    """Test room consultation."""
    result = await consultation_system.get_room_consultation("bedroom")

    assert result is not None
    assert "room_type" in result
    assert "best_directions" in result


@pytest.mark.asyncio
async def test_defect_diagnosis(consultation_system):
    """Test defect diagnosis."""
    result = await consultation_system.diagnose_defect("toilet_northeast")

    assert result is not None
    assert "defect" in result
    assert "severity" in result
    assert "remedies" in result


@pytest.mark.asyncio
async def test_batch_analyze_spaces(consultation_system):
    """Test batch space analysis."""
    spaces = [
        {
            "name": "Room 1",
            "type": "bedroom",
            "direction": "south",
            "purpose": "Sleeping",
        },
        {
            "name": "Room 2",
            "type": "kitchen",
            "direction": "southeast",
            "purpose": "Cooking",
        },
    ]

    results = await consultation_system.batch_analyze_spaces(spaces)

    assert len(results) == 2
    assert all("space_name" in r for r in results)


@pytest.mark.asyncio
async def test_consultation_report_generation(consultation_system):
    """Test consultation report generation."""
    space_data = {
        "name": "Living Room",
        "type": "living_room",
        "direction": "north",
        "issues": [],
        "purpose": "Gathering",
    }

    report = await consultation_system.create_consultation_report(space_data)

    assert isinstance(report, str)
    assert "VASTU SHASTRA CONSULTATION REPORT" in report
    assert "COMPLIANCE ASSESSMENT" in report
    assert "RECOMMENDATIONS" in report
