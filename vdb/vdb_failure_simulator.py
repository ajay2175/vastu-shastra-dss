"""
VDB Failure Simulator for Testing Graceful Degradation

Provides tools to simulate various VDB failure scenarios:
- Timeouts
- Connection errors
- Network failures (DNS, unreachable)
- Service errors (500, etc.)
- Partial failures
- Recovery patterns

Used in degradation testing to verify system resilience.
Author: Claude Haiku 4.5
"""

import asyncio
import logging
from typing import Dict, Optional, Callable, Any
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
import random

logger = logging.getLogger(__name__)


class FailureType(Enum):
    """Types of failures that can be simulated."""

    TIMEOUT = "timeout"
    CONNECTION_ERROR = "connection_error"
    DNS_ERROR = "dns_error"
    SERVICE_UNAVAILABLE = "service_unavailable"
    RATE_LIMIT = "rate_limit"
    PARTIAL_RESPONSE = "partial_response"
    INVALID_RESPONSE = "invalid_response"
    NO_FAILURE = "no_failure"


class FailureMode(Enum):
    """Modes for failure injection."""

    IMMEDIATE = "immediate"  # Fail immediately
    DELAYED = "delayed"  # Fail after delay
    INTERMITTENT = "intermittent"  # Fail randomly
    FLAKY = "flaky"  # Fail first N times, then succeed


@dataclass
class FailureConfig:
    """Configuration for VDB failure simulation."""

    failure_type: FailureType = FailureType.NO_FAILURE
    failure_mode: FailureMode = FailureMode.IMMEDIATE
    delay_ms: float = 0  # For DELAYED mode
    success_rate: float = 0.5  # For INTERMITTENT mode (0-1)
    fail_count: int = 3  # For FLAKY mode: fail first N times
    timeout_seconds: float = 5.0  # Timeout duration for TIMEOUT failures


