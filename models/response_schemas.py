"""Response schemas for Vastu Shastra DSS."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class RecommendationItem(BaseModel):
    """A single recommendation item."""

    title: str = Field(..., description="Recommendation title")
    description: str = Field(..., description="Detailed description")
    priority: str = Field(default="medium", description="Priority level: low, medium, high, critical")
    category: str = Field(..., description="Category of recommendation")
    estimated_impact: str = Field(default="moderate", description="Expected impact")
    implementation_effort: str = Field(default="medium", description="Implementation effort level")
    related_principles: List[str] = Field(default_factory=list, description="Related Vastu principles")


class SpaceAnalysis(BaseModel):
    """Analysis of a space."""

    space_name: str = Field(..., description="Name of the space")
    space_type: str = Field(..., description="Type of space (bedroom, kitchen, etc.)")
    direction: str = Field(..., description="Primary direction")
    compliance_score: float = Field(..., ge=0, le=100, description="Vastu compliance score")
    key_issues: List[str] = Field(default_factory=list, description="Key identified issues")
    critical_defects: List[str] = Field(default_factory=list, description="Critical defects found")
    recommendations: List[RecommendationItem] = Field(default_factory=list, description="Recommendations")
    suggested_color: Optional[str] = Field(default=None, description="Suggested auspicious color")
    element_association: Optional[str] = Field(default=None, description="Associated element")


class ConsultationRequest(BaseModel):
    """Consultation request schema."""

    space_name: str = Field(..., description="Name of the space being analyzed")
    space_type: str = Field(..., description="Type of space")
    primary_direction: str = Field(..., description="Primary facing direction")
    area_sqft: Optional[float] = Field(default=None, description="Area in square feet")
    purpose: str = Field(..., description="Primary purpose of the space")
    features: List[str] = Field(default_factory=list, description="Space features")
    perceived_issues: List[str] = Field(default_factory=list, description="Issues the client perceives")
    existing_defects: List[str] = Field(default_factory=list, description="Known Vastu defects")
    budget_constraint: Optional[str] = Field(default=None, description="Budget for improvements")
    timeline: Optional[str] = Field(default=None, description="Timeline for implementation")


class ConsultationResponse(BaseModel):
    """Consultation response schema."""

    consultation_id: str = Field(..., description="Unique consultation ID")
    timestamp: str = Field(..., description="Timestamp of consultation")
    space_analysis: SpaceAnalysis = Field(..., description="Space analysis results")
    overall_compliance_score: float = Field(..., ge=0, le=100, description="Overall compliance score")
    summary: str = Field(..., description="Summary of findings")
    recommendations: List[RecommendationItem] = Field(..., description="Recommended actions")
    implementation_plan: Optional[str] = Field(default=None, description="Step-by-step implementation plan")
    expected_benefits: List[str] = Field(default_factory=list, description="Expected benefits")
    success_indicators: List[str] = Field(default_factory=list, description="How to measure success")
    follow_up_suggestions: List[str] = Field(default_factory=list, description="Suggestions for follow-up")


class AnalysisReport(BaseModel):
    """Comprehensive analysis report."""

    report_id: str = Field(..., description="Unique report ID")
    report_title: str = Field(..., description="Report title")
    analysis_date: str = Field(..., description="Date of analysis")
    analyzed_spaces: List[SpaceAnalysis] = Field(..., description="Analyzed spaces")
    overall_assessment: str = Field(..., description="Overall assessment")
    compliance_score: float = Field(..., ge=0, le=100, description="Overall compliance score")
    top_priorities: List[RecommendationItem] = Field(..., description="Top priority recommendations")
    all_recommendations: List[RecommendationItem] = Field(..., description="All recommendations")
    implementation_roadmap: List[Dict[str, Any]] = Field(
        default_factory=list, description="Phased implementation roadmap"
    )
    budget_summary: Optional[Dict[str, Any]] = Field(default=None, description="Budget summary")
    estimated_timeline: Optional[str] = Field(default=None, description="Estimated timeline")
    expected_outcomes: List[str] = Field(default_factory=list, description="Expected outcomes")


class DiagnosticContext(BaseModel):
    """Context for diagnostic reasoning."""

    query: str = Field(..., description="Original query or problem")
    context_type: str = Field(..., description="Type of context")
    retrieved_evidence: List[Dict[str, Any]] = Field(
        default_factory=list, description="Retrieved evidence"
    )
    known_principles: List[str] = Field(default_factory=list, description="Relevant principles")
    applicable_remedies: List[str] = Field(default_factory=list, description="Applicable remedies")


class HealthCheckResponse(BaseModel):
    """Health check response."""

    status: str = Field(..., description="Status of the system")
    timestamp: str = Field(..., description="Timestamp of check")
    components: Dict[str, str] = Field(default_factory=dict, description="Status of components")
    message: Optional[str] = Field(default=None, description="Additional message")


class ErrorResponse(BaseModel):
    """Error response schema."""

    error: str = Field(..., description="Error message")
    error_code: str = Field(..., description="Error code")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Additional error details")
    timestamp: str = Field(..., description="Timestamp of error")
