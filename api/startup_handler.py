"""
Startup and Shutdown Handlers for Vastu Shastra DSS v4.0

Manages:
- Initialization of core components (consultation system, KG, Chroma DB)
- Health status tracking
- Graceful degradation when optional services unavailable
- Resource cleanup on shutdown

Author: Claude Haiku 4.5
Version: 4.0.0
"""

import logging
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class StartupManager:
    """Manages application startup and initialization."""

    def __init__(self):
        """Initialize startup manager."""
        self.components_status: Dict[str, str] = {}
        self.startup_timestamp = None
        self.consultation_system = None
        self.kg_data = None
        self.chroma_db = None

    async def initialize_all(self) -> Dict[str, Any]:
        """
        Initialize all application components.

        Returns:
            Dictionary with initialization results
        """
        logger.info("=" * 80)
        logger.info("VASTU SHASTRA DSS v4.0 - INITIALIZING ALL COMPONENTS")
        logger.info("=" * 80)

        self.startup_timestamp = datetime.now()
        results = {
            "startup_time": self.startup_timestamp.isoformat(),
            "components": {},
            "errors": [],
        }

        # 1. Initialize Standalone Consultation System (REQUIRED)
        try:
            await self._initialize_consultation_system()
            results["components"]["consultation_system"] = "operational"
            logger.info("✓ Consultation system initialized")
        except Exception as e:
            logger.error(f"✗ CRITICAL: Consultation system initialization failed: {e}")
            results["errors"].append(f"Consultation system: {str(e)}")
            results["components"]["consultation_system"] = "failed"
            raise

        # 2. Initialize Local KG (OPTIONAL)
        try:
            await self._initialize_local_kg()
            results["components"]["local_kg"] = "operational"
            logger.info("✓ Local Knowledge Graph loaded")
        except Exception as e:
            logger.warning(f"⚠ Local KG initialization failed: {e}")
            results["errors"].append(f"Local KG: {str(e)}")
            results["components"]["local_kg"] = "unavailable"

        # 3. Initialize Chroma DB (OPTIONAL)
        try:
            await self._initialize_chroma_db()
            results["components"]["chroma_db"] = "operational"
            logger.info("✓ Chroma DB initialized")
        except Exception as e:
            logger.warning(f"⚠ Chroma DB initialization failed: {e}")
            results["errors"].append(f"Chroma DB: {str(e)}")
            results["components"]["chroma_db"] = "unavailable"

        logger.info("=" * 80)
        logger.info("INITIALIZATION COMPLETE")
        logger.info(f"Components: {', '.join([f'{k}={v}' for k, v in results['components'].items()])}")
        logger.info("=" * 80)

        return results

    async def _initialize_consultation_system(self) -> None:
        """Initialize standalone consultation system."""
        logger.info("Initializing Standalone Consultation System...")

        try:
            from vastu.standalone_consultation import StandaloneConsultation
            self.consultation_system = StandaloneConsultation()
            logger.info("  ✓ StandaloneConsultation imported and instantiated")
        except ImportError as e:
            raise RuntimeError(f"Could not import StandaloneConsultation: {e}")
        except Exception as e:
            raise RuntimeError(f"Error creating StandaloneConsultation instance: {e}")

    async def _initialize_local_kg(self) -> None:
        """Initialize local Knowledge Graph."""
        logger.info("Loading Local Knowledge Graph...")

        try:
            # Construct path to KG file
            kg_path = Path(__file__).parent.parent / "data" / "kg" / "vastu_knowledge_graph_final.json"

            if not kg_path.exists():
                raise FileNotFoundError(f"KG file not found at {kg_path}")

            # Load KG
            with open(kg_path, 'r', encoding='utf-8') as f:
                self.kg_data = json.load(f)

            logger.info(f"  ✓ KG file loaded: {kg_path.name}")

            # Validate KG structure
            metadata = self.kg_data.get("metadata", {})
            nodes_count = len(self.kg_data.get("nodes", []))
            edges_count = len(self.kg_data.get("edges", []))

            logger.info(f"    - Version: {metadata.get('version')}")
            logger.info(f"    - Nodes: {nodes_count}")
            logger.info(f"    - Edges: {edges_count}")
            logger.info(f"    - Entity types: {metadata.get('entity_types')}")
            logger.info(f"    - Relation types: {metadata.get('relation_types')}")

        except FileNotFoundError as e:
            raise RuntimeError(f"KG file not found: {e}")
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Invalid JSON in KG file: {e}")
        except Exception as e:
            raise RuntimeError(f"Error loading KG: {e}")

    async def _initialize_chroma_db(self) -> None:
        """Initialize Chroma vector database."""
        logger.info("Initializing Chroma Vector Database...")

        try:
            import chromadb
        except ImportError:
            raise RuntimeError("chromadb not installed. Install with: pip install chromadb")

        try:
            # Construct path to Chroma DB
            chroma_path = Path(__file__).parent.parent / "vdb" / "chroma_vastu_db"

            if not chroma_path.exists():
                raise FileNotFoundError(f"Chroma DB directory not found at {chroma_path}")

            logger.info(f"  ✓ Chroma DB directory found: {chroma_path}")

            # Initialize Chroma client
            chroma_client = chromadb.PersistentClient(path=str(chroma_path))
            logger.info("    - PersistentClient created")

            # Try to get collection
            try:
                self.chroma_db = chroma_client.get_collection(name="vastu_texts")
                logger.info("    - Collection 'vastu_texts' retrieved")

                # Get collection stats
                count = self.chroma_db.count()
                logger.info(f"    - Collection contains {count} documents")

            except Exception as e:
                logger.warning(f"  ⚠ Could not access 'vastu_texts' collection: {e}")
                logger.info("    - Attempting to list available collections...")

                try:
                    collections = chroma_client.list_collections()
                    logger.info(f"    - Available collections: {[c.name for c in collections]}")
                except:
                    pass

                raise RuntimeError(f"Chroma collection not accessible: {e}")

        except FileNotFoundError as e:
            raise RuntimeError(f"Chroma DB path error: {e}")
        except Exception as e:
            raise RuntimeError(f"Error initializing Chroma DB: {e}")

    async def shutdown(self) -> None:
        """Clean up resources on shutdown."""
        logger.info("Shutting down application...")

        try:
            # Close database connections
            if self.chroma_db:
                logger.info("Closing Chroma DB connection...")
                # Chroma doesn't require explicit closing

            logger.info("All resources cleaned up successfully")

        except Exception as e:
            logger.error(f"Error during shutdown: {e}")


# Global instance
_startup_manager = None


async def startup_event():
    """FastAPI startup event handler."""
    global _startup_manager

    try:
        _startup_manager = StartupManager()
        results = await _startup_manager.initialize_all()

        # Register consultation system with endpoints
        from .endpoints_complete import set_consultation_system
        set_consultation_system(_startup_manager.consultation_system)
        logger.info("✓ Consultation system registered with endpoints")

        return results

    except Exception as e:
        logger.critical(f"STARTUP FAILED: {e}", exc_info=True)
        raise


async def shutdown_event():
    """FastAPI shutdown event handler."""
    global _startup_manager

    try:
        if _startup_manager:
            await _startup_manager.shutdown()
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


def get_startup_manager() -> Optional[StartupManager]:
    """Get the startup manager instance."""
    return _startup_manager


def get_consultation_system():
    """Get the consultation system instance."""
    global _startup_manager
    return _startup_manager.consultation_system if _startup_manager else None


def get_kg_data():
    """Get the loaded KG data."""
    global _startup_manager
    return _startup_manager.kg_data if _startup_manager else None


def get_chroma_db():
    """Get the Chroma DB instance."""
    global _startup_manager
    return _startup_manager.chroma_db if _startup_manager else None
