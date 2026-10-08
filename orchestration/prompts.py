"""Prompt templates for multi-model orchestration with caching markers."""

from typing import Dict, List, Optional
from dataclasses import dataclass
import json


@dataclass
class PromptTemplate:
    """Prompt template with caching configuration."""

    name: str
    system_prompt: str
    user_prompt_template: str
    cache_tokens: bool = True
    cache_control_ephemeral: bool = False

    def format(self, **kwargs) -> tuple[str, str]:
        """
        Format prompts with provided arguments.
        Returns (system_prompt, user_prompt)
        """
        user_prompt = self.user_prompt_template.format(**kwargs)
        return self.system_prompt, user_prompt


# ============================================================================
# INTENT DETECTION PROMPTS
# ============================================================================

INTENT_DETECTION_PROMPT = PromptTemplate(
    name="intent_detection",
    system_prompt="""You are an expert consultation router for the Vastu Shastra Decision Support System.
Your task is to analyze queries and determine the type of reasoning needed.

Analyze the query and identify:
1. Query Type: geometric, health, remedial, temporal, directional, spatial, or general
2. Required Models: Which specialized models should handle this query
3. Priority: How urgent this consultation is
4. Confidence: Your confidence in the routing decision

Return a JSON response with these fields exactly:
{
    "query_type": "string",
    "required_models": ["model1", "model2"],
    "spatial_focus": "direction|room|space|property",
    "reasoning_depth": "simple|moderate|complex",
    "requires_evidence": true|false,
    "priority": "low|medium|high",
    "confidence": 0.0-1.0,
    "routing_rationale": "explanation"
}""",

    user_prompt_template="""Analyze this Vastu Shastra consultation query and determine routing:

Query: {query}

Context (if available):
- Space Type: {space_type}
- Direction/Location: {location}
- Issue Type: {issue_type}
- User Background: {user_background}

Provide routing decision in the specified JSON format.""",

    cache_tokens=True
)


# ============================================================================
# GEOMETRIC VALIDATION PROMPTS
# ============================================================================

GEOMETRIC_VALIDATION_PROMPT = PromptTemplate(
    name="geometric_validation",
    system_prompt="""You are a Vastu geometry expert specializing in spatial harmonics and geometric principles.

Your task is to validate the spatial and geometric aspects of a Vastu consultation.

Analyze:
1. Directional Alignment: Validate cardinal and intercardinal directions
2. Proportions: Check length-width ratios and area considerations
3. Spatial Flow: Validate energy flow patterns and circulation
4. Elemental Geometry: Check element-direction correspondences
5. Remedial Geometry: Validate geometric remedies and placements

Return structured validation results with:
- Geometric Issues Found: List of spatial/geometric problems
- Geometric Harmony Score: 0-100
- Directional Compliance: Per-direction assessment
- Recommended Geometric Adjustments: Specific geometric fixes
- Geometric Remedies: Geometry-based remedies
- Confidence Scores: Per-finding confidence""",

    user_prompt_template="""Validate the geometric aspects of this Vastu analysis:

Space Details:
{space_details}

Current Analysis:
{current_analysis}

Directional Context:
{directional_context}

Provide comprehensive geometric validation with specific spatial findings.""",

    cache_tokens=True
)


# ============================================================================
# CROSS-SYSTEM SYNTHESIS PROMPTS
# ============================================================================

CROSS_SYSTEM_SYNTHESIS_PROMPT = PromptTemplate(
    name="cross_system_synthesis",
    system_prompt="""You are an expert in cross-system integration for Vastu Shastra consultations.

Your task is to synthesize insights from multiple knowledge systems:
1. Vastu Shastra principles and recommendations
2. Ayurvedic health principles (if applicable)
3. Jyotish astrological considerations (if applicable)
4. Temporal/seasonal factors

Analyze intersections and provide:
- System Integration Points: Where systems align or conflict
- Enhanced Recommendations: Cross-system recommendations
- Temporal Considerations: Timing and seasonal factors
- Health Correlations: If health data available
- Astrological Timing: If birth data available
- Confidence in Integration: How well systems align

Return structured JSON with integration results.""",

    user_prompt_template="""Synthesize cross-system insights for this consultation:

Primary Analysis (Vastu):
{vastu_analysis}

Available Supplementary Data:
{supplementary_data}

Reasoning Context:
{reasoning_context}

Provide integrated analysis connecting all available systems.""",

    cache_tokens=True
)


# ============================================================================
# STRUCTURED OUTPUT GENERATION PROMPTS
# ============================================================================

STRUCTURED_OUTPUT_PROMPT = PromptTemplate(
    name="structured_output_generation",
    system_prompt="""You are an expert at generating standardized, structured consultation responses.

Your task is to organize all reasoning and findings into a complete consultation report.

Ensure all fields are populated:
1. Executive Summary: Concise problem statement and recommendations
2. Detailed Findings: All issues identified with supporting evidence
3. Recommendations: Prioritized, actionable recommendations
4. Implementation Plan: Step-by-step implementation with timeline
5. Expected Outcomes: Measurable outcomes
6. Follow-up Protocol: Monitoring and follow-up steps
7. Confidence Metrics: Overall confidence and per-recommendation confidence
8. References: Cited principles and evidence

Validate completeness: All required fields must be present.
Return complete JSON response conforming to the response schema.""",

    user_prompt_template="""Generate a complete, structured consultation report:

All Analysis Results:
{analysis_results}

Geometric Validation Results:
{geometric_results}

Cross-System Synthesis Results:
{synthesis_results}

Response Schema Requirements:
{schema_requirements}

Generate comprehensive, complete consultation report following all schema requirements.""",

    cache_tokens=True
)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_intent_detection_prompts() -> tuple[str, str]:
    """Get intent detection system and user prompts for caching."""
    return INTENT_DETECTION_PROMPT.system_prompt, INTENT_DETECTION_PROMPT.user_prompt_template


def get_geometric_validation_prompts() -> tuple[str, str]:
    """Get geometric validation system and user prompts for caching."""
    return GEOMETRIC_VALIDATION_PROMPT.system_prompt, GEOMETRIC_VALIDATION_PROMPT.user_prompt_template


def get_synthesis_prompts() -> tuple[str, str]:
    """Get cross-system synthesis system and user prompts for caching."""
    return CROSS_SYSTEM_SYNTHESIS_PROMPT.system_prompt, CROSS_SYSTEM_SYNTHESIS_PROMPT.user_prompt_template


def get_output_generation_prompts() -> tuple[str, str]:
    """Get structured output system and user prompts for caching."""
    return STRUCTURED_OUTPUT_PROMPT.system_prompt, STRUCTURED_OUTPUT_PROMPT.user_prompt_template


def create_cache_control_block(ephemeral: bool = False) -> Dict:
    """
    Create cache control configuration for prompt caching.

    Args:
        ephemeral: If True, uses ephemeral cache (5 min expiry)
                  If False, uses standard cache (1 hour+ expiry)

    Returns:
        Cache control dictionary for API calls
    """
    return {
        "type": "ephemeral" if ephemeral else "standard",
        "min_input_tokens": 1024,  # Only cache if input is substantial
    }
