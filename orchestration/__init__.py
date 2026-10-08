"""Multi-model orchestration layer for reasoning."""

from .router import ModelRouter, ModelType, ModelHealth
from .orchestrator import ConsultationOrchestrator, ConsultationRequest, ConsultationResponse
from .prompts import (
    INTENT_DETECTION_PROMPT,
    GEOMETRIC_VALIDATION_PROMPT,
    CROSS_SYSTEM_SYNTHESIS_PROMPT,
    STRUCTURED_OUTPUT_PROMPT,
    PromptTemplate,
    create_cache_control_block,
)

__all__ = [
    "ModelRouter",
    "ModelType",
    "ModelHealth",
    "ConsultationOrchestrator",
    "ConsultationRequest",
    "ConsultationResponse",
    "INTENT_DETECTION_PROMPT",
    "GEOMETRIC_VALIDATION_PROMPT",
    "CROSS_SYSTEM_SYNTHESIS_PROMPT",
    "STRUCTURED_OUTPUT_PROMPT",
    "PromptTemplate",
    "create_cache_control_block",
]
