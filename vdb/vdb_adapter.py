"""
Akymatech VDB Adapter with graceful degradation.
Implements try-optional pattern for external VDB services.
Core Vastu system always works; VDB enhancements are optional.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class VDBStatus(Enum):
    """VDB status indicators."""

    OPERATIONAL = "operational"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"
    UNKNOWN = "unknown"


@dataclass
class VDBQueryResult:
    """Result of a VDB query with metadata."""

    data: List[Dict[str, Any]] = field(default_factory=list)
    source: str = "unknown"  # 'jyotish', 'ayurveda', 'cache', 'fallback'
    query_time_ms: float = 0.0
    status: VDBStatus = VDBStatus.UNKNOWN
    error: Optional[str] = None
    used_vdb: bool = False
    fallback_used: bool = False
    cache_hit: bool = False


@dataclass
class VDBMetadata:
    """Metadata tracking for VDB usage."""

    vdbs_attempted: List[str] = field(default_factory=list)
    vdbs_available: List[str] = field(default_factory=list)
    vdbs_failed: List[str] = field(default_factory=list)
    total_query_time_ms: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    enhancement_level: str = "core_only"  # 'core_only', 'partial', 'full'


class AkymatechVDBAdapter:
    """
    Adapter for Akymatech VDB services (Jyotish and Ayurveda).
    Implements try-optional pattern with graceful degradation.
    """

    def __init__(
        self,
        jyotish_url: Optional[str] = None,
        ayurveda_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout_seconds: float = 2.0,
        max_retries: int = 2,
        cache_enabled: bool = True,
        cache_ttl_minutes: int = 60,
    ):
        """
        Initialize Akymatech VDB Adapter.

        Args:
            jyotish_url: Base URL for Jyotish VDB endpoint
            ayurveda_url: Base URL for Ayurveda VDB endpoint
            api_key: API key for authentication
            timeout_seconds: Timeout for VDB queries (default 2s)
            max_retries: Max retries on failure (default 2)
            cache_enabled: Enable result caching (default True)
            cache_ttl_minutes: Cache TTL in minutes (default 60)
        """
        self.jyotish_url = jyotish_url or "https://api.akymatech.dev/jyotish"
        self.ayurveda_url = ayurveda_url or "https://api.akymatech.dev/ayurveda"
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.cache_enabled = cache_enabled
        self.cache_ttl_minutes = cache_ttl_minutes

        # State tracking
        self.jyotish_healthy = False
        self.ayurveda_healthy = False
        self.last_health_check = None
        self.health_check_interval = 300  # seconds

        # Result cache: {query_hash: (result, timestamp)}
        self.result_cache: Dict[str, tuple] = {}

        # Statistics
        self.query_stats = {
            "total_queries": 0,
            "successful_queries": 0,
            "failed_queries": 0,
            "cache_hits": 0,
            "jyotish_hits": 0,
            "ayurveda_hits": 0,
            "fallback_used": 0,
        }

    async def check_health(self, force: bool = False) -> Dict[str, VDBStatus]:
        """
        Check health of both VDB services with fast timeout.

        Args:
            force: Force health check even if recently checked

        Returns:
            Dict with status of each VDB
        """
        # Check if we need to re-check (avoid hammering services)
        if (
            not force
            and self.last_health_check
            and (datetime.now() - self.last_health_check).total_seconds() < self.health_check_interval
        ):
            return {
                "jyotish": (
                    VDBStatus.OPERATIONAL if self.jyotish_healthy else VDBStatus.UNAVAILABLE
                ),
                "ayurveda": (
                    VDBStatus.OPERATIONAL if self.ayurveda_healthy else VDBStatus.UNAVAILABLE
                ),
            }

        logger.debug("Performing VDB health checks...")
        self.last_health_check = datetime.now()

        # Check both services concurrently with timeout
        try:
            results = await asyncio.wait_for(
                asyncio.gather(
                    self._check_single_vdb("jyotish", self.jyotish_url),
                    self._check_single_vdb("ayurveda", self.ayurveda_url),
                    return_exceptions=True,
                ),
                timeout=max(self.timeout_seconds + 1, 3.0),  # Allow slightly more than query timeout
            )

            # Process results
            jyotish_result, ayurveda_result = results

            # Handle exceptions
            self.jyotish_healthy = isinstance(jyotish_result, bool) and jyotish_result
            self.ayurveda_healthy = isinstance(ayurveda_result, bool) and ayurveda_result

            if isinstance(jyotish_result, Exception):
                logger.warning(f"Jyotish VDB health check failed: {jyotish_result}")
                self.jyotish_healthy = False

            if isinstance(ayurveda_result, Exception):
                logger.warning(f"Ayurveda VDB health check failed: {ayurveda_result}")
                self.ayurveda_healthy = False

        except asyncio.TimeoutError:
            logger.warning("VDB health check timeout")
            self.jyotish_healthy = False
            self.ayurveda_healthy = False
        except Exception as e:
            logger.error(f"VDB health check error: {e}")
            self.jyotish_healthy = False
            self.ayurveda_healthy = False

        return {
            "jyotish": (
                VDBStatus.OPERATIONAL if self.jyotish_healthy else VDBStatus.UNAVAILABLE
            ),
            "ayurveda": (
                VDBStatus.OPERATIONAL if self.ayurveda_healthy else VDBStatus.UNAVAILABLE
            ),
        }

    async def _check_single_vdb(self, vdb_name: str, vdb_url: str) -> bool:
        """Check a single VDB health with quick timeout."""
        try:
            # Simulate quick health check (in production, use aiohttp with timeout)
            # This is a placeholder - actual implementation would hit /health endpoint
            await asyncio.sleep(0.1)  # Simulate network latency
            return True  # Placeholder: would be actual health check result
        except Exception as e:
            logger.debug(f"{vdb_name} health check failed: {e}")
            return False

    async def query_jyotish(
        self,
        query: str,
        query_vector: Optional[List[float]] = None,
        top_k: int = 5,
        fallback: bool = True,
    ) -> VDBQueryResult:
        """
        Query Jyotish VDB with graceful fallback.

        Args:
            query: Query text
            query_vector: Optional vector for semantic search
            top_k: Number of results
            fallback: Enable fallback if VDB unavailable

        Returns:
            VDBQueryResult with data and metadata
        """
        return await self._try_vdb_query(
            vdb_name="jyotish",
            query=query,
            query_vector=query_vector,
            top_k=top_k,
            fallback=fallback,
        )

    async def query_ayurveda(
        self,
        query: str,
        query_vector: Optional[List[float]] = None,
        top_k: int = 5,
        fallback: bool = True,
    ) -> VDBQueryResult:
        """
        Query Ayurveda VDB with graceful fallback.

        Args:
            query: Query text
            query_vector: Optional vector for semantic search
            top_k: Number of results
            fallback: Enable fallback if VDB unavailable

        Returns:
            VDBQueryResult with data and metadata
        """
        return await self._try_vdb_query(
            vdb_name="ayurveda",
            query=query,
            query_vector=query_vector,
            top_k=top_k,
            fallback=fallback,
        )

    async def _try_vdb_query(
        self,
        vdb_name: str,
        query: str,
        query_vector: Optional[List[float]] = None,
        top_k: int = 5,
        fallback: bool = True,
    ) -> VDBQueryResult:
        """
        Try to query a VDB with automatic fallback.
        Core pattern: TRY VDB -> FALLBACK if fails -> NEVER BLOCK

        Args:
            vdb_name: Name of VDB ('jyotish' or 'ayurveda')
            query: Query text
            query_vector: Optional vector
            top_k: Number of results
            fallback: Enable fallback

        Returns:
            VDBQueryResult with data and metadata
        """
        result = VDBQueryResult(source=vdb_name)
        start_time = datetime.now()
        self.query_stats["total_queries"] += 1

        # Step 1: Check cache
        cache_key = self._make_cache_key(vdb_name, query)
        if self.cache_enabled and cache_key in self.result_cache:
            cached_data, cached_time = self.result_cache[cache_key]
            cache_age_minutes = (datetime.now() - cached_time).total_seconds() / 60

            if cache_age_minutes < self.cache_ttl_minutes:
                logger.debug(f"Cache hit for {vdb_name} query: {query[:50]}")
                result.data = cached_data
                result.source = "cache"
                result.cache_hit = True
                result.status = VDBStatus.OPERATIONAL
                result.query_time_ms = (datetime.now() - start_time).total_seconds() * 1000
                self.query_stats["cache_hits"] += 1
                return result

        # Step 2: Try to query VDB
        vdb_url = self.jyotish_url if vdb_name == "jyotish" else self.ayurveda_url

        try:
            # Quick health check first
            is_healthy = (
                self.jyotish_healthy if vdb_name == "jyotish" else self.ayurveda_healthy
            )

            if not is_healthy:
                logger.debug(f"{vdb_name} VDB marked as unhealthy, skipping query")
                if fallback:
                    return await self._fallback_vdb_query(vdb_name, query, result)
                return result

            # Try query with timeout
            try:
                query_result = await asyncio.wait_for(
                    self._execute_vdb_query(vdb_name, vdb_url, query, query_vector, top_k),
                    timeout=self.timeout_seconds,
                )

                if query_result:
                    result.data = query_result
                    result.status = VDBStatus.OPERATIONAL
                    result.used_vdb = True
                    self.query_stats["successful_queries"] += 1

                    if vdb_name == "jyotish":
                        self.query_stats["jyotish_hits"] += 1
                    else:
                        self.query_stats["ayurveda_hits"] += 1

                    # Cache the result
                    if self.cache_enabled:
                        self.result_cache[cache_key] = (query_result, datetime.now())

                    logger.debug(f"Successfully queried {vdb_name} VDB: {len(query_result)} results")
                    return result

            except asyncio.TimeoutError:
                logger.warning(f"{vdb_name} VDB query timeout ({self.timeout_seconds}s)")
                self.query_stats["failed_queries"] += 1
                if fallback:
                    return await self._fallback_vdb_query(vdb_name, query, result)
                return result

        except Exception as e:
            logger.warning(f"{vdb_name} VDB query failed: {e}")
            result.error = str(e)
            self.query_stats["failed_queries"] += 1

            if fallback:
                return await self._fallback_vdb_query(vdb_name, query, result)

        return result

    async def _execute_vdb_query(
        self,
        vdb_name: str,
        vdb_url: str,
        query: str,
        query_vector: Optional[List[float]],
        top_k: int,
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Execute actual VDB query.
        In production, this would use aiohttp to call the VDB endpoint.

        Args:
            vdb_name: VDB name
            vdb_url: VDB URL
            query: Query text
            query_vector: Optional vector
            top_k: Number of results

        Returns:
            Query results or None on failure
        """
        # Placeholder implementation
        # In production, this would:
        # 1. Use aiohttp.ClientSession to make HTTP request
        # 2. Include proper headers with Authorization
        # 3. Parse response JSON
        # 4. Return results with metadata

        logger.debug(
            f"Querying {vdb_name} VDB at {vdb_url}: query='{query}', top_k={top_k}"
        )

        # Simulate query execution
        await asyncio.sleep(0.05)  # Simulate network latency

        # Return mock results for now
        return [
            {
                "id": f"{vdb_name}_result_{i}",
                "score": 1.0 - (i * 0.1),
                "text": f"{vdb_name} result {i} for query: {query}",
            }
            for i in range(min(top_k, 3))
        ]

    async def _fallback_vdb_query(
        self, vdb_name: str, query: str, result: VDBQueryResult
    ) -> VDBQueryResult:
        """
        Fallback when VDB is unavailable.
        Never blocks the consultation - core Vastu always works.

        Args:
            vdb_name: VDB name
            query: Original query
            result: Result object to update

        Returns:
            Updated VDBQueryResult (may be empty)
        """
        logger.info(f"Falling back from {vdb_name} VDB")
        result.fallback_used = True
        result.status = VDBStatus.UNAVAILABLE
        result.source = "fallback"

        # Strategy 1: Return cached results (best effort)
        # In production, could also use stale cache beyond TTL

        # Strategy 2: Return empty results with 'unavailable' flag
        # Core Vastu consultation continues without this enhancement

        self.query_stats["fallback_used"] += 1
        return result

    async def query_both_vdbs(
        self, query: str, query_vector: Optional[List[float]] = None, top_k: int = 5
    ) -> Dict[str, VDBQueryResult]:
        """
        Query both VDBs concurrently with graceful degradation.

        Args:
            query: Query text
            query_vector: Optional vector
            top_k: Number of results

        Returns:
            Dict with results from both VDBs (may be partial/empty on failure)
        """
        results = await asyncio.gather(
            self.query_jyotish(query, query_vector, top_k),
            self.query_ayurveda(query, query_vector, top_k),
            return_exceptions=False,
        )

        return {
            "jyotish": results[0],
            "ayurveda": results[1],
        }

    def _make_cache_key(self, vdb_name: str, query: str) -> str:
        """Create cache key for query."""
        import hashlib

        query_hash = hashlib.md5(query.encode()).hexdigest()[:8]
        return f"{vdb_name}:{query_hash}"

    def get_metadata(self) -> VDBMetadata:
        """Get metadata about current VDB state and usage."""
        vdbs_available = []
        if self.jyotish_healthy:
            vdbs_available.append("jyotish")
        if self.ayurveda_healthy:
            vdbs_available.append("ayurveda")

        # Determine enhancement level
        if len(vdbs_available) == 0:
            enhancement_level = "core_only"
        elif len(vdbs_available) == 1:
            enhancement_level = "partial"
        else:
            enhancement_level = "full"

        return VDBMetadata(
            vdbs_available=vdbs_available,
            enhancement_level=enhancement_level,
            total_query_time_ms=sum(
                v.query_time_ms
                for v in self.result_cache.values()
                if isinstance(v, tuple) and hasattr(v[0], "query_time_ms")
            ),
        )

    def get_stats(self) -> Dict[str, Any]:
        """Get usage statistics."""
        return {
            **self.query_stats,
            "cache_size": len(self.result_cache),
            "cache_enabled": self.cache_enabled,
            "timeout_seconds": self.timeout_seconds,
            "jyotish_healthy": self.jyotish_healthy,
            "ayurveda_healthy": self.ayurveda_healthy,
        }

    def clear_cache(self) -> None:
        """Clear result cache."""
        self.result_cache.clear()
        logger.info("VDB result cache cleared")

    async def close(self) -> None:
        """Close adapter and cleanup resources."""
        self.clear_cache()
        logger.info("VDB adapter closed")


