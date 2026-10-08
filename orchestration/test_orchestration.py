"""Unit tests for multi-model orchestration layer."""

import pytest
import asyncio
import json
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime, timedelta

from orchestration.router import ModelRouter, ModelType, ModelHealth
from orchestration.orchestrator import ConsultationOrchestrator, ConsultationRequest, ConsultationResponse
from orchestration.prompts import (
    INTENT_DETECTION_PROMPT,
    GEOMETRIC_VALIDATION_PROMPT,
    CROSS_SYSTEM_SYNTHESIS_PROMPT,
    STRUCTURED_OUTPUT_PROMPT,
)


class TestModelHealth:
    """Test ModelHealth tracking."""

    def test_initialization(self):
        """Test ModelHealth initialization."""
        health = ModelHealth("claude-opus")
        assert health.model_name == "claude-opus"
        assert health.failure_count == 0
        assert health.success_count == 0
        assert health.is_available is True

    def test_record_success(self):
        """Test recording successful model call."""
        health = ModelHealth("claude-opus")
        health.record_success(1000.0)

        assert health.success_count == 1
        assert health.failure_count == 0
        assert health.is_available is True
        assert health.avg_latency_ms == 1000.0

    def test_record_failure(self):
        """Test recording failed model call."""
        health = ModelHealth("claude-opus")
        health.record_failure("Test error")

        assert health.failure_count == 1
        assert health.is_available is True

    def test_auto_unavailable_after_failures(self):
        """Test model marked unavailable after 3 failures."""
        health = ModelHealth("claude-opus")

        health.record_failure("Error 1")
        assert health.is_available is True

        health.record_failure("Error 2")
        assert health.is_available is True

        health.record_failure("Error 3")
        assert health.is_available is False

    def test_health_score_calculation(self):
        """Test health score calculation."""
        health = ModelHealth("claude-opus")

        # With no calls
        score = health.get_health_score()
        assert score == 0.8  # Unknown state

        # After success
        health.record_success(500.0)
        score = health.get_health_score()
        assert score > 0.8  # Should improve

        # With mixed results
        health.record_failure("Error")
        score = health.get_health_score()
        # Score should be lower due to failure


class TestPromptTemplates:
    """Test prompt template functionality."""

    def test_intent_detection_format(self):
        """Test intent detection prompt formatting."""
        system, user = INTENT_DETECTION_PROMPT.format(
            query="Test query",
            space_type="bedroom",
            location="north",
            issue_type="energy",
            user_background="general",
        )

        assert "Test query" in user
        assert "bedroom" in user
        assert "north" in user
        assert len(system) > 0
        assert len(user) > 0

    def test_geometric_validation_format(self):
        """Test geometric validation prompt formatting."""
        system, user = GEOMETRIC_VALIDATION_PROMPT.format(
            space_details='{"type": "room"}',
            current_analysis='{"score": 50}',
            directional_context='{"focus": "north"}',
        )

        assert "room" in user
        assert "score" in user
        assert len(system) > 0
        assert len(user) > 0

    def test_synthesis_format(self):
        """Test cross-system synthesis prompt formatting."""
        system, user = CROSS_SYSTEM_SYNTHESIS_PROMPT.format(
            vastu_analysis='{"findings": []}',
            supplementary_data='{}',
            reasoning_context='{}',
        )

        assert len(system) > 0
        assert len(user) > 0

    def test_output_generation_format(self):
        """Test output generation prompt formatting."""
        system, user = STRUCTURED_OUTPUT_PROMPT.format(
            analysis_results='{}',
            geometric_results='{}',
            synthesis_results='{}',
            schema_requirements='{}',
        )

        assert len(system) > 0
        assert len(user) > 0


