"""Vector database health check functionality."""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


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