class VDBContext:
    """Context manager for VDB operations with automatic cleanup."""

    def __init__(self, adapter: AkymatechVDBAdapter):
        """Initialize context manager."""
        self.adapter = adapter

    async def __aenter__(self):
        """Enter async context."""
        return self.adapter

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context."""
        await self.adapter.close()
        if exc_type is not None:
            logger.error(f"VDB context error: {exc_val}")
        return False


# Global singleton instance
_vdb_adapter: Optional[AkymatechVDBAdapter] = None


async def get_vdb_adapter(
    jyotish_url: Optional[str] = None,
    ayurveda_url: Optional[str] = None,
    api_key: Optional[str] = None,
) -> AkymatechVDBAdapter:
    """
    Get or create global VDB adapter instance.

    Args:
        jyotish_url: Jyotish VDB URL (if creating new)
        ayurveda_url: Ayurveda VDB URL (if creating new)
        api_key: API key (if creating new)

    Returns:
        VDB adapter instance
    """
    global _vdb_adapter

    if _vdb_adapter is None:
        _vdb_adapter = AkymatechVDBAdapter(
            jyotish_url=jyotish_url,
            ayurveda_url=ayurveda_url,
            api_key=api_key,
        )
        # Perform initial health check
        await _vdb_adapter.check_health(force=True)

    return _vdb_adapter


async def close_vdb_adapter() -> None:
    """Close and cleanup global VDB adapter."""
    global _vdb_adapter

    if _vdb_adapter is not None:
        await _vdb_adapter.close()
        _vdb_adapter = None
