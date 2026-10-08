"""Reasoning and diagnostic schemas."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class DiagnosticStep(BaseModel):
    """A step in the diagnostic process."""

    step_number: int = Field(..., description="Step number in the process")
    description: str = Field(..., description="Description of this step")
    findings: List[str] = Field(..., description="Findings from this step")
    evidence_used: List[str] = Field(default_factory=list, description="Evidence used")
    confidence: float = Field(default=0.5, ge=0, le=1, description="Confidence level")
    next_steps: List[str] = Field(default_factory=list, description="Next steps")


class ReasoningChain(BaseModel):
    """Chain of reasoning for a diagnosis."""

    reasoning_id: str = Field(..., description="Unique reasoning chain ID")
    query: str = Field(..., description="Original query")
    hypothesis: str = Field(..., description="Working hypothesis")
    diagnostic_steps: List[DiagnosticStep] = Field(..., description="Sequence of diagnostic steps")
    conclusion: str = Field(..., description="Final conclusion")
    confidence_score: float = Field(..., ge=0, le=1, description="Overall confidence")
    supporting_principles: List[str] = Field(default_factory=list, description="Supporting Vastu principles")
    contradictions: List[str] = Field(default_factory=list, description="Any contradictions found")
    recommendations: List[str] = Field(default_factory=list, description="Recommended actions")
    reasoning_quality: str = Field(default="moderate", description="Quality of reasoning")


class EvidenceEvaluation(BaseModel):
    """Evaluation of evidence for relevance and quality."""

    evidence_id: str = Field(..., description="ID of the evidence")
    content_snippet: str = Field(..., description="Snippet of the evidence")
    relevance_score: float = Field(..., ge=0, le=1, description="Relevance to query")
    quality_score: float = Field(..., ge=0, le=1, description="Quality of evidence")
    reliability: str = Field(..., description="Reliability assessment")
    source: str = Field(..., description="Source of evidence")
    applicable_to_case: bool = Field(..., description="Whether applicable to this case")
    supporting_reasoning: str = Field(..., description="Why this evidence is relevant")


class PrincipleApplication(BaseModel):
    """Application of a Vastu principle to a specific case."""

    principle_name: str = Field(..., description="Name of the principle")
    description: str = Field(..., description="Description of the principle")
    relevance_to_case: str = Field(..., description="How it applies to this case")
    supporting_evidence: List[str] = Field(default_factory=list, description="Supporting evidence")
    implementation: str = Field(..., description="How to implement this principle")
    expected_outcome: str = Field(..., description="Expected outcome if implemented")
    potential_challenges: List[str] = Field(default_factory=list, description="Potential challenges")


class RemediationStrategy(BaseModel):
    """Strategy for remediation of a Vastu defect."""

    defect_identified: str = Field(..., description="Identified defect")
    severity: str = Field(..., description="Severity level")
    root_causes: List[str] = Field(..., description="Root causes")
    remediation_options: List[Dict[str, Any]] = Field(..., description="Available remediation options")
    recommended_approach: str = Field(..., description="Recommended approach")
    implementation_steps: List[str] = Field(..., description="Step-by-step implementation")
    timeline: str = Field(..., description="Estimated timeline")
    cost_estimate: Optional[str] = Field(default=None, description="Cost estimate")
    success_criteria: List[str] = Field(..., description="Criteria for success")
    follow_up_monitoring: List[str] = Field(..., description="Follow-up monitoring steps")


class IntegratedAnalysis(BaseModel):
    """Integrated analysis combining multiple components."""

    analysis_id: str = Field(..., description="Unique analysis ID")
    input_query: str = Field(..., description="Input query")
    reasoning_chains: List[ReasoningChain] = Field(..., description="Reasoning chains")
    evidence_evaluations: List[EvidenceEvaluation] = Field(
        ..., description="Evaluated evidence items"
    )
    principle_applications: List[PrincipleApplication] = Field(
        ..., description="Applied principles"
    )
    remediation_strategies: List[RemediationStrategy] = Field(
        ..., description="Remediation strategies"
    )
    final_recommendation: str = Field(..., description="Final recommendation")
    confidence_level: float = Field(..., ge=0, le=1, description="Overall confidence level")
    reasoning_explanation: str = Field(..., description="Explanation of the reasoning")


class ClaudeResponse(BaseModel):
    """Wrapper for Claude AI response."""

    response_id: str = Field(..., description="Unique response ID")
    query: str = Field(..., description="Original query")
    response_text: str = Field(..., description="Claude's response")
    reasoning_used: Optional[str] = Field(default=None, description="Reasoning approach used")
    evidence_cited: List[str] = Field(default_factory=list, description="Evidence cited")
    principles_referenced: List[str] = Field(
        default_factory=list, description="Vastu principles referenced"
    )
    recommendations: List[str] = Field(default_factory=list, description="Recommendations made")
    confidence: float = Field(default=0.7, ge=0, le=1, description="Confidence in response")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
