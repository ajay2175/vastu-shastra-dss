"""Vector database health check functionality with fast timeout and retry logic."""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health check status indicators."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class HealthChecker:
    """
    Health checker for vector databases.
    Monitors availability and performance.
    """

    def __init__(self, check_interval: int = 300):
        """
        Initialize health checker.

        Args:
            check_interval: Seconds between health checks
        """
        self.check_interval = check_interval
        self.last_check = None
        self.health_status = {}
        self.check_history = []
        self.max_history = 100

    async def check_adapter(self, adapter: Any) -> Dict[str, Any]:
        """
        Check health of a database adapter.

        Args:
            adapter: Database adapter to check

        Returns:
            Health status dictionary
        """
        try:
            health = await adapter.health_check()
            stats = await adapter.get_stats()

            status = {
                "timestamp": datetime.now().isoformat(),
                "adapter": adapter.__class__.__name__,
                "status": health.get("status", "unknown"),
                "health": health,
                "stats": stats,
                "response_time_ms": self._get_response_time(),
            }

            return status
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "timestamp": datetime.now().isoformat(),
                "adapter": adapter.__class__.__name__,
                "status": "error",
                "error": str(e),
            }

    async def check_multiple(self, adapters: List[Any]) -> Dict[str, Any]:
        """
        Check health of multiple adapters concurrently.

        Args:
            adapters: List of database adapters

        Returns:
            Combined health status
        """
        tasks = [self.check_adapter(adapter) for adapter in adapters]
        results = await asyncio.gather(*tasks)

        combined_status = {
            "timestamp": datetime.now().isoformat(),
            "checks": results,
            "overall_status": self._determine_overall_status(results),
            "healthy_count": sum(1 for r in results if r.get("status") == "healthy"),
            "unhealthy_count": sum(1 for r in results if r.get("status") != "healthy"),
        }

        self._record_check(combined_status)
        return combined_status

    def _determine_overall_status(self, results: List[Dict]) -> str:
        """Determine overall status from individual checks."""
        statuses = [r.get("status", "unknown") for r in results]

        if all(s == "healthy" for s in statuses):
            return "healthy"
        elif any(s == "healthy" for s in statuses):
            return "degraded"
        else:
            return "unhealthy"

    def _get_response_time(self) -> float:
        """Get response time in milliseconds."""
        # Placeholder - would measure actual response time
        return 10.0

    def _record_check(self, status: Dict) -> None:
        """Record health check result."""
        self.health_status = status
        self.check_history.append(status)

        # Keep only recent history
        if len(self.check_history) > self.max_history:
            self.check_history.pop(0)

        self.last_check = datetime.now()

    def get_status(self) -> Dict[str, Any]:
        """Get current health status."""
        return self.health_status

    def get_history(self, limit: Optional[int] = None) -> List[Dict]:
        """
        Get health check history.

        Args:
            limit: Maximum number of records to return

        Returns:
            List of health check records
        """
        history = self.check_history

        if limit:
            history = history[-limit:]

        return history

    def is_healthy(self) -> bool:
        """Check if overall status is healthy."""
        return self.health_status.get("overall_status") == "healthy"

    def is_degraded(self) -> bool:
        """Check if status is degraded."""
        return self.health_status.get("overall_status") == "degraded"

    def get_unhealthy_adapters(self) -> List[str]:
        """Get list of unhealthy adapters."""
        checks = self.health_status.get("checks", [])
        return [c.get("adapter") for c in checks if c.get("status") != "healthy"]

    async def continuous_monitoring(self, adapters: List[Any]) -> None:
        """
        Continuously monitor database health.

        Args:
            adapters: List of adapters to monitor
        """
        while True:
            try:
                await self.check_multiple(adapters)
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Continuous monitoring error: {e}")
                await asyncio.sleep(self.check_interval)


