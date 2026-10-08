"""Graceful fallback mechanism for database failures."""

import logging
from typing import List, Dict, Optional, Any, Callable
from enum import Enum

logger = logging.getLogger(__name__)


class FallbackStrategy(Enum):
    """Fallback strategies for database failures."""

    PRIMARY_ONLY = "primary_only"
    PRIMARY_WITH_SECONDARY = "primary_with_secondary"
    SECONDARY_FALLBACK = "secondary_fallback"
    GRACEFUL_DEGRADATION = "graceful_degradation"
    OFFLINE_MODE = "offline_mode"


class GracefulFallback:
    """
    Handles graceful fallback when primary database is unavailable.
    Supports multiple fallback strategies and offline modes.
    """

    def __init__(self, strategy: FallbackStrategy = FallbackStrategy.SECONDARY_FALLBACK):
        """
        Initialize graceful fallback.

        Args:
            strategy: Fallback strategy to use
        """
        self.strategy = strategy
        self.primary_db = None
        self.secondary_db = None
        self.cache = {}
        self.fallback_active = False
        self.fallback_reason = None
        self.offline_fallback = None

    def set_primary(self, db: Any) -> None:
        """Set primary database adapter."""
        self.primary_db = db

    def set_secondary(self, db: Any) -> None:
        """Set secondary database adapter."""
        self.secondary_db = db

    def set_offline_fallback(self, fallback_fn: Callable) -> None:
        """
        Set offline fallback function.

        Args:
            fallback_fn: Function to call when offline
        """
        self.offline_fallback = fallback_fn

    async def search_with_fallback(
        self, query_vector: List[float], top_k: int = 5, filter_dict: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Search with fallback strategy.

        Args:
            query_vector: Query vector
            top_k: Number of results
            filter_dict: Optional filters

        Returns:
            Search results with fallback info
        """
        result = {
            "results": [],
            "fallback_active": False,
            "fallback_reason": None,
            "source": "primary",
        }

        # Try primary database
        if self.primary_db:
            try:
                primary_results = await self.primary_db.search(
                    query_vector, top_k=top_k, filter_dict=filter_dict
                )
                result["results"] = primary_results
                result["source"] = "primary"
                result["fallback_active"] = False
                self.fallback_active = False
                return result
            except Exception as e:
                logger.warning(f"Primary database search failed: {e}")
                result["fallback_reason"] = str(e)

        # Execute fallback strategy
        if self.strategy == FallbackStrategy.PRIMARY_ONLY:
            logger.error("Primary database failed and no fallback configured")
            result["error"] = "Primary database unavailable and fallback disabled"

        elif self.strategy == FallbackStrategy.SECONDARY_FALLBACK:
            result = await self._fallback_to_secondary(query_vector, top_k, filter_dict, result)

        elif self.strategy == FallbackStrategy.GRACEFUL_DEGRADATION:
            result = await self._graceful_degradation(query_vector, top_k, result)

        elif self.strategy == FallbackStrategy.OFFLINE_MODE:
            result = await self._offline_mode(query_vector, top_k, filter_dict, result)

        self.fallback_active = True
        return result

    async def _fallback_to_secondary(
        self, query_vector: List[float], top_k: int, filter_dict: Optional[Dict], result: Dict
    ) -> Dict:
        """Fallback to secondary database."""
        if not self.secondary_db:
            logger.error("Secondary database not configured")
            return result

        try:
            secondary_results = await self.secondary_db.search(
                query_vector, top_k=top_k, filter_dict=filter_dict
            )
            result["results"] = secondary_results
            result["source"] = "secondary"
            result["fallback_active"] = True
            logger.info("Successfully fell back to secondary database")
        except Exception as e:
            logger.error(f"Secondary database also failed: {e}")
            result["error"] = f"Both primary and secondary failed: {e}"

        return result

    async def _graceful_degradation(self, query_vector: List[float], top_k: int, result: Dict) -> Dict:
        """Graceful degradation - return cached or partial results."""
        # Try to return cached results
        cache_key = str(query_vector[:10])  # Use first 10 dimensions as cache key
        if cache_key in self.cache:
            result["results"] = self.cache[cache_key]
            result["source"] = "cache"
            result["fallback_active"] = True
            logger.info("Returned cached results for query")
            return result

        # Use offline fallback if available
        if self.offline_fallback:
            try:
                offline_results = await self.offline_fallback(query_vector, top_k)
                result["results"] = offline_results
                result["source"] = "offline_fallback"
                result["fallback_active"] = True
                logger.info("Using offline fallback for results")
            except Exception as e:
                logger.error(f"Offline fallback failed: {e}")

        return result

    async def _offline_mode(
        self, query_vector: List[float], top_k: int, filter_dict: Optional[Dict], result: Dict
    ) -> Dict:
        """Complete offline mode - use local knowledge only."""
        if self.offline_fallback:
            try:
                offline_results = await self.offline_fallback(query_vector, top_k)
                result["results"] = offline_results
                result["source"] = "offline"
                result["fallback_active"] = True
                logger.info("Operating in offline mode")
            except Exception as e:
                logger.error(f"Offline mode failed: {e}")
                result["error"] = f"Offline mode unavailable: {e}"

        return result

    def cache_results(self, query_key: str, results: List[Dict]) -> None:
        """Cache search results."""
        self.cache[query_key] = results

    def get_cached_results(self, query_key: str) -> Optional[List[Dict]]:
        """Get cached results."""
        return self.cache.get(query_key)

    def clear_cache(self) -> None:
        """Clear the cache."""
        self.cache.clear()

    def get_fallback_status(self) -> Dict[str, Any]:
        """Get current fallback status."""
        return {
            "fallback_active": self.fallback_active,
            "fallback_reason": self.fallback_reason,
            "strategy": self.strategy.value,
            "cache_size": len(self.cache),
            "has_primary": self.primary_db is not None,
            "has_secondary": self.secondary_db is not None,
            "has_offline_fallback": self.offline_fallback is not None,
        }

    async def reset_fallback(self) -> None:
        """Reset fallback state and try primary again."""
        logger.info("Resetting fallback state")
        self.fallback_active = False
        self.fallback_reason = None