class TestModelRouter:
    """Test ModelRouter functionality."""

    def test_initialization(self):
        """Test router initialization."""
        router = ModelRouter(api_key="test-key")

        assert router.client is not None
        assert len(router.model_map) > 0
        assert len(router.model_health) > 0

    def test_get_available_model_primary(self):
        """Test getting primary available model."""
        router = ModelRouter(api_key="test-key")

        # Primary should be available
        model = router.get_available_model(ModelType.INTENT_DETECTION)
        assert model is not None

    def test_get_available_model_fallback(self):
        """Test fallback model selection."""
        router = ModelRouter(api_key="test-key")

        # Mark primary unavailable
        primary = router.model_map[ModelType.INTENT_DETECTION]
        router.model_health[primary].is_available = False

        # Should return fallback
        model = router.get_available_model(ModelType.INTENT_DETECTION)
        assert model in router.fallbacks[ModelType.INTENT_DETECTION]

    def test_set_model(self):
        """Test setting custom model."""
        router = ModelRouter(api_key="test-key")

        router.set_model(ModelType.INTENT_DETECTION, "claude-custom")
        assert router.model_map[ModelType.INTENT_DETECTION] == "claude-custom"

    def test_add_fallback(self):
        """Test adding fallback model."""
        router = ModelRouter(api_key="test-key")

        initial_count = len(router.fallbacks[ModelType.INTENT_DETECTION])
        router.add_fallback(ModelType.INTENT_DETECTION, "claude-fallback")

        assert len(router.fallbacks[ModelType.INTENT_DETECTION]) == initial_count + 1

    def test_extract_json_direct(self):
        """Test extracting JSON from direct response."""
        json_data = '{"key": "value", "number": 42}'
        result = ModelRouter._extract_json(json_data)

        assert result == {"key": "value", "number": 42}

    def test_extract_json_markdown(self):
        """Test extracting JSON from markdown code block."""
        markdown_response = """Here's your JSON:
```json
{"key": "value"}
```
"""
        result = ModelRouter._extract_json(markdown_response)
        assert result == {"key": "value"}

    def test_extract_json_fallback(self):
        """Test JSON extraction with embedded JSON."""
        text = 'Response: {"key": "value"} more text'
        result = ModelRouter._extract_json(text)
        assert result == {"key": "value"}

    def test_model_health_status(self):
        """Test getting model health status."""
        router = ModelRouter(api_key="test-key")
        status = router.get_model_health_status()

        assert isinstance(status, dict)
        for model_name, health in status.items():
            assert "available" in health
            assert "health_score" in health
            assert "success_count" in health
            assert "failure_count" in health


class TestConsultationRequest:
    """Test ConsultationRequest."""

    def test_initialization(self):
        """Test request initialization."""
        request = ConsultationRequest(
            query="Test query",
            space_type="bedroom",
            location="north",
        )

        assert request.query == "Test query"
        assert request.space_type == "bedroom"
        assert request.location == "north"
        assert request.request_id is not None

    def test_custom_request_id(self):
        """Test setting custom request ID."""
        custom_id = "custom-123"
        request = ConsultationRequest(
            query="Test",
            request_id=custom_id,
        )

        assert request.request_id == custom_id


class TestConsultationResponse:
    """Test ConsultationResponse."""

    def test_to_dict(self):
        """Test response to dictionary conversion."""
        response = ConsultationResponse(
            request_id="req-123",
            status="success",
            query="Test query",
            executive_summary="Summary",
            findings=[],
            recommendations=[],
            implementation_plan=[],
            expected_outcomes=[],
            follow_up_protocol=[],
            confidence_metrics={"overall": 0.85},
            reasoning_chains=[],
            model_routing={},
            performance_metrics={},
            timestamp=datetime.now().isoformat(),
        )

        response_dict = response.to_dict()
        assert response_dict["request_id"] == "req-123"
        assert response_dict["status"] == "success"
        assert response_dict["query"] == "Test query"

    def test_to_json(self):
        """Test response to JSON conversion."""
        response = ConsultationResponse(
            request_id="req-123",
            status="success",
            query="Test query",
            executive_summary="Summary",
            findings=[],
            recommendations=[],
            implementation_plan=[],
            expected_outcomes=[],
            follow_up_protocol=[],
            confidence_metrics={"overall": 0.85},
            reasoning_chains=[],
            model_routing={},
            performance_metrics={},
            timestamp=datetime.now().isoformat(),
        )

        json_str = response.to_json()
        parsed = json.loads(json_str)

        assert parsed["request_id"] == "req-123"
        assert parsed["status"] == "success"


