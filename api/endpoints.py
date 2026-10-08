"""API endpoints for Vastu Shastra DSS."""

import logging
from datetime import datetime
from typing import List

from fastapi import APIRouter, HTTPException, Query
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

router = APIRouter(prefix="/api/v1", tags=["vastu"])

# Global consultation system instance
consultation_system = None


def set_consultation_system(system):
    """Set the global consultation system instance."""
    global consultation_system
    consultation_system = system


# Health Check Endpoints


@router.get("/health", response_model=HealthCheckResponse)
async def health_check() -> HealthCheckResponse:
    """Check API health status."""
    return HealthCheckResponse(
        status="healthy",
        components={
            "api": "operational",
            "consultation": "operational",
            "database": "operational",
        },
        timestamp=datetime.now().isoformat(),
    )


# Direction Consultation Endpoints


@router.post("/directions/consult", response_model=DirectionConsultationResponse)
async def consult_direction(request: DirectionConsultationRequest) -> DirectionConsultationResponse:
    """Get consultation for a specific direction."""
    if not consultation_system:
        raise HTTPException(status_code=503, detail="Consultation system not initialized")

    try:
        result = await consultation_system.get_direction_consultation(request.direction)

        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])

        return DirectionConsultationResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in direction consultation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/directions", response_model=List[str])
async def list_directions() -> List[str]:
    """Get list of all directions."""
    from config.constants import CARDINAL_DIRECTIONS

    return CARDINAL_DIRECTIONS


# Room Consultation Endpoints


@router.post("/rooms/consult", response_model=RoomConsultationResponse)
async def consult_room(request: RoomConsultationRequest) -> RoomConsultationResponse:
    """Get consultation for a specific room type."""
    if not consultation_system:
        raise HTTPException(status_code=503, detail="Consultation system not initialized")

    try:
        result = await consultation_system.get_room_consultation(request.room_type)

        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])

        return RoomConsultationResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in room consultation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rooms", response_model=List[str])
async def list_rooms() -> List[str]:
    """Get list of all room types."""
    from config.constants import ROOM_TYPES

    return ROOM_TYPES


# Defect Diagnosis Endpoints


@router.post("/defects/diagnose", response_model=DefectDiagnosisResponse)
async def diagnose_defect(request: DefectDiagnosisRequest) -> DefectDiagnosisResponse:
    """Diagnose a Vastu defect."""
    if not consultation_system:
        raise HTTPException(status_code=503, detail="Consultation system not initialized")

    try:
        result = await consultation_system.diagnose_defect(request.defect_type)

        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])

        return DefectDiagnosisResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in defect diagnosis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Space Analysis Endpoints


@router.post("/spaces/analyze", response_model=SpaceAnalysisResponse)
async def analyze_space(request: SpaceAnalysisRequest) -> SpaceAnalysisResponse:
    """Analyze a space for Vastu compliance."""
    if not consultation_system:
        raise HTTPException(status_code=503, detail="Consultation system not initialized")

    try:
        space_dict = request.dict()
        result = await consultation_system.analyze_space(space_dict)

        # Convert result to response schema
        response = SpaceAnalysisResponse(
            space_name=result.get("space_name", ""),
            compliance_score=result.get("compliance_score", 0),
            issues=result.get("critical_issues", []),
            recommendations=result.get("recommendations", []),
            suggested_color=result.get("suggested_color", ""),
            element_association=result.get("element_association"),
            remedies=result.get("remedies", []),
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in space analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/spaces/analyze-batch", response_model=BatchSpaceAnalysisResponse)
async def analyze_spaces_batch(request: BatchSpaceAnalysisRequest) -> BatchSpaceAnalysisResponse:
    """Analyze multiple spaces."""
    if not consultation_system:
        raise HTTPException(status_code=503, detail="Consultation system not initialized")

    try:
        spaces = [space.dict() for space in request.spaces]
        results = await consultation_system.batch_analyze_spaces(spaces)

        # Convert results
        analyses = []
        total_score = 0

        for result in results:
            analysis = SpaceAnalysisResponse(
                space_name=result.get("space_name", ""),
                compliance_score=result.get("compliance_score", 0),
                issues=result.get("critical_issues", []),
                recommendations=result.get("recommendations", []),
                suggested_color=result.get("suggested_color", ""),
                element_association=result.get("element_association"),
                remedies=result.get("remedies", []),
            )
            analyses.append(analysis)
            total_score += result.get("compliance_score", 0)

        overall_score = total_score / len(results) if results else 0

        return BatchSpaceAnalysisResponse(
            analyses=analyses,
            overall_score=overall_score,
            summary=f"Analyzed {len(results)} spaces with average compliance score of {overall_score:.1f}",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in batch space analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/consultation")
async def create_consultation(space: SpaceAnalysisRequest):
    """Create a full consultation report."""
    if not consultation_system:
        raise HTTPException(status_code=503, detail="Consultation system not initialized")

    try:
        space_dict = space.dict()
        report = await consultation_system.create_consultation_report(space_dict)

        return {
            "report": report,
            "timestamp": datetime.now().isoformat(),
            "status": "success",
        }

    except Exception as e:
        logger.error(f"Error creating consultation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Information Endpoints


@router.get("/principles")
async def get_all_principles():
    """Get all Vastu principles."""
    from vastu.constants import VASTU_PRINCIPLES

    return VASTU_PRINCIPLES


@router.get("/remedies")
async def get_all_remedies():
    """Get all available remedies."""
    from vastu.constants import REMEDIES_BY_TYPE

    return REMEDIES_BY_TYPE


@router.get("/system-info")
async def get_system_info():
    """Get system information."""
    from config import settings

    return {
        "system": "Vastu Shastra Decision Support System",
        "version": "1.0.0",
        "api_version": "v1",
        "debug_mode": settings.debug,
        "timestamp": datetime.now().isoformat(),
    }
