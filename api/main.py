"""Main FastAPI application."""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .startup import startup_event, shutdown_event
from .endpoints import router, set_consultation_system
from config import settings

# Configure logging
logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description="Vastu Shastra Decision Support System using Claude AI",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(router)


# Startup and shutdown events
@app.on_event("startup")
async def on_startup():
    """Initialize application on startup."""
    await startup_event()

    # Initialize consultation system
    from vastu.standalone_consultation import StandaloneConsultation

    consultation_system = StandaloneConsultation()
    set_consultation_system(consultation_system)
    logger.info("Consultation system initialized and registered")


@app.on_event("shutdown")
async def on_shutdown():
    """Clean up on shutdown."""
    await shutdown_event()


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to Vastu Shastra Decision Support System",
        "version": settings.api_version,
        "docs": "/docs",
        "api": "/api/v1",
    }


# API version info
@app.get("/api/v1")
async def api_info():
    """API v1 information."""
    return {
        "version": "1.0",
        "endpoints": [
            "/api/v1/health",
            "/api/v1/directions/consult",
            "/api/v1/directions",
            "/api/v1/rooms/consult",
            "/api/v1/rooms",
            "/api/v1/defects/diagnose",
            "/api/v1/spaces/analyze",
            "/api/v1/spaces/analyze-batch",
            "/api/v1/consultation",
            "/api/v1/principles",
            "/api/v1/remedies",
            "/api/v1/system-info",
        ],
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=settings.api_host, port=settings.api_port)
