#!/usr/bin/env python
"""Run the Vastu Shastra DSS server."""

import os
import sys
import logging
import uvicorn
from pathlib import Path

# Add project to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    """Run the server."""
    from config import settings

    logger.info("Starting Vastu Shastra DSS...")
    logger.info(f"Configuration: {settings.api_host}:{settings.api_port}")

    # Verify required settings
    errors = settings.validate_required_settings()
    if errors:
        logger.error("Configuration errors:")
        for error in errors:
            logger.error(f"  - {error}")
        sys.exit(1)

    logger.info("Configuration validated successfully")

    # Start server
    try:
        uvicorn.run(
            "api.main:app",
            host=settings.api_host,
            port=settings.api_port,
            reload=settings.debug,
            log_level=settings.log_level.lower(),
        )
    except Exception as e:
        logger.error(f"Server startup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