class VDBFailureSimulator:
    """
    Simulate various VDB failure scenarios.

    Example:
        simulator = VDBFailureSimulator()
        simulator.set_failure_config("jyotish", FailureType.TIMEOUT)

        async def failing_query():
            return await simulator.simulate_failure("jyotish", mock_vdb_func)
    """

    def __init__(self):
        """Initialize the failure simulator."""
        self.vdb_configs: Dict[str, FailureConfig] = {
            "jyotish": FailureConfig(),
            "ayurveda": FailureConfig(),
        }

        # Statistics tracking
        self.stats = {
            "jyotish": {
                "total_queries": 0,
                "failures": 0,
                "successes": 0,
                "timeouts": 0,
                "connection_errors": 0,
            },
            "ayurveda": {
                "total_queries": 0,
                "failures": 0,
                "successes": 0,
                "timeouts": 0,
                "connection_errors": 0,
            },
        }

        # Track flaky failures per VDB
        self.flaky_call_counts: Dict[str, int] = {
            "jyotish": 0,
            "ayurveda": 0,
        }

    def set_failure_config(
        self, vdb_name: str, config: FailureConfig
    ) -> None:
        """Set failure configuration for a VDB."""
        if vdb_name not in self.vdb_configs:
            raise ValueError(f"Unknown VDB: {vdb_name}")

        self.vdb_configs[vdb_name] = config
        logger.info(
            f"Set failure config for {vdb_name}: "
            f"type={config.failure_type.value}, mode={config.failure_mode.value}"
        )

    def set_failure_type(self, vdb_name: str, failure_type: FailureType) -> None:
        """Set failure type for a VDB."""
        self.vdb_configs[vdb_name].failure_type = failure_type

    def set_failure_mode(self, vdb_name: str, failure_mode: FailureMode) -> None:
        """Set failure mode for a VDB."""
        self.vdb_configs[vdb_name].failure_mode = failure_mode

    async def simulate_failure(
        self,
        vdb_name: str,
        vdb_func: Callable,
        *args,
        **kwargs,
    ) -> Any:
        """
        Simulate a VDB failure and execute the function accordingly.

        Args:
            vdb_name: Name of VDB ('jyotish' or 'ayurveda')
            vdb_func: Async function to call if no failure is injected
            *args: Arguments to pass to vdb_func
            **kwargs: Keyword arguments to pass to vdb_func

        Returns:
            Result from vdb_func or raises exception based on failure config
        """
        config = self.vdb_configs.get(vdb_name)
        if not config:
            # Unknown VDB, just call the function
            return await vdb_func(*args, **kwargs)

        # Update statistics
        self.stats[vdb_name]["total_queries"] += 1

        # Check if we should inject a failure
        should_fail = self._should_inject_failure(vdb_name, config)

        if should_fail:
            # Inject the failure
            await self._inject_failure(vdb_name, config)
            self.stats[vdb_name]["failures"] += 1
            return None

        # No failure, execute normally
        try:
            result = await vdb_func(*args, **kwargs)
            self.stats[vdb_name]["successes"] += 1
            return result
        except Exception as e:
            # Unexpected error in the VDB function
            self.stats[vdb_name]["failures"] += 1
            raise

    def _should_inject_failure(
        self, vdb_name: str, config: FailureConfig
    ) -> bool:
        """Determine if a failure should be injected."""
        if config.failure_type == FailureType.NO_FAILURE:
            return False

        if config.failure_mode == FailureMode.IMMEDIATE:
            return True

        if config.failure_mode == FailureMode.DELAYED:
            return True

        if config.failure_mode == FailureMode.INTERMITTENT:
            # Randomly fail based on success_rate
            return random.random() > config.success_rate

        if config.failure_mode == FailureMode.FLAKY:
            # Fail for first N calls, then succeed
            call_count = self.flaky_call_counts.get(vdb_name, 0)
            if call_count < config.fail_count:
                self.flaky_call_counts[vdb_name] = call_count + 1
                return True
            return False

        return False

    async def _inject_failure(
        self, vdb_name: str, config: FailureConfig
    ) -> None:
        """Inject the configured failure."""
        # Handle delay first
        if config.failure_mode == FailureMode.DELAYED:
            delay_sec = config.delay_ms / 1000.0
            await asyncio.sleep(delay_sec)

        # Inject the specific failure type
        if config.failure_type == FailureType.TIMEOUT:
            self.stats[vdb_name]["timeouts"] += 1
            # Simulate timeout by sleeping longer than the timeout period
            await asyncio.sleep(config.timeout_seconds + 1)
            raise TimeoutError(f"{vdb_name} VDB query timed out")

        elif config.failure_type == FailureType.CONNECTION_ERROR:
            self.stats[vdb_name]["connection_errors"] += 1
            raise ConnectionError(
                f"Failed to connect to {vdb_name} VDB: Connection refused"
            )

        elif config.failure_type == FailureType.DNS_ERROR:
            self.stats[vdb_name]["connection_errors"] += 1
            raise ConnectionError(
                f"Failed to resolve {vdb_name} VDB hostname: Name or service not known"
            )

        elif config.failure_type == FailureType.SERVICE_UNAVAILABLE:
            self.stats[vdb_name]["failures"] += 1
            raise Exception(f"{vdb_name} VDB service temporarily unavailable (HTTP 503)")

        elif config.failure_type == FailureType.RATE_LIMIT:
            self.stats[vdb_name]["failures"] += 1
            raise Exception(f"{vdb_name} VDB rate limit exceeded (HTTP 429)")

        elif config.failure_type == FailureType.PARTIAL_RESPONSE:
            # Return incomplete data instead of raising
            return {}

        elif config.failure_type == FailureType.INVALID_RESPONSE:
            # Return malformed data
            return {"malformed": "response", "missing_required": True}

    def get_stats(self, vdb_name: Optional[str] = None) -> Dict[str, Any]:
        """Get failure simulation statistics."""
        if vdb_name:
            return self.stats.get(vdb_name, {})
        return self.stats

    def reset_stats(self, vdb_name: Optional[str] = None) -> None:
        """Reset failure statistics."""
        if vdb_name:
            if vdb_name in self.stats:
                for key in self.stats[vdb_name]:
                    self.stats[vdb_name][key] = 0
                self.flaky_call_counts[vdb_name] = 0
        else:
            for vdb in self.stats:
                for key in self.stats[vdb]:
                    self.stats[vdb][key] = 0
            self.flaky_call_counts = {
                "jyotish": 0,
                "ayurveda": 0,
            }

    def reset_all(self) -> None:
        """Reset all configurations and statistics."""
        for vdb_name in self.vdb_configs:
            self.vdb_configs[vdb_name] = FailureConfig()
        self.reset_stats()

    def get_status(self, vdb_name: Optional[str] = None) -> Dict[str, Any]:
        """Get current failure simulation status."""
        if vdb_name:
            config = self.vdb_configs.get(vdb_name)
            if not config:
                return {}
            return {
                "vdb": vdb_name,
                "failure_type": config.failure_type.value,
                "failure_mode": config.failure_mode.value,
                "stats": self.stats.get(vdb_name, {}),
            }

        # Return status for all VDBs
        status = {}
        for vdb in self.vdb_configs:
            config = self.vdb_configs[vdb]
            status[vdb] = {
                "failure_type": config.failure_type.value,
                "failure_mode": config.failure_mode.value,
                "stats": self.stats.get(vdb, {}),
            }
        return status


