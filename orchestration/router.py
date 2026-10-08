"""Model routing and selection logic for multi-model orchestration."""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
from datetime import datetime, timedelta
import anthropic

from .prompts import (
    INTENT_DETECTION_PROMPT,
    GEOMETRIC_VALIDATION_PROMPT,
    CROSS_SYSTEM_SYNTHESIS_PROMPT,
    STRUCTURED_OUTPUT_PROMPT,
    create_cache_control_block,
)

logger = logging.getLogger(__name__)


class ModelType(str, Enum):
    """Available model types in the orchestration system."""

    INTENT_DETECTION = "claude-opus"  # Main reasoning model
    GEOMETRIC_VALIDATION = "claude-sonnet"  # Geometric specialist
    SYNTHESIS = "claude-sonnet"  # Cross-system synthesis
    OUTPUT_GENERATION = "claude-sonnet"  # Structured output


class ModelHealth:
    """Track model health and availability."""

    def __init__(self, model_name: str):
        self.model_name = model_name
        self.last_success = datetime.now()
        self.last_failure: Optional[datetime] = None
        self.failure_count = 0
        self.success_count = 0
        self.avg_latency_ms = 0.0
        self.is_available = True

    def record_success(self, latency_ms: float):
        """Record successful model call."""
        self.last_success = datetime.now()
        self.success_count += 1
        self.failure_count = 0
        # Exponential moving average
        self.avg_latency_ms = (self.avg_latency_ms * 0.8) + (latency_ms * 0.2)
        self.is_available = True

    def record_failure(self, error: str):
        """Record failed model call."""
        self.last_failure = datetime.now()
        self.failure_count += 1
        logger.warning(f"Model {self.model_name} failure #{self.failure_count}: {error}")

        # Mark unavailable after 3 failures
        if self.failure_count >= 3:
            self.is_available = False
            logger.error(f"Model {self.model_name} marked unavailable after {self.failure_count} failures")

    def get_health_score(self) -> float:
        """Calculate model health score 0-1."""
        if not self.is_available:
            return 0.0

        total_calls = self.success_count + self.failure_count
        if total_calls == 0:
            return 0.8  # Unknown state

        # Primary factor: success rate
        success_rate = self.success_count / total_calls

        # Secondary factor: recency (recent success better)
        time_since_last_success = (datetime.now() - self.last_success).total_seconds()
        recency_factor = 1.0 if time_since_last_success < 300 else 0.8

        return success_rate * recency_factor


