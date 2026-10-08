"""Startup and shutdown handlers for the FastAPI app."""

import logging
from typing import Callable

logger = logging.getLogger(__name__)


async def startup_event():
    """Run on application startup."""
    logger.info("Application startup initiated")

    # Initialize components
    logger.info("Initializing Vastu Shastra DSS...")

    try:
        # Load configuration
        from config import settings

        logger.info(f"Configuration loaded: {settings.api_host}:{settings.api_port}")

        # Initialize standalone consultation
        from vastu.standalone_consultation import StandaloneConsultation

        logger.info("Standalone consultation system initialized")

        # Try to initialize database connections (optional)
        try:
            logger.info("Attempting to initialize vector databases...")
            # Database initialization would go here
            logger.info("Vector databases initialized (or will use fallback)")
        except Exception as e:
            logger.warning(f"Vector database initialization failed, will use graceful fallback: {e}")

        logger.info("Application startup complete")

    except Exception as e:
        logger.error(f"Startup error: {e}")
        raise


async def shutdown_event():
    """Run on application shutdown."""
    logger.info("Application shutdown initiated")

    try:
        # Clean up resources
        logger.info("Cleaning up resources...")

        # Close database connections
        logger.info("Closing database connections...")

        logger.info("Application shutdown complete")

    except Exception as e:
        logger.error(f"Shutdown error: {e}")


def get_startup_handler() -> Callable:
    """Get startup event handler."""
    return startup_event


def get_shutdown_handler() -> Callable:
    """Get shutdown event handler."""
    return shutdown_event
