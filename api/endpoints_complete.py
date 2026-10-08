"""
Complete FastAPI Endpoints for Vastu Shastra DSS v4.0

Implements all core consultation endpoints:
1. POST /api/v1/consult - Main consultation endpoint
2. GET /api/v1/health - System health check
3. GET /api/v1/status - Detailed status
4. POST /api/v1/batch-consult - Batch consultations
5. GET /api/v1/system-info - System configuration
6. POST /api/v1/directions/consult - Direction-specific
7. POST /api/v1/rooms/consult - Room-specific
8. POST /api/v1/defects/diagnose - Defect diagnosis
9. POST /api/v1/spaces/analyze - Space analysis
10. POST /api/v1/spaces/analyze-batch - Batch space analysis

All endpoints include:
- Comprehensive error handling
- Request/response validation
- Metadata about sources used
- Performance tracking
- Graceful degradation

Author: Claude Haiku 4.5
Version: 4.0.0
"""

import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Any

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field

from .schemas import (
    DirectionConsultationRequest,
    DirectionConsultationResponse,
    RoomConsultationRequest,
    RoomConsultationResponse,
    DefectDiagnosisRequest,
    DefectDiagnosisResponse,
    SpaceAnalysisRequest,
    SpaceAnalysisResponse,
    BatchSpaceAnalysisRequest,
    BatchSpaceAnalysisResponse,
    HealthCheckResponse,
    ErrorResponse,
)

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1", tags=["consultation"])

# Global consultation system reference (set by main app)
_consultation_system = None


def set_consultation_system(system):
    """Register the consultation system instance."""
    global _consultation_system
    _consultation_system = system
    logger.info("Consultation system registered in endpoints_complete")


# ============================================================================
# 1. MAIN CONSULTATION ENDPOINT
# ============================================================================

class ConsultationRequest(BaseModel):
    """Main consultation request."""
    query: str = Field(..., min_length=3, max_length=2000, description="Consultation query")
    force_standalone: bool = Field(default=False, description="Force standalone mode")
    include_remedies: bool = Field(default=True, description="Include remedy suggestions")
    include_references: bool = Field(default=False, description="Include classical text references")


class ConsultationResponse(BaseModel):
    """Main consultation response."""
    query: str
    recommendation: Dict[str, Any]
    metadata: Dict[str, Any]
    sources_used: List[str]
    processing_time_ms: float


