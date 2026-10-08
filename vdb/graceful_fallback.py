"""Graceful fallback mechanism for database failures."""

import asyncio
import logging
from typing import List, Dict, Optional, Any, Callable
from datetime import datetime
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


class ConsultationFallbackManager:
    """
    Manages fallback for Vastu consultations.
    Ensures core consultation always works, VDB enhancements are optional.
    """

    def __init__(self):
        """Initialize consultation fallback manager."""
        self.core_consultation_cache = {}
        self.vdb_enhancement_cache = {}
        self.fallback_active = False
        self.fallback_metrics = {
            "core_only_served": 0,
            "core_with_jyotish": 0,
            "core_with_ayurveda": 0,
            "core_with_both_vdbs": 0,
            "fallback_triggered": 0,
        }

    async def get_consultation_with_vdb_enhancements(
        self,
        consultation_id: str,
        core_consultation_fn: Callable,
        jyotish_fn: Optional[Callable] = None,
        ayurveda_fn: Optional[Callable] = None,
        timeout_seconds: float = 5.0,
    ) -> Dict[str, Any]:
        """
        Get consultation with optional VDB enhancements.
        Core always succeeds; VDBs enhance if available.

        Pattern:
        1. Get core consultation (ALWAYS WORKS)
        2. Try Jyotish enhancement (optional, fast-fail)
        3. Try Ayurveda enhancement (optional, fast-fail)
        4. Merge enhancements with core
        5. Return complete result (always has core at minimum)

        Args:
            consultation_id: Unique consultation ID
            core_consultation_fn: Async function for core consultation
            jyotish_fn: Optional async function for Jyotish enhancement
            ayurveda_fn: Optional async function for Ayurveda enhancement
            timeout_seconds: Timeout for enhancement queries

        Returns:
            Complete consultation with optional enhancements
        """
        result = {
            "consultation_id": consultation_id,
            "timestamp": datetime.now().isoformat(),
            "core_result": None,
            "enhancements": {
                "jyotish": None,
                "ayurveda": None,
            },
            "vdbs_used": [],
            "enhancement_level": "unknown",
            "errors": [],
        }

        # STEP 1: Get core consultation (ALWAYS WORKS - never fails the user)
        try:
            logger.info(f"Getting core consultation for {consultation_id}")
            core_result = await asyncio.wait_for(core_consultation_fn(), timeout=10.0)
            result["core_result"] = core_result
            self.core_consultation_cache[consultation_id] = core_result

        except Exception as e:
            logger.error(f"Core consultation failed: {e}")
            result["errors"].append(f"Core consultation error: {e}")
            # Return early - core consultation must work
            result["enhancement_level"] = "error"
            return result

        # STEP 2: Try Jyotish enhancement (optional, fast-fail)
        if jyotish_fn:
            try:
                logger.debug("Attempting Jyotish enhancement")
                jyotish_result = await asyncio.wait_for(jyotish_fn(), timeout=timeout_seconds)
                result["enhancements"]["jyotish"] = jyotish_result
                result["vdbs_used"].append("jyotish")
                logger.debug("Jyotish enhancement successful")

            except asyncio.TimeoutError:
                logger.warning(f"Jyotish enhancement timeout ({timeout_seconds}s)")
                result["errors"].append("Jyotish enhancement timeout")

            except Exception as e:
                logger.warning(f"Jyotish enhancement failed: {e}")
                result["errors"].append(f"Jyotish error: {e}")

        # STEP 3: Try Ayurveda enhancement (optional, fast-fail)
        if ayurveda_fn:
            try:
                logger.debug("Attempting Ayurveda enhancement")
                ayurveda_result = await asyncio.wait_for(ayurveda_fn(), timeout=timeout_seconds)
                result["enhancements"]["ayurveda"] = ayurveda_result
                result["vdbs_used"].append("ayurveda")
                logger.debug("Ayurveda enhancement successful")

            except asyncio.TimeoutError:
                logger.warning(f"Ayurveda enhancement timeout ({timeout_seconds}s)")
                result["errors"].append("Ayurveda enhancement timeout")

            except Exception as e:
                logger.warning(f"Ayurveda enhancement failed: {e}")
                result["errors"].append(f"Ayurveda error: {e}")

        # STEP 4: Determine enhancement level
        vdbs_count = len(result["vdbs_used"])
        if vdbs_count == 0:
            result["enhancement_level"] = "core_only"
            self.fallback_metrics["core_only_served"] += 1

        elif vdbs_count == 1:
            if "jyotish" in result["vdbs_used"]:
                result["enhancement_level"] = "core_with_jyotish"
                self.fallback_metrics["core_with_jyotish"] += 1
            else:
                result["enhancement_level"] = "core_with_ayurveda"
                self.fallback_metrics["core_with_ayurveda"] += 1

        else:
            result["enhancement_level"] = "core_with_both_vdbs"
            self.fallback_metrics["core_with_both_vdbs"] += 1

        logger.info(
            f"Consultation {consultation_id} complete: "
            f"enhancement_level={result['enhancement_level']}, "
            f"errors={len(result['errors'])}"
        )

        return result

    async def merge_enhancements(
        self, core_result: Dict, enhancements: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Merge VDB enhancements with core consultation.

        Args:
            core_result: Core consultation result
            enhancements: Dict with 'jyotish' and 'ayurveda' enhancements

        Returns:
            Merged result
        """
        merged = {**core_result}

        # Add Jyotish insights if available
        if enhancements.get("jyotish"):
            merged["jyotish_insights"] = enhancements["jyotish"]

        # Add Ayurveda insights if available
        if enhancements.get("ayurveda"):
            merged["ayurveda_insights"] = enhancements["ayurveda"]

        return merged

    def get_fallback_metrics(self) -> Dict[str, Any]:
        """Get fallback and enhancement metrics."""
        total_consultations = sum(self.fallback_metrics.values())

        return {
            **self.fallback_metrics,
            "total_consultations": total_consultations,
            "core_only_percentage": (
                (self.fallback_metrics["core_only_served"] / total_consultations * 100)
                if total_consultations > 0
                else 0
            ),
            "fully_enhanced_percentage": (
                (self.fallback_metrics["core_with_both_vdbs"] / total_consultations * 100)
                if total_consultations > 0
                else 0
            ),
        }
