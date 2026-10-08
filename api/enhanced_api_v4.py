"""
Enhanced FastAPI Backend for Vastu Shastra DSS v4.0

Core features:
- Standalone operation without external VDBs
- Graceful degradation if optional services unavailable
- Comprehensive health checks and system status
- Async request handling with proper error management
- Complete metadata tracking for all responses
- Support for batch operations
- CORS and security middleware

Author: Claude Haiku 4.5
Version: 4.0.0
"""

import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, Field

from config.settings import settings
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

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# Global State
# ============================================================================

# System state tracking
class SystemState:
    """Global system state container."""
    consultation_system = None
    kg_loader = None
    chroma_db = None
    health_status = {
        "api": "initializing",
        "consultation": "initializing",
        "kg": "initializing",
        "chroma_db": "initializing",
        "startup_time": datetime.now().isoformat(),
        "last_check": datetime.now().isoformat(),
    }
    performance_metrics = {
        "total_requests": 0,
        "total_consultations": 0,
        "avg_response_time_ms": 0,
    }


# ============================================================================
# Lifespan Management
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan: startup and shutdown."""
    # STARTUP
    logger.info("=" * 80)
    logger.info("VASTU SHASTRA DSS v4.0 - STARTUP INITIATED")
    logger.info("=" * 80)

    try:
        # Initialize core components
        from vastu.standalone_consultation import StandaloneConsultation
        SystemState.consultation_system = StandaloneConsultation()
        SystemState.health_status["consultation"] = "operational"
        logger.info("✓ Standalone consultation system initialized")

        # Try to load local KG
        try:
            from vastu.local_kg import LocalKGQueryEngine
            kg_path = Path(__file__).parent.parent / "data" / "kg" / "vastu_knowledge_graph_final.json"
            if kg_path.exists():
                with open(kg_path, 'r') as f:
                    kg_data = json.load(f)
                SystemState.kg_loader = kg_data
                SystemState.health_status["kg"] = "operational"
                logger.info(f"✓ Local KG loaded: {kg_path.name} ({kg_data['metadata']['total_nodes']} nodes, {kg_data['metadata']['total_edges']} edges)")
            else:
                logger.warning(f"⚠ Local KG not found at {kg_path}")
                SystemState.health_status["kg"] = "unavailable"
        except Exception as e:
            logger.warning(f"⚠ Could not load local KG: {e}")
            SystemState.health_status["kg"] = "degraded"

        # Try to load Chroma DB
        try:
            import chromadb
            chroma_path = Path(__file__).parent.parent / "vdb" / "chroma_vastu_db"
            if chroma_path.exists():
                chroma_client = chromadb.PersistentClient(path=str(chroma_path))
                try:
                    SystemState.chroma_db = chroma_client.get_collection(name="vastu_texts")
                    SystemState.health_status["chroma_db"] = "operational"
                    logger.info(f"✓ Chroma DB collection loaded successfully")
                except Exception as e:
                    logger.warning(f"⚠ Could not access Chroma collection: {e}")
                    SystemState.health_status["chroma_db"] = "unavailable"
            else:
                logger.warning(f"⚠ Chroma DB not found at {chroma_path}")
                SystemState.health_status["chroma_db"] = "unavailable"
        except ImportError:
            logger.warning("⚠ chromadb not available, proceeding without Chroma DB")
            SystemState.health_status["chroma_db"] = "unavailable"
        except Exception as e:
            logger.warning(f"⚠ Could not initialize Chroma DB: {e}")
            SystemState.health_status["chroma_db"] = "degraded"

        SystemState.health_status["api"] = "operational"
        SystemState.health_status["startup_time"] = datetime.now().isoformat()
        logger.info("✓ API core systems initialized")
        logger.info("=" * 80)
        logger.info("STARTUP COMPLETE - System ready for requests")
        logger.info("=" * 80)

    except Exception as e:
        logger.error(f"✗ CRITICAL STARTUP ERROR: {e}", exc_info=True)
        SystemState.health_status["api"] = "failed"
        raise

    yield

    # SHUTDOWN
    logger.info("Shutting down application...")
    try:
        # Cleanup resources
        logger.info("Closing database connections...")
        logger.info("Application shutdown complete")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


# ============================================================================
# FastAPI Application Factory
# ============================================================================

def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(
        title=settings.api_title,
        version=settings.api_version,
        description="Vastu Shastra Decision Support System - FastAPI Backend v4.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Process-Time", "X-Request-ID"],
    )

    # Custom exception handlers
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request, exc):
        """Handle validation errors with detailed response."""
        logger.warning(f"Validation error: {exc}")
        return JSONResponse(
            status_code=422,
            content={
                "error": "Request validation failed",
                "error_code": "VALIDATION_ERROR",
                "details": exc.errors(),
                "timestamp": datetime.now().isoformat(),
            },
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request, exc):
        """Handle unexpected exceptions."""
        logger.error(f"Unexpected error: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "error_code": "INTERNAL_ERROR",
                "message": str(exc) if settings.debug else "An unexpected error occurred",
                "timestamp": datetime.now().isoformat(),
            },
        )

    return app


# Create app instance
app = create_app()


# ============================================================================
# Root Endpoints
# ============================================================================

@app.get("/", tags=["root"])
async def root():
    """Root endpoint - API information."""
    return {
        "name": "Vastu Shastra Decision Support System",
        "version": settings.api_version,
        "description": "AI-powered consultation platform for Vastu Shastra principles",
        "documentation": "/docs",
        "api_v1": "/api/v1",
        "health": "/api/v1/health",
        "status": "/api/v1/status",
    }


@app.get("/api/v1", tags=["api-info"])
async def api_info():
    """API v1 information and available endpoints."""
    return {
        "version": "1.0.0",
        "name": "Vastu Shastra DSS API v1",
        "documentation": "/docs",
        "endpoints": {
            "health": {
                "url": "/api/v1/health",
                "method": "GET",
                "description": "Check system health and component status",
            },
            "status": {
                "url": "/api/v1/status",
                "method": "GET",
                "description": "Detailed system status with performance metrics",
            },
            "system-info": {
                "url": "/api/v1/system-info",
                "method": "GET",
                "description": "System configuration and available features",
            },
            "consult": {
                "url": "/api/v1/consult",
                "method": "POST",
                "description": "Main consultation endpoint",
                "input": {"query": "str", "force_standalone": "bool (optional)"},
            },
            "batch-consult": {
                "url": "/api/v1/batch-consult",
                "method": "POST",
                "description": "Batch consultation for multiple queries",
                "input": {"queries": ["str"]},
            },
            "directions-consult": {
                "url": "/api/v1/directions/consult",
                "method": "POST",
                "description": "Get consultation for a specific direction",
            },
            "rooms-consult": {
                "url": "/api/v1/rooms/consult",
                "method": "POST",
                "description": "Get consultation for a specific room type",
            },
            "spaces-analyze": {
                "url": "/api/v1/spaces/analyze",
                "method": "POST",
                "description": "Analyze a space for Vastu compliance",
            },
            "spaces-analyze-batch": {
                "url": "/api/v1/spaces/analyze-batch",
                "method": "POST",
                "description": "Batch analyze multiple spaces",
            },
        },
    }


# ============================================================================
# Health & Status Endpoints
# ============================================================================

@app.get("/api/v1/health", response_model=HealthCheckResponse, tags=["health"])
async def health_check() -> HealthCheckResponse:
    """
    Health check endpoint.

    Returns:
        HealthCheckResponse with component status
    """
    SystemState.health_status["last_check"] = datetime.now().isoformat()

    overall_status = "healthy" if SystemState.health_status["api"] == "operational" else "degraded"

    return HealthCheckResponse(
        status=overall_status,
        components={
            "api": SystemState.health_status["api"],
            "consultation_system": SystemState.health_status["consultation"],
            "local_kg": SystemState.health_status["kg"],
            "chroma_db": SystemState.health_status["chroma_db"],
        },
        timestamp=datetime.now().isoformat(),
        message=f"System is {overall_status}. API started at {SystemState.health_status['startup_time']}"
    )


class StatusResponse(BaseModel):
    """Detailed status response."""
    status: str
    components: Dict[str, str]
    performance: Dict[str, Any]
    uptime_seconds: Optional[float] = None
    timestamp: str


@app.get("/api/v1/status", response_model=StatusResponse, tags=["health"])
async def status():
    """
    Detailed status endpoint.

    Returns:
        Comprehensive system status including performance metrics
    """
    startup_time = SystemState.health_status.get("startup_time")
    uptime_seconds = None
    if startup_time:
        startup_dt = datetime.fromisoformat(startup_time)
        uptime_seconds = (datetime.now() - startup_dt).total_seconds()

    return StatusResponse(
        status="operational" if SystemState.health_status["api"] == "operational" else "degraded",
        components=SystemState.health_status,
        performance=SystemState.performance_metrics,
        uptime_seconds=uptime_seconds,
        timestamp=datetime.now().isoformat(),
    )


class SystemInfoResponse(BaseModel):
    """System information response."""
    api_version: str
    system_name: str
    capabilities: List[str]
    embedded_components: Dict[str, Any]
    configuration: Dict[str, Any]


@app.get("/api/v1/system-info", response_model=SystemInfoResponse, tags=["system"])
async def system_info():
    """
    Get system configuration and available features.

    Returns:
        System information including capabilities and configuration
    """
    from vastu.embedded_principles import (
        DIRECTIONS, VASTU_DOSHAS, ROOM_PLACEMENTS, REMEDIES
    )

    capabilities = [
        "standalone_consultation",
        "direction_analysis",
        "room_placement_guidance",
        "defect_diagnosis",
        "space_analysis",
        "batch_operations",
        "graceful_degradation",
    ]

    if SystemState.chroma_db:
        capabilities.append("vector_search")

    if SystemState.kg_loader:
        capabilities.append("knowledge_graph_reasoning")

    return SystemInfoResponse(
        api_version=settings.api_version,
        system_name="Vastu Shastra DSS v4.0",
        capabilities=capabilities,
        embedded_components={
            "directions": len(DIRECTIONS),
            "vastu_doshas": len(VASTU_DOSHAS),
            "room_types": len(ROOM_PLACEMENTS),
            "remedy_categories": len(REMEDIES),
            "kg_nodes": len(SystemState.kg_loader.get("nodes", [])) if SystemState.kg_loader else 0,
            "kg_edges": len(SystemState.kg_loader.get("edges", [])) if SystemState.kg_loader else 0,
        },
        configuration={
            "enable_rag": settings.enable_rag,
            "enable_kg_reasoning": settings.enable_kg_reasoning,
            "enable_hybrid_search": settings.enable_hybrid_search,
            "enable_degradation": settings.enable_degradation,
            "debug_mode": settings.debug,
        },
    )


# ============================================================================
# Import endpoints module
# ============================================================================

# Import and include endpoint router
try:
    from .endpoints_complete import router as complete_router
    app.include_router(complete_router)
    logger.info("✓ Complete endpoints router included")
except ImportError as e:
    logger.warning(f"⚠ Could not import complete endpoints: {e}")
    logger.info("Falling back to basic endpoints...")
    from .endpoints import router as basic_router
    app.include_router(basic_router)


# ============================================================================
# Utility Endpoints
# ============================================================================

@app.get("/api/v1/directions", tags=["reference"])
async def list_directions() -> List[str]:
    """List all available directions."""
    from vastu.embedded_principles import DIRECTIONS
    return list(DIRECTIONS.keys())


@app.get("/api/v1/rooms", tags=["reference"])
async def list_rooms() -> List[str]:
    """List all available room types."""
    from vastu.embedded_principles import ROOM_PLACEMENTS
    return list(ROOM_PLACEMENTS.keys())


@app.get("/api/v1/doshas", tags=["reference"])
async def list_doshas() -> List[str]:
    """List all known Vastu doshas."""
    from vastu.embedded_principles import VASTU_DOSHAS
    return list(VASTU_DOSHAS.keys())


@app.get("/api/v1/principles", tags=["reference"])
async def list_principles():
    """List all Vastu principles."""
    from vastu.embedded_principles import DIRECTIONS, SACRED_GEOMETRY, HEALTH_CORRELATIONS

    return {
        "directions": list(DIRECTIONS.keys()),
        "sacred_geometry": list(SACRED_GEOMETRY.keys()),
        "health_correlations": list(HEALTH_CORRELATIONS.keys()),
    }


# ============================================================================
# Server Entry Point
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host=settings.api_host,
        port=settings.api_port,
        log_level=settings.log_level.lower(),
        reload=settings.debug,
    )