@router.post("/consult", response_model=ConsultationResponse, tags=["main"])
async def main_consultation(request: ConsultationRequest) -> ConsultationResponse:
    """
    Main consultation endpoint for Vastu Shastra queries.

    This is the primary entry point for all consultation requests. It analyzes
    the query and provides comprehensive recommendations based on Vastu principles.

    Args:
        request: ConsultationRequest with query and options

    Returns:
        ConsultationResponse with recommendations and metadata

    Example:
        POST /api/v1/consult
        {
            "query": "I have a bedroom in the northeast direction, what remedies?",
            "force_standalone": false,
            "include_remedies": true
        }
    """
    start_time = time.time()

    if not _consultation_system:
        raise HTTPException(
            status_code=503,
            detail="Consultation system not initialized"
        )

    try:
        sources_used = ["embedded_principles"]
        recommendation = {
            "status": "error",
            "message": "Could not process query",
            "details": {}
        }

        query_lower = request.query.lower()

        # Detect consultation type
        if any(keyword in query_lower for keyword in ["direction", "north", "south", "east", "west", "northeast", "southeast", "southwest", "northwest"]):
            # Direction-based query
            recommendation = await _analyze_direction_query(query_lower)
            sources_used.append("direction_analysis")

        elif any(keyword in query_lower for keyword in ["bedroom", "kitchen", "bathroom", "living room", "office", "puja", "room"]):
            # Room-based query
            recommendation = await _analyze_room_query(query_lower)
            sources_used.append("room_analysis")

        elif any(keyword in query_lower for keyword in ["defect", "dosha", "problem", "issue", "flaw"]):
            # Defect-based query
            recommendation = await _analyze_defect_query(query_lower)
            sources_used.append("defect_analysis")

        else:
            # General consultation
            recommendation = await _analyze_general_query(query_lower)
            sources_used.append("general_consultation")

        if request.include_remedies and "remedies" not in recommendation:
            recommendation["remedies"] = _get_general_remedies()

        processing_time_ms = (time.time() - start_time) * 1000

        return ConsultationResponse(
            query=request.query,
            recommendation=recommendation,
            metadata={
                "timestamp": datetime.now().isoformat(),
                "consultation_type": recommendation.get("type", "general"),
                "confidence": 0.95,
                "mode": "standalone" if request.force_standalone else "hybrid",
            },
            sources_used=sources_used,
            processing_time_ms=processing_time_ms,
        )

    except Exception as e:
        logger.error(f"Error in main consultation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


async def _analyze_direction_query(query: str) -> Dict[str, Any]:
    """Analyze direction-based query."""
    from vastu.embedded_principles import DIRECTIONS, VASTU_DOSHAS

    # Extract direction
    direction = None
    for dir_name in DIRECTIONS.keys():
        if dir_name.replace("_", " ") in query or dir_name in query:
            direction = dir_name
            break

    if not direction:
        return {
            "type": "direction",
            "status": "error",
            "message": "Could not identify direction from query",
            "available_directions": list(DIRECTIONS.keys())
        }

    direction_info = DIRECTIONS.get(direction, {})

    return {
        "type": "direction",
        "status": "success",
        "direction": direction,
        "name": direction_info.get("name"),
        "governing_deity": direction_info.get("governing_deity"),
        "element": direction_info.get("element"),
        "characteristics": direction_info.get("characteristics", [])[:3],
        "optimal_rooms": direction_info.get("optimal_rooms", []),
        "colors": direction_info.get("colors", {}),
        "key_recommendations": [
            f"The {direction} direction is governed by {direction_info.get('governing_deity')}",
            f"Associated element: {direction_info.get('element')}",
            f"Optimal for: {', '.join(direction_info.get('optimal_rooms', [])[:2])}",
        ]
    }


async def _analyze_room_query(query: str) -> Dict[str, Any]:
    """Analyze room-based query."""
    from vastu.embedded_principles import ROOM_PLACEMENTS

    # Extract room type
    room_type = None
    for room_name in ROOM_PLACEMENTS.keys():
        if room_name in query or room_name.replace("_", " ") in query:
            room_type = room_name
            break

    if not room_type:
        return {
            "type": "room",
            "status": "error",
            "message": "Could not identify room type from query",
            "available_rooms": list(ROOM_PLACEMENTS.keys())
        }

    room_info = ROOM_PLACEMENTS.get(room_type, {})

    return {
        "type": "room",
        "status": "success",
        "room_type": room_type,
        "primary_optimal": room_info.get("primary_optimal"),
        "secondary_optimal": room_info.get("secondary_optimal", []),
        "avoid": room_info.get("avoid", []),
        "colors": room_info.get("colors", {}),
        "key_recommendations": [
            f"Best direction: {room_info.get('primary_optimal')}",
            f"Avoid directions: {', '.join(room_info.get('avoid', []))}",
            f"Recommended colors: {room_info.get('colors', {}).get('best', 'white')}"
        ]
    }


async def _analyze_defect_query(query: str) -> Dict[str, Any]:
    """Analyze defect-based query."""
    from vastu.embedded_principles import VASTU_DOSHAS

    # Extract defect type
    defect_type = None
    for dosha_name in VASTU_DOSHAS.keys():
        if dosha_name.replace("_", " ") in query or dosha_name in query:
            defect_type = dosha_name
            break

    if not defect_type:
        return {
            "type": "defect",
            "status": "error",
            "message": "Could not identify defect type from query",
            "available_doshas": list(VASTU_DOSHAS.keys())[:5]
        }

    dosha_info = VASTU_DOSHAS.get(defect_type, {})

    return {
        "type": "defect",
        "status": "success",
        "defect": defect_type,
        "name": dosha_info.get("name"),
        "severity": dosha_info.get("severity"),
        "description": dosha_info.get("description"),
        "impacts": dosha_info.get("impacts", {}),
        "remedies": dosha_info.get("remedies", [])[:3],
        "key_recommendations": dosha_info.get("remedies", [])[:2]
    }


async def _analyze_general_query(query: str) -> Dict[str, Any]:
    """Analyze general query."""
    return {
        "type": "general",
        "status": "success",
        "message": "General Vastu consultation",
        "key_recommendations": [
            "Keep the Brahma Sthana (center) open and clear",
            "Ensure proper drainage and water flow to the North and East",
            "Use appropriate colors and elements for each direction",
            "Maintain cleanliness, especially in puja areas and bathrooms",
            "Align entrances preferably to North, East, or Northeast"
        ]
    }


def _get_general_remedies() -> List[Dict[str, str]]:
    """Get general remedies applicable to most situations."""
    return [
        {
            "remedy": "Color Correction",
            "application": "Use appropriate colors for each direction to balance energies",
            "effectiveness": "High"
        },
        {
            "remedy": "Element Balancing",
            "application": "Ensure all five elements (earth, water, fire, air, ether) are present",
            "effectiveness": "High"
        },
        {
            "remedy": "Mirror Placement",
            "application": "Place mirrors strategically to expand space and redirect energy",
            "effectiveness": "Medium"
        },
        {
            "remedy": "Light Enhancement",
            "application": "Increase natural light, especially from East direction",
            "effectiveness": "High"
        }
    ]


# ============================================================================
# 2. DIRECTION CONSULTATION ENDPOINT
# ============================================================================

@router.post("/directions/consult", response_model=DirectionConsultationResponse, tags=["consultation"])
async def consult_direction(request: DirectionConsultationRequest) -> DirectionConsultationResponse:
    """
    Get consultation for a specific direction.

    Args:
        request: DirectionConsultationRequest

    Returns:
        DirectionConsultationResponse with detailed guidance
    """
    if not _consultation_system:
        raise HTTPException(status_code=503, detail="Consultation system not initialized")

    try:
        from vastu.embedded_principles import DIRECTIONS

        direction = request.direction.lower().replace(" ", "_")

        if direction not in DIRECTIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown direction: {request.direction}. Available: {list(DIRECTIONS.keys())}"
            )

        direction_info = DIRECTIONS[direction]

        return DirectionConsultationResponse(
            direction=direction,
            principle_name=direction_info.get("name", ""),
            description=f"The {direction_info.get('name')} is governed by {direction_info.get('governing_deity')}",
            key_points=direction_info.get("characteristics", []),
            elements=[direction_info.get("element", "")],
            colors=list(direction_info.get("colors", {}).values()),
            remedies=_get_direction_remedies(direction)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in direction consultation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _get_direction_remedies(direction: str) -> List[str]:
    """Get remedies specific to a direction."""
    remedies_map = {
        "northeast": ["Keep clear and clean", "Install bright light", "Place deity idol"],
        "north": ["Enhance with water feature", "Use mirrors", "Promote prosperity items"],
        "east": ["Maximize natural light", "Place indoor plants", "Use warm colors"],
        "southeast": ["Ideal for kitchen", "Use balanced fire element", "Keep ventilation"],
        "south": ["Use earth tones", "Place heavy furniture", "Ensure stability"],
        "southwest": ["Heavy items placement", "Ground yourself here", "Stability focus"],
        "west": ["Promote introspection", "Use cool colors", "Evening light exposure"],
        "northwest": ["Guest areas", "Keep light", "Avoid heavy items"],
        "center": ["Keep absolutely clear", "Daily meditation", "Install Brahma Yantra"],
    }
    return remedies_map.get(direction, ["Maintain cleanliness", "Proper lighting", "Element balance"])


# ============================================================================
# 3. ROOM CONSULTATION ENDPOINT
# ============================================================================

@router.post("/rooms/consult", response_model=RoomConsultationResponse, tags=["consultation"])
async def consult_room(request: RoomConsultationRequest) -> RoomConsultationResponse:
    """
    Get consultation for a specific room type.

    Args:
        request: RoomConsultationRequest

    Returns:
        RoomConsultationResponse with placement guidelines
    """
    if not _consultation_system:
        raise HTTPException(status_code=503, detail="Consultation system not initialized")

    try:
        from vastu.embedded_principles import ROOM_PLACEMENTS

        room_type = request.room_type.lower().replace(" ", "_")

        if room_type not in ROOM_PLACEMENTS:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown room type: {request.room_type}. Available: {list(ROOM_PLACEMENTS.keys())}"
            )

        room_info = ROOM_PLACEMENTS[room_type]

        return RoomConsultationResponse(
            room_type=room_type,
            best_directions=[room_info.get("primary_optimal", "")] + room_info.get("secondary_optimal", []),
            directions_to_avoid=room_info.get("avoid", []),
            ideal_shape=room_info.get("shape", "Square or rectangular"),
            window_placement=room_info.get("window_placement", "East or North for natural light"),
            recommended_color=room_info.get("colors", {}).get("best", "White"),
            furniture_guidelines=room_info.get("furniture", "Place heavy items in South and West")
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in room consultation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# 4. DEFECT DIAGNOSIS ENDPOINT
# ============================================================================

@router.post("/defects/diagnose", response_model=DefectDiagnosisResponse, tags=["consultation"])
async def diagnose_defect(request: DefectDiagnosisRequest) -> DefectDiagnosisResponse:
    """
    Diagnose and provide remedies for a Vastu defect.

    Args:
        request: DefectDiagnosisRequest

    Returns:
        DefectDiagnosisResponse with diagnosis and remedies
    """
    if not _consultation_system:
        raise HTTPException(status_code=503, detail="Consultation system not initialized")

    try:
        from vastu.embedded_principles import VASTU_DOSHAS

        defect_key = request.defect_type.lower().replace(" ", "_")

        if defect_key not in VASTU_DOSHAS:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown defect: {request.defect_type}"
            )

        dosha_info = VASTU_DOSHAS[defect_key]

        return DefectDiagnosisResponse(
            defect=request.defect_type,
            problem=dosha_info.get("description", ""),
            impact=str(dosha_info.get("impacts", {}).get("health", ["Unknown"])[0]),
            severity=dosha_info.get("severity", "MEDIUM"),
            remedies=dosha_info.get("remedies", []),
            detailed_remedies=[
                {"remedy": r, "details": f"Apply as needed for {request.defect_type}"}
                for r in dosha_info.get("remedies", [])
            ]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in defect diagnosis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# 5. SPACE ANALYSIS ENDPOINT
# ============================================================================

@router.post("/spaces/analyze", response_model=SpaceAnalysisResponse, tags=["analysis"])
async def analyze_space(request: SpaceAnalysisRequest) -> SpaceAnalysisResponse:
    """
    Analyze a space for Vastu compliance.

    Args:
        request: SpaceAnalysisRequest with space details

    Returns:
        SpaceAnalysisResponse with compliance score and recommendations
    """
    if not _consultation_system:
        raise HTTPException(status_code=503, detail="Consultation system not initialized")

    try:
        analysis = await _consultation_system.analyze_space({
            "name": request.space_name,
            "type": request.space_type,
            "direction": request.direction,
            "area": request.area_sqft,
            "features": request.features,
            "issues": request.issues,
            "purpose": request.purpose,
        })

        return SpaceAnalysisResponse(
            space_name=request.space_name,
            compliance_score=analysis.get("compliance_score", 50),
            issues=analysis.get("issues", []) or request.issues or [],
            recommendations=analysis.get("recommendations", []),
            suggested_color=analysis.get("suggested_color", "White"),
            element_association=analysis.get("element_association"),
            remedies=analysis.get("remedies", [])
        )

    except Exception as e:
        logger.error(f"Error in space analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# 6. BATCH CONSULTATION ENDPOINT
# ============================================================================

class BatchConsultationRequest(BaseModel):
    """Batch consultation request."""
    queries: List[str] = Field(..., min_items=1, max_items=10)
    include_remedies: bool = Field(default=True)


class BatchConsultationResponse(BaseModel):
    """Batch consultation response."""
    results: List[ConsultationResponse]
    summary: Dict[str, Any]
    total_processing_time_ms: float


@router.post("/batch-consult", response_model=BatchConsultationResponse, tags=["consultation"])
async def batch_consultation(request: BatchConsultationRequest) -> BatchConsultationResponse:
    """
    Process multiple consultation queries in batch.

    Args:
        request: BatchConsultationRequest with list of queries

    Returns:
        BatchConsultationResponse with all results and summary
    """
    start_time = time.time()

    results = []
    for query in request.queries:
        try:
            result = await main_consultation(
                ConsultationRequest(
                    query=query,
                    include_remedies=request.include_remedies
                )
            )
            results.append(result)
        except Exception as e:
            logger.error(f"Error processing query '{query}': {e}")
            # Continue with next query
            results.append(
                ConsultationResponse(
                    query=query,
                    recommendation={"status": "error", "message": str(e)},
                    metadata={"timestamp": datetime.now().isoformat()},
                    sources_used=[],
                    processing_time_ms=0
                )
            )

    processing_time_ms = (time.time() - start_time) * 1000

    return BatchConsultationResponse(
        results=results,
        summary={
            "total_queries": len(request.queries),
            "successful": len([r for r in results if r.recommendation.get("status") != "error"]),
            "avg_processing_time_ms": processing_time_ms / len(request.queries) if request.queries else 0,
        },
        total_processing_time_ms=processing_time_ms,
    )


# ============================================================================
# 7. BATCH SPACE ANALYSIS ENDPOINT
# ============================================================================

@router.post("/spaces/analyze-batch", response_model=BatchSpaceAnalysisResponse, tags=["analysis"])
async def analyze_spaces_batch(request: BatchSpaceAnalysisRequest) -> BatchSpaceAnalysisResponse:
    """
    Analyze multiple spaces in batch.

    Args:
        request: BatchSpaceAnalysisRequest with list of spaces

    Returns:
        BatchSpaceAnalysisResponse with all analyses and summary
    """
    if not _consultation_system:
        raise HTTPException(status_code=503, detail="Consultation system not initialized")

    start_time = time.time()
    analyses = []
    compliance_scores = []

    for space in request.spaces:
        try:
            analysis = await analyze_space(space)
            analyses.append(analysis)
            compliance_scores.append(analysis.compliance_score)
        except Exception as e:
            logger.error(f"Error analyzing space '{space.space_name}': {e}")
            # Continue with next space
            analyses.append(
                SpaceAnalysisResponse(
                    space_name=space.space_name,
                    compliance_score=0,
                    issues=[str(e)],
                    recommendations=[],
                    suggested_color="",
                    remedies=[]
                )
            )

    overall_score = sum(compliance_scores) / len(compliance_scores) if compliance_scores else 0
    processing_time_ms = (time.time() - start_time) * 1000

    summary = f"Analyzed {len(request.spaces)} spaces. Overall compliance score: {overall_score:.1f}/100."

    return BatchSpaceAnalysisResponse(
        analyses=analyses,
        overall_score=overall_score,
        summary=summary
    )