class TestConsultationOrchestrator:
    """Test ConsultationOrchestrator."""

    def test_initialization(self):
        """Test orchestrator initialization."""
        orchestrator = ConsultationOrchestrator(api_key="test-key")

        assert orchestrator.router is not None
        assert orchestrator.enable_caching is True
        assert len(orchestrator.consultation_history) == 0

    @pytest.mark.asyncio
    async def test_process_consultation_fallback(self):
        """Test consultation processing with fallback."""
        orchestrator = ConsultationOrchestrator(api_key="test-key")

        request = ConsultationRequest(
            query="Test query",
            space_type="bedroom",
        )

        # Mock all model calls to fail so we test fallback
        with patch.object(orchestrator.router, "detect_intent") as mock_intent:
            mock_intent.return_value = {
                "status": "fallback",
                "intent": {
                    "query_type": "general",
                    "confidence": 0.5,
                    "required_models": [],
                    "spatial_focus": "space",
                    "reasoning_depth": "moderate",
                },
                "model_used": "fallback",
            }

            with patch.object(orchestrator.router, "validate_geometric_aspects") as mock_geo:
                mock_geo.return_value = {
                    "status": "fallback",
                    "validation": {
                        "geometric_harmony_score": 50,
                        "confidence_scores": {"overall": 0.5},
                    },
                    "model_used": "fallback",
                }

                with patch.object(orchestrator.router, "synthesize_cross_systems") as mock_syn:
                    mock_syn.return_value = {
                        "status": "fallback",
                        "synthesis": {"integration_confidence": 0.5},
                        "model_used": "fallback",
                    }

                    with patch.object(orchestrator.router, "generate_structured_output") as mock_out:
                        mock_out.return_value = {
                            "status": "fallback",
                            "output": {
                                "executive_summary": "Test response",
                                "findings": [],
                                "recommendations": [],
                                "implementation_plan": [],
                                "expected_outcomes": [],
                                "follow_up_protocol": [],
                                "confidence_metrics": {"overall": 0.5},
                            },
                            "model_used": "fallback",
                        }

                        response = await orchestrator.process_consultation(request)

                        assert response.status == "success"
                        assert response.query == "Test query"
                        assert len(response.reasoning_chains) > 0

    def test_get_consultation_history(self):
        """Test retrieving consultation history."""
        orchestrator = ConsultationOrchestrator(api_key="test-key")

        # Add mock responses
        for i in range(15):
            response = ConsultationResponse(
                request_id=f"req-{i}",
                status="success",
                query=f"Query {i}",
                executive_summary="Summary",
                findings=[],
                recommendations=[],
                implementation_plan=[],
                expected_outcomes=[],
                follow_up_protocol=[],
                confidence_metrics={"overall": 0.85},
                reasoning_chains=[],
                model_routing={},
                performance_metrics={},
                timestamp=datetime.now().isoformat(),
            )
            orchestrator.consultation_history.append(response)

        # Get last 5
        history = orchestrator.get_consultation_history(limit=5)
        assert len(history) == 5
        assert history[-1].request_id == "req-14"

    def test_get_model_health_status(self):
        """Test getting model health status."""
        orchestrator = ConsultationOrchestrator(api_key="test-key")
        status = orchestrator.get_model_health_status()

        assert isinstance(status, dict)
        assert len(status) > 0


# Performance & Integration Tests


class TestPerformanceCharacteristics:
    """Test performance characteristics."""

    def test_model_latency_tracking(self):
        """Test that model latencies are tracked."""
        router = ModelRouter(api_key="test-key")
        model = "claude-opus"

        router.model_health[model].record_success(1500.0)
        router.model_health[model].record_success(1600.0)

        avg = router.model_health[model].avg_latency_ms
        assert 1500 < avg < 1600

    def test_confidence_score_aggregation(self):
        """Test confidence score aggregation."""
        orchestrator = ConsultationOrchestrator(api_key="test-key")

        scores = orchestrator._calculate_confidence_scores(
            intent_confidence=0.9,
            geometric_confidence=0.8,
            synthesis_confidence=0.7,
            output_confidence=0.9,
        )

        assert "overall" in scores
        assert 0 <= scores["overall"] <= 1
        assert scores["output_generation"] == 0.9


# Error Handling Tests


class TestErrorHandling:
    """Test error handling and graceful degradation."""

    def test_fallback_intent_response(self):
        """Test fallback intent response."""
        router = ModelRouter(api_key="test-key")
        fallback = router._create_fallback_intent_response("Test query")

        assert fallback["status"] == "fallback"
        assert fallback["intent"]["query_type"] == "general"
        assert fallback["model_used"] == "fallback"

    def test_fallback_geometric_response(self):
        """Test fallback geometric response."""
        router = ModelRouter(api_key="test-key")
        fallback = router._create_fallback_geometric_response({"type": "room"})

        assert fallback["status"] == "fallback"
        assert fallback["validation"]["geometric_harmony_score"] == 50

    def test_fallback_synthesis_response(self):
        """Test fallback synthesis response."""
        router = ModelRouter(api_key="test-key")
        fallback = router._create_fallback_synthesis_response({})

        assert fallback["status"] == "fallback"
        assert "system_integration_points" in fallback["synthesis"]

    def test_fallback_output_response(self):
        """Test fallback output response."""
        router = ModelRouter(api_key="test-key")
        fallback = router._create_fallback_output_response({})

        assert fallback["status"] == "fallback"
        assert "executive_summary" in fallback["output"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