class ModelRouter:
    """Routes queries to appropriate models and aggregates responses."""

    def __init__(self, api_key: str, model_fallbacks: Optional[Dict[ModelType, List[str]]] = None):
        """
        Initialize the model router.

        Args:
            api_key: Anthropic API key
            model_fallbacks: Dict of model types to fallback model names
        """
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model_health: Dict[str, ModelHealth] = {}

        # Default model mapping
        self.model_map: Dict[ModelType, str] = {
            ModelType.INTENT_DETECTION: "claude-3-5-sonnet-20241022",
            ModelType.GEOMETRIC_VALIDATION: "claude-3-5-sonnet-20241022",
            ModelType.SYNTHESIS: "claude-3-5-sonnet-20241022",
            ModelType.OUTPUT_GENERATION: "claude-3-5-sonnet-20241022",
        }

        # Fallback models for each type
        self.fallbacks: Dict[ModelType, List[str]] = model_fallbacks or {
            ModelType.INTENT_DETECTION: ["claude-3-5-haiku-20241022"],
            ModelType.GEOMETRIC_VALIDATION: ["claude-3-5-haiku-20241022"],
            ModelType.SYNTHESIS: ["claude-3-5-haiku-20241022"],
            ModelType.OUTPUT_GENERATION: ["claude-3-5-haiku-20241022"],
        }

        # Initialize health tracking
        for model_name in set(list(self.model_map.values()) + sum(self.fallbacks.values(), [])):
            self.model_health[model_name] = ModelHealth(model_name)

        # Response cache for identical queries
        self.response_cache: Dict[str, Any] = {}
        self.cache_ttl = timedelta(hours=1)

    def get_available_model(self, model_type: ModelType) -> Optional[str]:
        """
        Get the best available model for the given type.

        Returns primary model if healthy, otherwise tries fallbacks.
        """
        primary_model = self.model_map.get(model_type)
        if primary_model and self.model_health[primary_model].is_available:
            return primary_model

        # Try fallbacks
        for fallback_model in self.fallbacks.get(model_type, []):
            if self.model_health[fallback_model].is_available:
                logger.info(f"Using fallback model {fallback_model} for {model_type}")
                return fallback_model

        logger.error(f"No available models for type {model_type}")
        return None

    async def detect_intent(
        self,
        query: str,
        space_type: str = "general",
        location: str = "unknown",
        issue_type: str = "general",
        user_background: str = "general",
    ) -> Dict[str, Any]:
        """
        Detect the intent and routing for a query.

        Uses Claude Opus (main synthesis model) for intent detection.
        """
        model = self.get_available_model(ModelType.INTENT_DETECTION)
        if not model:
            return self._create_fallback_intent_response(query)

        system_prompt, user_template = INTENT_DETECTION_PROMPT.format(
            query=query,
            space_type=space_type,
            location=location,
            issue_type=issue_type,
            user_background=user_background,
        )

        try:
            import time

            start = time.time()

            # Use prompt caching for intent detection
            response = self.client.messages.create(
                model=model,
                max_tokens=1024,
                system=[
                    {
                        "type": "text",
                        "text": system_prompt,
                        "cache_control": {"type": "ephemeral"},
                    }
                ],
                messages=[
                    {
                        "role": "user",
                        "content": user_template,
                    }
                ],
            )

            latency_ms = (time.time() - start) * 1000
            self.model_health[model].record_success(latency_ms)

            # Extract JSON from response
            content = response.content[0].text
            intent_data = self._extract_json(content)

            return {
                "status": "success",
                "intent": intent_data,
                "model_used": model,
                "latency_ms": latency_ms,
            }

        except Exception as e:
            self.model_health[model].record_failure(str(e))
            logger.error(f"Intent detection failed: {e}")
            return self._create_fallback_intent_response(query)

    async def validate_geometric_aspects(
        self,
        space_details: Dict[str, Any],
        current_analysis: Dict[str, Any],
        directional_context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Validate geometric aspects using Grok-equivalent (geometric validation model).

        Specialized model for spatial/geometric validation.
        """
        model = self.get_available_model(ModelType.GEOMETRIC_VALIDATION)
        if not model:
            return self._create_fallback_geometric_response(space_details)

        system_prompt, user_template = GEOMETRIC_VALIDATION_PROMPT.format(
            space_details=json.dumps(space_details, indent=2),
            current_analysis=json.dumps(current_analysis, indent=2),
            directional_context=json.dumps(directional_context, indent=2),
        )

        try:
            import time

            start = time.time()

            response = self.client.messages.create(
                model=model,
                max_tokens=2048,
                system=[
                    {
                        "type": "text",
                        "text": system_prompt,
                        "cache_control": {"type": "ephemeral"},
                    }
                ],
                messages=[
                    {
                        "role": "user",
                        "content": user_template,
                    }
                ],
            )

            latency_ms = (time.time() - start) * 1000
            self.model_health[model].record_success(latency_ms)

            content = response.content[0].text
            validation_data = self._extract_json(content)

            return {
                "status": "success",
                "validation": validation_data,
                "model_used": model,
                "latency_ms": latency_ms,
            }

        except Exception as e:
            self.model_health[model].record_failure(str(e))
            logger.error(f"Geometric validation failed: {e}")
            return self._create_fallback_geometric_response(space_details)

    async def synthesize_cross_systems(
        self,
        vastu_analysis: Dict[str, Any],
        supplementary_data: Dict[str, Any],
        reasoning_context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Synthesize cross-system insights (Gemini-equivalent).

        Integrates Vastu with available health/astrological data.
        """
        model = self.get_available_model(ModelType.SYNTHESIS)
        if not model:
            return self._create_fallback_synthesis_response(vastu_analysis)

        system_prompt, user_template = CROSS_SYSTEM_SYNTHESIS_PROMPT.format(
            vastu_analysis=json.dumps(vastu_analysis, indent=2),
            supplementary_data=json.dumps(supplementary_data, indent=2),
            reasoning_context=json.dumps(reasoning_context, indent=2),
        )

        try:
            import time

            start = time.time()

            response = self.client.messages.create(
                model=model,
                max_tokens=2048,
                system=[
                    {
                        "type": "text",
                        "text": system_prompt,
                        "cache_control": {"type": "ephemeral"},
                    }
                ],
                messages=[
                    {
                        "role": "user",
                        "content": user_template,
                    }
                ],
            )

            latency_ms = (time.time() - start) * 1000
            self.model_health[model].record_success(latency_ms)

            content = response.content[0].text
            synthesis_data = self._extract_json(content)

            return {
                "status": "success",
                "synthesis": synthesis_data,
                "model_used": model,
                "latency_ms": latency_ms,
            }

        except Exception as e:
            self.model_health[model].record_failure(str(e))
            logger.error(f"Cross-system synthesis failed: {e}")
            return self._create_fallback_synthesis_response(vastu_analysis)

    async def generate_structured_output(
        self,
        analysis_results: Dict[str, Any],
        geometric_results: Dict[str, Any],
        synthesis_results: Dict[str, Any],
        schema_requirements: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Generate structured output (GPT-5-equivalent).

        Produces standardized, schema-compliant response.
        """
        model = self.get_available_model(ModelType.OUTPUT_GENERATION)
        if not model:
            return self._create_fallback_output_response(analysis_results)

        system_prompt, user_template = STRUCTURED_OUTPUT_PROMPT.format(
            analysis_results=json.dumps(analysis_results, indent=2),
            geometric_results=json.dumps(geometric_results, indent=2),
            synthesis_results=json.dumps(synthesis_results, indent=2),
            schema_requirements=json.dumps(schema_requirements, indent=2),
        )

        try:
            import time

            start = time.time()

            response = self.client.messages.create(
                model=model,
                max_tokens=4096,
                system=[
                    {
                        "type": "text",
                        "text": system_prompt,
                        "cache_control": {"type": "ephemeral"},
                    }
                ],
                messages=[
                    {
                        "role": "user",
                        "content": user_template,
                    }
                ],
            )

            latency_ms = (time.time() - start) * 1000
            self.model_health[model].record_success(latency_ms)

            content = response.content[0].text
            output_data = self._extract_json(content)

            return {
                "status": "success",
                "output": output_data,
                "model_used": model,
                "latency_ms": latency_ms,
            }

        except Exception as e:
            self.model_health[model].record_failure(str(e))
            logger.error(f"Output generation failed: {e}")
            return self._create_fallback_output_response(analysis_results)

    def get_model_health_status(self) -> Dict[str, Dict[str, Any]]:
        """Get health status for all models."""
        return {
            model_name: {
                "available": health.is_available,
                "health_score": health.get_health_score(),
                "success_count": health.success_count,
                "failure_count": health.failure_count,
                "avg_latency_ms": round(health.avg_latency_ms, 2),
                "last_success": health.last_success.isoformat(),
                "last_failure": health.last_failure.isoformat() if health.last_failure else None,
            }
            for model_name, health in self.model_health.items()
        }

    # ========================================================================
    # FALLBACK RESPONSES (Graceful Degradation)
    # ========================================================================

    def _create_fallback_intent_response(self, query: str) -> Dict[str, Any]:
        """Create fallback intent response when model unavailable."""
        return {
            "status": "fallback",
            "intent": {
                "query_type": "general",
                "required_models": ["intent_detection"],
                "spatial_focus": "space",
                "reasoning_depth": "moderate",
                "requires_evidence": True,
                "priority": "medium",
                "confidence": 0.5,
                "routing_rationale": "Fallback routing due to model unavailability",
            },
            "model_used": "fallback",
            "error": "Primary models unavailable, using default routing",
        }

    def _create_fallback_geometric_response(self, space_details: Dict[str, Any]) -> Dict[str, Any]:
        """Create fallback geometric validation response."""
        return {
            "status": "fallback",
            "validation": {
                "geometric_issues": [],
                "geometric_harmony_score": 50,
                "directional_compliance": {},
                "geometric_adjustments": [],
                "geometric_remedies": [],
                "confidence_scores": {},
            },
            "model_used": "fallback",
            "error": "Geometric validation model unavailable",
        }

    def _create_fallback_synthesis_response(self, vastu_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Create fallback synthesis response."""
        return {
            "status": "fallback",
            "synthesis": {
                "system_integration_points": [],
                "enhanced_recommendations": vastu_analysis.get("recommendations", []),
                "temporal_considerations": [],
                "health_correlations": [],
                "astrological_timing": None,
                "integration_confidence": 0.5,
            },
            "model_used": "fallback",
            "error": "Synthesis model unavailable",
        }

    def _create_fallback_output_response(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Create fallback output generation response."""
        return {
            "status": "fallback",
            "output": {
                "executive_summary": "Consultation generated with limited model availability",
                "findings": analysis_results.get("findings", []),
                "recommendations": analysis_results.get("recommendations", []),
                "implementation_plan": [],
                "expected_outcomes": [],
                "follow_up_protocol": [],
                "confidence_metrics": {"overall": 0.5},
                "references": [],
            },
            "model_used": "fallback",
            "error": "Output generation model unavailable",
        }

    # ========================================================================
    # UTILITY FUNCTIONS
    # ========================================================================

    @staticmethod
    def _extract_json(text: str) -> Dict[str, Any]:
        """Extract JSON from model response, handling markdown code blocks."""
        try:
            # Try direct JSON parsing first
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Try extracting from markdown code block
        import re

        json_match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        # Fallback: try to find JSON object in text
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            try:
                return json.loads(text[start:end])
            except json.JSONDecodeError:
                pass

        logger.warning("Failed to extract JSON from response")
        return {}

    def set_model(self, model_type: ModelType, model_name: str):
        """Override model selection for a specific type."""
        self.model_map[model_type] = model_name
        if model_name not in self.model_health:
            self.model_health[model_name] = ModelHealth(model_name)
        logger.info(f"Set {model_type} to {model_name}")

    def add_fallback(self, model_type: ModelType, model_name: str):
        """Add a fallback model for a specific type."""
        if model_type not in self.fallbacks:
            self.fallbacks[model_type] = []
        self.fallbacks[model_type].append(model_name)
        if model_name not in self.model_health:
            self.model_health[model_name] = ModelHealth(model_name)
        logger.info(f"Added fallback {model_name} for {model_type}")