class FastHealthChecker:
    """
    Fast health checker with quick timeout and retry logic.
    Optimized for critical VDB availability checks.
    """

    def __init__(self, timeout_seconds: float = 2.0, max_retries: int = 3):
        """
        Initialize fast health checker.

        Args:
            timeout_seconds: Timeout for each health check (default 2s)
            max_retries: Maximum retries on failure (default 3)
        """
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.last_check_time = None
        self.check_cache = {}  # vdb_name -> (status, timestamp)

    async def check_vdb_health(
        self, vdb_name: str, check_fn: Callable, use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Check VDB health with fast timeout and retry logic.

        Args:
            vdb_name: Name of VDB service
            check_fn: Async function that performs health check
            use_cache: Use cached result if available (default True)

        Returns:
            Health check result
        """
        # Try cache first
        if use_cache and vdb_name in self.check_cache:
            cached_status, cached_time = self.check_cache[vdb_name]
            # Cache valid for 60 seconds
            if (datetime.now() - cached_time).total_seconds() < 60:
                logger.debug(f"Using cached health status for {vdb_name}")
                return cached_status

        # Try health check with retries
        for attempt in range(self.max_retries):
            try:
                logger.debug(f"Health check for {vdb_name} (attempt {attempt + 1}/{self.max_retries})")

                # Execute health check with timeout
                result = await asyncio.wait_for(check_fn(), timeout=self.timeout_seconds)

                # Cache successful result
                status = {
                    "vdb_name": vdb_name,
                    "status": HealthStatus.HEALTHY.value,
                    "timestamp": datetime.now().isoformat(),
                    "attempts": attempt + 1,
                    "success": True,
                }

                self.check_cache[vdb_name] = (status, datetime.now())
                return status

            except asyncio.TimeoutError:
                logger.warning(f"{vdb_name} health check timeout (attempt {attempt + 1}/{self.max_retries})")
                # Exponential backoff before retry
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(0.1 * (2 ** attempt))

            except Exception as e:
                logger.warning(
                    f"{vdb_name} health check failed: {e} (attempt {attempt + 1}/{self.max_retries})"
                )
                # Exponential backoff before retry
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(0.1 * (2 ** attempt))

        # All retries exhausted
        status = {
            "vdb_name": vdb_name,
            "status": HealthStatus.UNHEALTHY.value,
            "timestamp": datetime.now().isoformat(),
            "attempts": self.max_retries,
            "success": False,
        }

        self.check_cache[vdb_name] = (status, datetime.now())
        return status

    async def check_multiple_vdbs(
        self,
        checks: Dict[str, Callable],
        timeout_per_check: Optional[float] = None,
    ) -> Dict[str, Dict[str, Any]]:
        """
        Check multiple VDBs concurrently with fast timeout.

        Args:
            checks: Dict of {vdb_name: check_fn}
            timeout_per_check: Override timeout for this check

        Returns:
            Dict of health check results
        """
        timeout = timeout_per_check or self.timeout_seconds

        # Run all checks concurrently
        tasks = {
            vdb_name: self.check_vdb_health(vdb_name, check_fn)
            for vdb_name, check_fn in checks.items()
        }

        try:
            results = await asyncio.wait_for(
                asyncio.gather(*tasks.values(), return_exceptions=True),
                timeout=timeout + 1,  # Allow slightly more than individual timeout
            )

            return {vdb_name: result for vdb_name, result in zip(tasks.keys(), results)}

        except asyncio.TimeoutError:
            logger.error("Multiple VDB health check timeout")
            return {
                vdb_name: {
                    "vdb_name": vdb_name,
                    "status": HealthStatus.UNKNOWN.value,
                    "timestamp": datetime.now().isoformat(),
                    "error": "Health check timeout",
                }
                for vdb_name in checks.keys()
            }

    def get_overall_status(self, health_results: Dict[str, Dict[str, Any]]) -> str:
        """Determine overall system health status."""
        statuses = [r.get("status", HealthStatus.UNKNOWN.value) for r in health_results.values()]

        if all(s == HealthStatus.HEALTHY.value for s in statuses):
            return HealthStatus.HEALTHY.value
        elif any(s == HealthStatus.HEALTHY.value for s in statuses):
            return HealthStatus.DEGRADED.value
        else:
            return HealthStatus.UNHEALTHY.value

    def clear_cache(self, vdb_name: Optional[str] = None) -> None:
        """
        Clear health check cache.

        Args:
            vdb_name: Clear specific VDB cache, or None for all
        """
        if vdb_name:
            self.check_cache.pop(vdb_name, None)
            logger.debug(f"Cleared cache for {vdb_name}")
        else:
            self.check_cache.clear()
            logger.debug("Cleared all health check cache")
