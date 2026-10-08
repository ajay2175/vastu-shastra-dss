"""Tests for enhanced features and integrations."""

import pytest
from models.response_schemas import (
    ConsultationRequest,
    RecommendationItem,
    SpaceAnalysis,
)


def test_consultation_request_validation():
    """Test consultation request validation."""
    request = ConsultationRequest(
        space_name="Master Bedroom",
        space_type="bedroom",
        primary_direction="southwest",
        purpose="Sleeping",
    )

    assert request.space_name == "Master Bedroom"
    assert request.space_type == "bedroom"
    assert request.primary_direction == "southwest"
    assert request.purpose == "Sleeping"


def test_recommendation_item():
    """Test recommendation item."""
    rec = RecommendationItem(
        title="Add Water Feature",
        description="Place a water fountain in the north direction",
        priority="high",
        category="Element Balance",
    )

    assert rec.title == "Add Water Feature"
    assert rec.priority == "high"
    assert rec.category == "Element Balance"


def test_space_analysis():
    """Test space analysis schema."""
    analysis = SpaceAnalysis(
        space_name="Living Room",
        space_type="living_room",
        direction="north",
        compliance_score=75.5,
    )

    assert analysis.space_name == "Living Room"
    assert analysis.compliance_score == 75.5


def test_recommendation_priority_levels():
    """Test all recommendation priority levels."""
    priorities = ["low", "medium", "high", "critical"]

    for priority in priorities:
        rec = RecommendationItem(
            title="Test",
            description="Test recommendation",
            priority=priority,
            category="Test",
        )
        assert rec.priority == priority


def test_space_analysis_compliance_bounds():
    """Test compliance score bounds."""
    with pytest.raises(ValueError):
        SpaceAnalysis(
            space_name="Test",
            space_type="bedroom",
            direction="north",
            compliance_score=150,  # Should fail - > 100
        )

    with pytest.raises(ValueError):
        SpaceAnalysis(
            space_name="Test",
            space_type="bedroom",
            direction="north",
            compliance_score=-10,  # Should fail - < 0
        )