class FailureScenarioBuilder:
    """Builder for constructing complex failure scenarios."""

    def __init__(self, simulator: VDBFailureSimulator):
        """Initialize the scenario builder."""
        self.simulator = simulator
        self.scenarios: Dict[str, Dict[str, FailureConfig]] = {}

    def create_scenario(self, name: str) -> "FailureScenarioBuilder":
        """Create a new scenario."""
        self.scenarios[name] = {}
        return self

    def add_vdb_failure(
        self,
        scenario_name: str,
        vdb_name: str,
        failure_type: FailureType,
        failure_mode: FailureMode = FailureMode.IMMEDIATE,
        **kwargs,
    ) -> "FailureScenarioBuilder":
        """Add a VDB failure to a scenario."""
        config = FailureConfig(
            failure_type=failure_type,
            failure_mode=failure_mode,
            **kwargs,
        )

        if scenario_name not in self.scenarios:
            self.scenarios[scenario_name] = {}

        self.scenarios[scenario_name][vdb_name] = config
        return self

    def apply_scenario(self, name: str) -> Dict[str, FailureConfig]:
        """Apply a scenario to the simulator."""
        scenario = self.scenarios.get(name)
        if not scenario:
            raise ValueError(f"Scenario not found: {name}")

        for vdb_name, config in scenario.items():
            self.simulator.set_failure_config(vdb_name, config)

        logger.info(f"Applied scenario: {name}")
        return scenario

    def get_predefined_scenarios(self) -> Dict[str, str]:
        """Get descriptions of predefined failure scenarios."""
        return {
            "both_vdbs_down": "Both Jyotish and Ayurveda VDBs are down",
            "jyotish_down": "Only Jyotish VDB is down",
            "ayurveda_down": "Only Ayurveda VDB is down",
            "both_timeout": "Both VDBs timing out",
            "jyotish_timeout": "Only Jyotish VDB timing out",
            "ayurveda_timeout": "Only Ayurveda VDB timing out",
            "network_failures": "Network-level failures (DNS, connection)",
            "flaky_vdbs": "VDBs fail intermittently",
            "slow_recovery": "VDBs fail then slowly recover",
            "cascading_failures": "Failures cascade between VDBs",
        }

    def setup_predefined_scenario(self, scenario_name: str) -> None:
        """Setup a predefined failure scenario."""
        if scenario_name == "both_vdbs_down":
            self.add_vdb_failure(
                "predefined",
                "jyotish",
                FailureType.CONNECTION_ERROR,
            )
            self.add_vdb_failure(
                "predefined",
                "ayurveda",
                FailureType.CONNECTION_ERROR,
            )

        elif scenario_name == "jyotish_down":
            self.add_vdb_failure(
                "predefined",
                "jyotish",
                FailureType.CONNECTION_ERROR,
            )

        elif scenario_name == "ayurveda_down":
            self.add_vdb_failure(
                "predefined",
                "ayurveda",
                FailureType.CONNECTION_ERROR,
            )

        elif scenario_name == "both_timeout":
            self.add_vdb_failure(
                "predefined",
                "jyotish",
                FailureType.TIMEOUT,
            )
            self.add_vdb_failure(
                "predefined",
                "ayurveda",
                FailureType.TIMEOUT,
            )

        elif scenario_name == "flaky_vdbs":
            self.add_vdb_failure(
                "predefined",
                "jyotish",
                FailureType.CONNECTION_ERROR,
                FailureMode.INTERMITTENT,
                success_rate=0.5,
            )
            self.add_vdb_failure(
                "predefined",
                "ayurveda",
                FailureType.CONNECTION_ERROR,
                FailureMode.INTERMITTENT,
                success_rate=0.5,
            )

        elif scenario_name == "slow_recovery":
            self.add_vdb_failure(
                "predefined",
                "jyotish",
                FailureType.CONNECTION_ERROR,
                FailureMode.FLAKY,
                fail_count=3,
            )
            self.add_vdb_failure(
                "predefined",
                "ayurveda",
                FailureType.CONNECTION_ERROR,
                FailureMode.FLAKY,
                fail_count=2,
            )

        self.apply_scenario("predefined")


