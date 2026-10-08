"""Consultation orchestrator coordinating multi-model reasoning flow."""

import asyncio
import logging
import json
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from dataclasses import dataclass, asdict
import uuid

from .router import ModelRouter, ModelType
from models.reasoning_schemas import ReasoningChain, DiagnosticStep

logger = logging.getLogger(__name__)


@dataclass
class ConsultationRequest:
    """Structured consultation request."""

    query: str
    space_type: str = "general"
    location: str = "unknown"
    issue_type: str = "general"
    user_background: str = "general"
    supplementary_data: Optional[Dict[str, Any]] = None
    request_id: Optional[str] = None

    def __post_init__(self):
        if self.request_id is None:
            self.request_id = str(uuid.uuid4())


@dataclass
class ConsultationResponse:
    """Structured consultation response."""

    request_id: str
    status: str
    query: str
    executive_summary: str
    findings: List[Dict[str, Any]]
    recommendations: List[Dict[str, Any]]
    implementation_plan: List[Dict[str, Any]]
    expected_outcomes: List[str]
    follow_up_protocol: List[str]
    confidence_metrics: Dict[str, float]
    reasoning_chains: List[Dict[str, Any]]
    model_routing: Dict[str, Any]
    performance_metrics: Dict[str, Any]
    timestamp: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary."""
        return asdict(self)

    def to_json(self) -> str:
        """Convert response to JSON."""
        return json.dumps(self.to_dict(), indent=2, default=str)


class ConsultationOrchestrator:
    """
    Orchestrates multi-model consultation flow.

    Coordinates:
    1. Intent detection (routing)
    2. Geometric validation
    3. Cross-system synthesis
    4. Structured output generation
    5. Result aggregation and confidence scoring
    """

    def __init__(self, api_key: str, enable_caching: bool = True):
        """
        Initialize orchestrator.

        Args:
            api_key: Anthropic API key
            enable_caching: Enable prompt caching for repeated queries
        """
        self.router = ModelRouter(api_key=api_key)
        self.enable_caching = enable_caching
        self.consultation_history: List[ConsultationResponse] = []
        self.performance_logs: List[Dict[str, Any]] = []

    async def process_consultation(self, request: ConsultationRequest) -> ConsultationResponse:
        """
        Process a full consultation through the multi-model pipeline.

        Pipeline:
        1. Intent Detection -> Route to specialist models
        2. Geometric Validation -> Validate spatial aspects
        3. Cross-System Synthesis -> Integrate supplementary data
        4. Structured Output -> Generate final response
        5. Aggregate Results -> Combine all findings
        """
        logger.info(f"Processing consultation {request.request_id}: {request.query[:100]}")

        start_time = datetime.now()
        performance_metrics = {}

        try:
            # ================================================================
            # STEP 1: INTENT DETECTION & ROUTING
            # ================================================================
            logger.info(f"[{request.request_id}] Step 1: Intent Detection")

            intent_start = datetime.now()
            intent_result = await self.router.detect_intent(
                query=request.query,
                space_type=request.space_type,
                location=request.location,
                issue_type=request.issue_type,
                user_background=request.user_background,
            )
            intent_latency = (datetime.now() - intent_start).total_seconds() * 1000
            performance_metrics["intent_detection_ms"] = intent_latency

            intent_data = intent_result.get("intent", {})
            logger.info(
                f"[{request.request_id}] Intent: {intent_data.get('query_type')} | "
                f"Depth: {intent_data.get('reasoning_depth')} | "
                f"Confidence: {intent_data.get('confidence')}"
            )

            # ================================================================
            # STEP 2: GEOMETRIC VALIDATION
            # ================================================================
            logger.info(f"[{request.request_id}] Step 2: Geometric Validation")

            space_details = {
                "type": request.space_type,
                "location": request.location,
                "issue": request.issue_type,
                "user_background": request.user_background,
            }

            # Build directional context from intent
            directional_context = {
                "primary_focus": intent_data.get("spatial_focus", "space"),
                "requires_geometric_validation": intent_data.get("reasoning_depth") in [
                    "moderate",
                    "complex",
                ],
            }

            geometric_start = datetime.now()
            geometric_result = await self.router.validate_geometric_aspects(
                space_details=space_details,
                current_analysis={
                    "query": request.query,
                    "intent": intent_data,
                },
                directional_context=directional_context,
            )
            geometric_latency = (datetime.now() - geometric_start).total_seconds() * 1000
            performance_metrics["geometric_validation_ms"] = geometric_latency

            geometric_data = geometric_result.get("validation", {})
            logger.info(
                f"[{request.request_id}] Geometric Score: "
                f"{geometric_data.get('geometric_harmony_score', 'N/A')}/100"
            )

            # ================================================================
            # STEP 3: CROSS-SYSTEM SYNTHESIS
            # ================================================================
            logger.info(f"[{request.request_id}] Step 3: Cross-System Synthesis")

            synthesis_start = datetime.now()
            synthesis_result = await self.router.synthesize_cross_systems(
                vastu_analysis={
                    "findings": geometric_data.get("geometric_issues", []),
                    "recommendations": geometric_data.get("geometric_adjustments", []),
                },
                supplementary_data=request.supplementary_data or {},
                reasoning_context={
                    "intent": intent_data,
                    "primary_focus": directional_context["primary_focus"],
                },
            )
            synthesis_latency = (datetime.now() - synthesis_start).total_seconds() * 1000
            performance_metrics["synthesis_ms"] = synthesis_latency

            synthesis_data = synthesis_result.get("synthesis", {})
            logger.info(
                f"[{request.request_id}] Integration Confidence: "
                f"{synthesis_data.get('integration_confidence', 'N/A')}"
            )

            # ================================================================
            # STEP 4: STRUCTURED OUTPUT GENERATION
            # ================================================================
            logger.info(f"[{request.request_id}] Step 4: Output Generation")

            schema_requirements = {
                "require_executive_summary": True,
                "require_findings": True,
                "require_recommendations": True,
                "require_implementation": True,
                "require_outcomes": True,
                "require_confidence": True,
                "include_references": True,
            }

            output_start = datetime.now()
            output_result = await self.router.generate_structured_output(
                analysis_results={
                    "geometric_data": geometric_data,
                    "query": request.query,
                    "issue_type": request.issue_type,
                },
                geometric_results=geometric_data,
                synthesis_results=synthesis_data,
                schema_requirements=schema_requirements,
            )
            output_latency = (datetime.now() - output_start).total_seconds() * 1000
            performance_metrics["output_generation_ms"] = output_latency

            output_data = output_result.get("output", {})

            # ================================================================
            # STEP 5: AGGREGATE RESULTS & CALCULATE CONFIDENCE
            # ================================================================
            logger.info(f"[{request.request_id}] Step 5: Aggregating Results")

            total_latency = (datetime.now() - start_time).total_seconds() * 1000
            performance_metrics["total_latency_ms"] = total_latency

            # Calculate overall confidence
            confidence_scores = self._calculate_confidence_scores(
                intent_confidence=intent_data.get("confidence", 0.5),
                geometric_confidence=geometric_data.get("confidence_scores", {}).get(
                    "overall", 0.5
                ),
                synthesis_confidence=synthesis_data.get("integration_confidence", 0.5),
                output_confidence=output_data.get("confidence_metrics", {}).get("overall", 0.7),
            )

            # Create reasoning chain
            reasoning_chain = self._create_reasoning_chain(
                request=request,
                intent_data=intent_data,
                geometric_data=geometric_data,
                synthesis_data=synthesis_data,
                confidence_scores=confidence_scores,
            )

            # ================================================================
            # BUILD RESPONSE
            # ================================================================
            response = ConsultationResponse(
                request_id=request.request_id,
                status="success",
                query=request.query,
                executive_summary=output_data.get("executive_summary", ""),
                findings=output_data.get("findings", []),
                recommendations=output_data.get("recommendations", []),
                implementation_plan=output_data.get("implementation_plan", []),
                expected_outcomes=output_data.get("expected_outcomes", []),
                follow_up_protocol=output_data.get("follow_up_protocol", []),
                confidence_metrics=confidence_scores,
                reasoning_chains=[
                    {
                        "reasoning_id": reasoning_chain.reasoning_id,
                        "query": reasoning_chain.query,
                        "hypothesis": reasoning_chain.hypothesis,
                        "conclusion": reasoning_chain.conclusion,
                        "confidence_score": reasoning_chain.confidence_score,
                        "recommendations": reasoning_chain.recommendations,
                    }
                ],
                model_routing={
                    "intent_model": intent_result.get("model_used"),
                    "geometric_model": geometric_result.get("model_used"),
                    "synthesis_model": synthesis_result.get("model_used"),
                    "output_model": output_result.get("model_used"),
                    "routing_decision": intent_data.get("query_type"),
                    "reasoning_depth": intent_data.get("reasoning_depth"),
                },
                performance_metrics=performance_metrics,
                timestamp=datetime.now().isoformat(),
            )

            # Log performance
            self._log_performance(request.request_id, response, performance_metrics)

            # Store in history
            self.consultation_history.append(response)

            logger.info(
                f"[{request.request_id}] Consultation complete | "
                f"Status: {response.status} | "
                f"Confidence: {confidence_scores['overall']:.2f} | "
                f"Latency: {total_latency:.0f}ms"
            )

            return response

        except Exception as e:
            logger.error(f"[{request.request_id}] Consultation failed: {e}", exc_info=True)

            # Return error response
            return ConsultationResponse(
                request_id=request.request_id,
                status="error",
                query=request.query,
                executive_summary=f"Consultation failed: {str(e)}",
                findings=[],
                recommendations=[],
                implementation_plan=[],
                expected_outcomes=[],
                follow_up_protocol=[],
                confidence_metrics={"overall": 0.0},
                reasoning_chains=[],
                model_routing={"error": str(e)},
                performance_metrics=performance_metrics,
                timestamp=datetime.now().isoformat(),
            )

    async def process_batch_consultations(
        self, requests: List[ConsultationRequest], max_concurrent: int = 3
    ) -> List[ConsultationResponse]:
        """
        Process multiple consultations concurrently with rate limiting.

        Args:
            requests: List of consultation requests
            max_concurrent: Maximum concurrent requests

        Returns:
            List of consultation responses
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def limited_process(req: ConsultationRequest) -> ConsultationResponse:
            async with semaphore:
                return await self.process_consultation(req)

        logger.info(f"Processing batch of {len(requests)} consultations")
        responses = await asyncio.gather(
            *[limited_process(req) for req in requests], return_exceptions=False
        )

        return responses

    def get_model_health_status(self) -> Dict[str, Any]:
        """Get health status of all models."""
        return self.router.get_model_health_status()

    def get_consultation_history(self, limit: int = 10) -> List[ConsultationResponse]:
        """Get recent consultation history."""
        return self.consultation_history[-limit:]

    # ========================================================================
    # PRIVATE HELPER METHODS
    # ========================================================================

    def _calculate_confidence_scores(
        self,
        intent_confidence: float,
        geometric_confidence: float,
        synthesis_confidence: float,
        output_confidence: float,
    ) -> Dict[str, float]:
        """Calculate aggregated confidence scores."""
        scores = {
            "intent_detection": intent_confidence,
            "geometric_validation": geometric_confidence,
            "cross_system_synthesis": synthesis_confidence,
            "output_generation": output_confidence,
        }

        # Weighted average (output generation is most critical)
        weights = {
            "intent_detection": 0.2,
            "geometric_validation": 0.3,
            "cross_system_synthesis": 0.2,
            "output_generation": 0.3,
        }

        overall = sum(scores[k] * weights[k] for k in scores)
        scores["overall"] = overall

        return scores

    def _create_reasoning_chain(
        self,
        request: ConsultationRequest,
        intent_data: Dict[str, Any],
        geometric_data: Dict[str, Any],
        synthesis_data: Dict[str, Any],
        confidence_scores: Dict[str, float],
    ) -> ReasoningChain:
        """Create a structured reasoning chain from analysis results."""
        steps = [
            DiagnosticStep(
                step_number=1,
                description="Intent Detection and Routing",
                findings=[
                    f"Query Type: {intent_data.get('query_type', 'unknown')}",
                    f"Reasoning Depth: {intent_data.get('reasoning_depth', 'moderate')}",
                    f"Primary Focus: {intent_data.get('spatial_focus', 'space')}",
                ],
                evidence_used=[intent_data.get("routing_rationale", "")],
                confidence=intent_data.get("confidence", 0.5),
                next_steps=intent_data.get("required_models", []),
            ),
            DiagnosticStep(
                step_number=2,
                description="Geometric Validation",
                findings=geometric_data.get("geometric_issues", []),
                evidence_used=geometric_data.get("geometric_remedies", []),
                confidence=geometric_data.get("confidence_scores", {}).get("overall", 0.5),
                next_steps=geometric_data.get("geometric_adjustments", []),
            ),
            DiagnosticStep(
                step_number=3,
                description="Cross-System Synthesis",
                findings=synthesis_data.get("system_integration_points", []),
                evidence_used=synthesis_data.get("enhanced_recommendations", []),
                confidence=synthesis_data.get("integration_confidence", 0.5),
                next_steps=synthesis_data.get("temporal_considerations", []),
            ),
        ]

        return ReasoningChain(
            reasoning_id=request.request_id,
            query=request.query,
            hypothesis=intent_data.get("query_type", "general analysis"),
            diagnostic_steps=steps,
            conclusion="Multi-model analysis completed with integrated recommendations",
            confidence_score=confidence_scores["overall"],
            supporting_principles=["Vastu Harmony", "Spatial Flow", "Elemental Balance"],
            contradictions=[],
            recommendations=geometric_data.get("geometric_adjustments", []),
            reasoning_quality="enhanced" if confidence_scores["overall"] > 0.75 else "moderate",
        )

    def _log_performance(
        self, request_id: str, response: ConsultationResponse, metrics: Dict[str, Any]
    ):
        """Log performance metrics."""
        log_entry = {
            "request_id": request_id,
            "timestamp": datetime.now().isoformat(),
            "status": response.status,
            "confidence": response.confidence_metrics.get("overall", 0.0),
            "metrics": metrics,
        }
        self.performance_logs.append(log_entry)

        # Log to file if metrics show performance issues
        if metrics.get("total_latency_ms", 0) > 5000:
            logger.warning(
                f"[{request_id}] High latency consultation: "
                f"{metrics.get('total_latency_ms', 0):.0f}ms"
            )
