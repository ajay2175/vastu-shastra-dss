"""API request/response schemas."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class DirectionConsultationRequest(BaseModel):
    """Request for direction-specific consultation."""

    direction: str = Field(..., description="Direction to consult about")


class DirectionConsultationResponse(BaseModel):
    """Response for direction consultation."""

    direction: str = Field(..., description="Direction consulted")
    principle_name: str = Field(..., description="Associated principle")
    description: str = Field(..., description="Principle description")
    key_points: List[str] = Field(..., description="Key points")
    elements: List[str] = Field(..., description="Associated elements")
    colors: List[str] = Field(..., description="Recommended colors")
    remedies: List[str] = Field(..., description="Available remedies")


class RoomConsultationRequest(BaseModel):
    """Request for room-specific consultation."""

    room_type: str = Field(..., description="Type of room")


class RoomConsultationResponse(BaseModel):
    """Response for room consultation."""

    room_type: str = Field(..., description="Room type")
    best_directions: List[str] = Field(..., description="Best directions for this room")
    directions_to_avoid: List[str] = Field(..., description="Directions to avoid")
    ideal_shape: str = Field(..., description="Ideal shape")
    window_placement: str = Field(..., description="Window placement guidelines")
    recommended_color: str = Field(..., description="Recommended color")
    furniture_guidelines: str = Field(..., description="Furniture guidelines")


class DefectDiagnosisRequest(BaseModel):
    """Request for defect diagnosis."""

    defect_type: str = Field(..., description="Type of defect")


class DefectDiagnosisResponse(BaseModel):
    """Response for defect diagnosis."""

    defect: str = Field(..., description="Defect identified")
    problem: str = Field(..., description="Problem description")
    impact: str = Field(..., description="Impact of the defect")
    severity: str = Field(..., description="Severity level")
    remedies: List[str] = Field(..., description="Available remedies")
    detailed_remedies: List[Dict[str, str]] = Field(..., description="Detailed remedy information")


class SpaceAnalysisRequest(BaseModel):
    """Request for space analysis."""

    space_name: str = Field(..., description="Name of the space")
    space_type: str = Field(..., description="Type of space")
    direction: str = Field(..., description="Primary direction")
    area_sqft: Optional[float] = Field(default=None, description="Area in square feet")
    features: List[str] = Field(default_factory=list, description="Space features")
    issues: List[str] = Field(default_factory=list, description="Perceived issues")
    purpose: str = Field(..., description="Purpose of the space")


class SpaceAnalysisResponse(BaseModel):
    """Response for space analysis."""

    space_name: str = Field(..., description="Analyzed space")
    compliance_score: float = Field(..., description="Compliance score")
    issues: List[str] = Field(..., description="Identified issues")
    recommendations: List[str] = Field(..., description="Recommendations")
    suggested_color: str = Field(..., description="Suggested color")
    element_association: Optional[str] = Field(default=None, description="Associated element")
    remedies: List[str] = Field(..., description="Available remedies")


class BatchSpaceAnalysisRequest(BaseModel):
    """Request for batch space analysis."""

    spaces: List[SpaceAnalysisRequest] = Field(..., description="List of spaces to analyze")


class BatchSpaceAnalysisResponse(BaseModel):
    """Response for batch analysis."""

    analyses: List[SpaceAnalysisResponse] = Field(..., description="Analysis results")
    overall_score: float = Field(..., description="Overall compliance score")
    summary: str = Field(..., description="Summary of findings")


class HealthCheckResponse(BaseModel):
    """Health check response."""

    status: str = Field(..., description="System status")
    components: Dict[str, str] = Field(..., description="Component statuses")
    timestamp: str = Field(..., description="Timestamp of check")
    message: Optional[str] = Field(default=None, description="Additional message")


class ErrorResponse(BaseModel):
    """Error response."""

    error: str = Field(..., description="Error message")
    error_code: str = Field(..., description="Error code")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Error details")
    timestamp: str = Field(..., description="Timestamp of error")