# ============================================================================
# Convenience Functions
# ============================================================================


async def test_with_failure(
    failure_type: FailureType,
    vdb_name: str = "jyotish",
    query_func: Optional[Callable] = None,
    num_queries: int = 5,
) -> Dict[str, Any]:
    """
    Convenience function to test a VDB with a specific failure.

    Args:
        failure_type: Type of failure to inject
        vdb_name: VDB to fail ('jyotish' or 'ayurveda')
        query_func: Optional query function to execute
        num_queries: Number of queries to execute

    Returns:
        Results dictionary with success rate and stats
    """
    simulator = VDBFailureSimulator()
    config = FailureConfig(failure_type=failure_type)
    simulator.set_failure_config(vdb_name, config)

    if query_func is None:
        async def default_query():
            return {"data": "test"}

        query_func = default_query

    results = []
    for i in range(num_queries):
        try:
            result = await simulator.simulate_failure(vdb_name, query_func)
            results.append({"success": result is not None, "result": result})
        except Exception as e:
            results.append({"success": False, "error": str(e)})

    stats = simulator.get_stats(vdb_name)
    success_rate = stats["successes"] / stats["total_queries"] * 100

    return {
        "failure_type": failure_type.value,
        "vdb": vdb_name,
        "num_queries": num_queries,
        "success_rate": success_rate,
        "stats": stats,
        "results": results,
    }


if __name__ == "__main__":
    # Example usage
    import asyncio

    async def demo():
        """Demo the VDB failure simulator."""
        logger.info("VDB Failure Simulator Demo")
        logger.info("=" * 80)

        # Test 1: Immediate connection error
        logger.info("\nTest 1: Immediate Connection Error")
        result = await test_with_failure(
            FailureType.CONNECTION_ERROR,
            "jyotish",
            num_queries=5,
        )
        logger.info(f"Success rate: {result['success_rate']}%")

        # Test 2: Intermittent failures
        logger.info("\nTest 2: Intermittent Failures (50% success rate)")
        result = await test_with_failure(
            FailureType.CONNECTION_ERROR,
            "ayurveda",
            num_queries=10,
        )
        logger.info(f"Success rate: {result['success_rate']}%")

        # Test 3: Complex scenario
        logger.info("\nTest 3: Complex Failure Scenario")
        simulator = VDBFailureSimulator()
        builder = FailureScenarioBuilder(simulator)

        # Setup a flaky recovery scenario
        builder.setup_predefined_scenario("slow_recovery")

        async def test_query():
            return {"data": "test_result"}

        successes = 0
        for i in range(10):
            try:
                result1 = await simulator.simulate_failure("jyotish", test_query)
                if result1 is not None:
                    successes += 1
            except Exception:
                pass

        logger.info(f"Recovery scenario - Success rate: {successes}/10 queries")

    asyncio.run(demo())
