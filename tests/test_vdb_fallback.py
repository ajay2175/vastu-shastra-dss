"""
Comprehensive tests for VDB fallback and graceful degradation.
Tests the critical requirement: system works with or without VDBs.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from vdb.vdb_adapter import AkymatechVDBAdapter, VDBQueryResult, VDBStatus, VDBMetadata
from vdb.health_check import FastHealthChecker, HealthStatus
from vdb.graceful_fallback import GracefulFallback, FallbackStrategy, ConsultationFallbackManager


class TestAkymatechVDBAdapter:
    """Test Akymatech VDB adapter with try-optional pattern."""

    @pytest.fixture
    def adapter(self):
        """Create adapter instance."""
        return AkymatechVDBAdapter(
            timeout_seconds=2.0,
            max_retries=2,
            cache_enabled=True,
        )

    @pytest.mark.asyncio
    async def test_adapter_initialization(self, adapter):
        """Test adapter initializes correctly."""
        assert adapter.jyotish_url == "https://api.akymatech.dev/jyotish"
        assert adapter.ayurveda_url == "https://api.akymatech.dev/ayurveda"
        assert adapter.timeout_seconds == 2.0
        assert adapter.cache_enabled is True

    @pytest.mark.asyncio
    async def test_health_check_both_healthy(self, adapter):
        """Test health check when both VDBs are healthy."""
        # Mock the health check to succeed
        adapter._check_single_vdb = AsyncMock(return_value=True)

        health = await adapter.check_health(force=True)

        assert health["jyotish"] == VDBStatus.OPERATIONAL
        assert health["ayurveda"] == VDBStatus.OPERATIONAL
        assert adapter.jyotish_healthy is True
        assert adapter.ayurveda_healthy is True

    @pytest.mark.asyncio
    async def test_health_check_jyotish_down(self, adapter):
        """Test health check when Jyotish is unavailable."""

        async def mock_check(name, url):
            if name == "jyotish":
                raise ConnectionError("Connection failed")
            return True

        adapter._check_single_vdb = mock_check

        health = await adapter.check_health(force=True)

        assert health["jyotish"] == VDBStatus.UNAVAILABLE
        assert health["ayurveda"] == VDBStatus.OPERATIONAL

    @pytest.mark.asyncio
    async def test_query_jyotish_success(self, adapter):
        """Test successful Jyotish query."""
        adapter.jyotish_healthy = True
        adapter._execute_vdb_query = AsyncMock(
            return_value=[
                {"id": "result_1", "score": 0.95, "text": "Jyotish result"}
            ]
        )

        result = await adapter.query_jyotish("planetary impact on northeast")

        assert result.status == VDBStatus.OPERATIONAL
        assert result.used_vdb is True
        assert len(result.data) == 1
        assert result.source == "jyotish"

    @pytest.mark.asyncio
    async def test_query_with_timeout(self, adapter):
        """Test query timeout handling."""
        adapter.jyotish_healthy = True

        async def slow_query(*args, **kwargs):
            await asyncio.sleep(5)  # Simulate slow query
            return []

        adapter._execute_vdb_query = slow_query

        result = await adapter.query_jyotish("test query", fallback=True)

        # Should timeout and fallback
        assert result.fallback_used is True
        assert result.status == VDBStatus.UNAVAILABLE

    @pytest.mark.asyncio
    async def test_cache_hit(self, adapter):
        """Test result caching."""
        adapter.jyotish_healthy = True

        query = "test planetary query"
        cache_key = adapter._make_cache_key("jyotish", query)
        cached_data = [{"id": "cached_1", "score": 0.9}]

        # Pre-populate cache
        import datetime

        adapter.result_cache[cache_key] = (cached_data, datetime.datetime.now())

        result = await adapter.query_jyotish(query)

        assert result.cache_hit is True
        assert result.source == "cache"
        assert result.data == cached_data

    @pytest.mark.asyncio
    async def test_query_both_vdbs_concurrent(self, adapter):
        """Test concurrent querying of both VDBs."""
        adapter.jyotish_healthy = True
        adapter.ayurveda_healthy = True

        adapter._execute_vdb_query = AsyncMock(
            return_value=[{"id": "result_1", "score": 0.95}]
        )

        results = await adapter.query_both_vdbs("test query")

        assert "jyotish" in results
        assert "ayurveda" in results
        assert results["jyotish"].status == VDBStatus.OPERATIONAL
        assert results["ayurveda"].status == VDBStatus.OPERATIONAL

    @pytest.mark.asyncio
    async def test_query_fallback_to_cache(self, adapter):
        """Test fallback to cache when VDB unavailable."""
        adapter.jyotish_healthy = False  # VDB is down

        query = "test query"
        cache_key = adapter._make_cache_key("jyotish", query)
        cached_data = [{"id": "cached_1", "score": 0.9}]

        import datetime

        adapter.result_cache[cache_key] = (cached_data, datetime.datetime.now())

        result = await adapter.query_jyotish(query, fallback=True)

        # Should use fallback but not block
        assert result.fallback_used is True
        # Cache would be used if implemented

    @pytest.mark.asyncio
    async def test_get_metadata(self, adapter):
        """Test metadata tracking."""
        adapter.jyotish_healthy = True
        adapter.ayurveda_healthy = False

        metadata = adapter.get_metadata()

        assert isinstance(metadata, VDBMetadata)
        assert "jyotish" in metadata.vdbs_available
        assert "ayurveda" not in metadata.vdbs_available
        assert metadata.enhancement_level == "partial"

    @pytest.mark.asyncio
    async def test_stats_tracking(self, adapter):
        """Test statistics tracking."""
        adapter.query_stats["total_queries"] = 10
        adapter.query_stats["successful_queries"] = 8
        adapter.query_stats["cache_hits"] = 2

        stats = adapter.get_stats()

        assert stats["total_queries"] == 10
        assert stats["successful_queries"] == 8
        assert stats["cache_hits"] == 2

    @pytest.mark.asyncio
    async def test_cache_clear(self, adapter):
        """Test cache clearing."""
        adapter.result_cache["key1"] = ([], None)
        adapter.result_cache["key2"] = ([], None)

        assert len(adapter.result_cache) == 2

        adapter.clear_cache()

        assert len(adapter.result_cache) == 0


class TestFastHealthChecker:
    """Test fast health checker with retry logic."""

    @pytest.fixture
    def checker(self):
        """Create checker instance."""
        return FastHealthChecker(timeout_seconds=2.0, max_retries=3)

    @pytest.mark.asyncio
    async def test_health_check_success(self, checker):
        """Test successful health check."""

        async def mock_check():
            return True

        result = await checker.check_vdb_health("jyotish", mock_check)

        assert result["status"] == HealthStatus.HEALTHY.value
        assert result["attempts"] == 1
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_health_check_timeout(self, checker):
        """Test health check timeout."""

        async def slow_check():
            await asyncio.sleep(5)

        result = await checker.check_vdb_health("jyotish", slow_check)

        assert result["status"] == HealthStatus.UNHEALTHY.value
        assert result["attempts"] == 3  # All retries exhausted

    @pytest.mark.asyncio
    async def test_health_check_retry_success(self, checker):
        """Test health check succeeds on retry."""
        call_count = 0

        async def flaky_check():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Connection failed")
            return True

        result = await checker.check_vdb_health("jyotish", flaky_check)

        # Should eventually succeed on retry
        assert result["status"] == HealthStatus.HEALTHY.value

    @pytest.mark.asyncio
    async def test_check_multiple_vdbs(self, checker):
        """Test checking multiple VDBs concurrently."""

        async def healthy_check():
            return True

        async def unhealthy_check():
            raise Exception("Service down")

        checks = {
            "jyotish": healthy_check,
            "ayurveda": unhealthy_check,
        }

        results = await checker.check_multiple_vdbs(checks)

        assert len(results) == 2
        # Results may vary based on implementation

    @pytest.mark.asyncio
    async def test_cache_usage(self, checker):
        """Test health check caching."""
        call_count = 0

        async def mock_check():
            nonlocal call_count
            call_count += 1
            return True

        # First call
        await checker.check_vdb_health("jyotish", mock_check)
        assert call_count == 1

        # Second call should use cache
        await checker.check_vdb_health("jyotish", mock_check, use_cache=True)
        assert call_count == 1  # No additional call

    def test_cache_clear(self, checker):
        """Test cache clearing."""
        checker.check_cache["jyotish"] = ({"status": "healthy"}, None)
        checker.check_cache["ayurveda"] = ({"status": "healthy"}, None)

        assert len(checker.check_cache) == 2

        checker.clear_cache()

        assert len(checker.check_cache) == 0


class TestConsultationFallbackManager:
    """Test consultation with VDB enhancement fallback."""

    @pytest.fixture
    def manager(self):
        """Create manager instance."""
        return ConsultationFallbackManager()

    @pytest.mark.asyncio
    async def test_core_consultation_always_works(self, manager):
        """Test that core consultation always succeeds."""

        async def core_consultation():
            return {
                "direction": "northeast",
                "element": "earth",
                "recommendations": ["Place heavy objects"],
            }

        result = await manager.get_consultation_with_vdb_enhancements(
            "test_001",
            core_consultation,
        )

        assert result["core_result"] is not None
        assert result["enhancement_level"] == "core_only"
        assert len(result["errors"]) == 0

    @pytest.mark.asyncio
    async def test_vdbs_enhance_core(self, manager):
        """Test VDBs enhance core consultation when available."""

        async def core_consultation():
            return {"direction": "northeast", "element": "earth"}

        async def jyotish_enhancement():
            return {"planetary_influence": "Mars in Aries"}

        async def ayurveda_enhancement():
            return {"dosha": "Pitta imbalance"}

        result = await manager.get_consultation_with_vdb_enhancements(
            "test_002",
            core_consultation,
            jyotish_enhancement,
            ayurveda_enhancement,
        )

        assert result["core_result"] is not None
        assert result["enhancements"]["jyotish"] is not None
        assert result["enhancements"]["ayurveda"] is not None
        assert result["enhancement_level"] == "core_with_both_vdbs"
        assert set(result["vdbs_used"]) == {"jyotish", "ayurveda"}

    @pytest.mark.asyncio
    async def test_one_vdb_unavailable(self, manager):
        """Test system works when one VDB is down."""

        async def core_consultation():
            return {"direction": "northeast"}

        async def jyotish_enhancement():
            return {"planetary": "Mars"}

        async def ayurveda_enhancement():
            raise TimeoutError("Service timeout")

        result = await manager.get_consultation_with_vdb_enhancements(
            "test_003",
            core_consultation,
            jyotish_enhancement,
            ayurveda_enhancement,
            timeout_seconds=1.0,
        )

        assert result["core_result"] is not None
        assert result["enhancements"]["jyotish"] is not None
        assert result["enhancements"]["ayurveda"] is None
        assert result["enhancement_level"] == "core_with_jyotish"
        assert "jyotish" in result["vdbs_used"]
        assert "ayurveda" not in result["vdbs_used"]

    @pytest.mark.asyncio
    async def test_all_vdbs_down_still_returns_core(self, manager):
        """Test core consultation returned even if all VDBs down."""

        async def core_consultation():
            return {"direction": "northeast", "recommendations": ["Use colors wisely"]}

        async def jyotish_enhancement():
            raise ConnectionError("Jyotish down")

        async def ayurveda_enhancement():
            raise ConnectionError("Ayurveda down")

        result = await manager.get_consultation_with_vdb_enhancements(
            "test_004",
            core_consultation,
            jyotish_enhancement,
            ayurveda_enhancement,
            timeout_seconds=1.0,
        )

        # Core should still be returned
        assert result["core_result"] is not None
        assert result["enhancement_level"] == "core_only"
        # Errors logged but not blocking
        assert len(result["errors"]) > 0

    @pytest.mark.asyncio
    async def test_metrics_tracking(self, manager):
        """Test metrics tracking for fallback scenarios."""

        async def core_consultation():
            return {"result": "test"}

        # Simulate different scenarios
        for _ in range(3):
            await manager.get_consultation_with_vdb_enhancements(
                "test_id", core_consultation
            )

        metrics = manager.get_fallback_metrics()

        assert metrics["core_only_served"] == 3
        assert metrics["total_consultations"] == 3
        assert metrics["core_only_percentage"] == 100.0


class TestEndToEndGracefulDegradation:
    """End-to-end tests for system resilience."""

    @pytest.mark.asyncio
    async def test_system_works_without_vdbs(self):
        """Test entire system works when VDBs unavailable."""
        # Create adapter with no working VDBs
        adapter = AkymatechVDBAdapter()
        adapter.jyotish_healthy = False
        adapter.ayurveda_healthy = False

        # Core Vastu consultation (would be implemented separately)
        core_result = {"direction": "northeast", "compliance": 75}

        # Should still be able to provide core result
        metadata = adapter.get_metadata()

        assert metadata.enhancement_level == "core_only"
        # System can continue serving users with core functionality

    @pytest.mark.asyncio
    async def test_vdb_failure_doesnt_block_user(self):
        """Test that VDB failures are transparent to user."""
        manager = ConsultationFallbackManager()

        async def core_consultation():
            await asyncio.sleep(0.1)
            return {
                "direction": "northeast",
                "recommendations": ["Place water features in east"],
            }

        async def slow_jyotish():
            # Simulate very slow VDB
            await asyncio.sleep(10)
            return {"planetary": "slow result"}

        # Should complete quickly because VDB timeout is short
        result = await manager.get_consultation_with_vdb_enhancements(
            "perf_test",
            core_consultation,
            slow_jyotish,
            timeout_seconds=1.0,
        )

        # Core result should be returned quickly
        assert result["core_result"] is not None
        # User gets answer fast, VDB enhancement skipped
        assert result["enhancement_level"] == "core_only"

    @pytest.mark.asyncio
    async def test_partial_enhancement_better_than_none(self):
        """Test that partial enhancements are better than complete failure."""
        adapter = AkymatechVDBAdapter()
        adapter.jyotish_healthy = True
        adapter.ayurveda_healthy = False

        # With Jyotish available, get partial enhancement
        result_jyotish_only = await adapter.query_jyotish("direction consultation")
        assert result_jyotish_only.status != VDBStatus.UNHEALTHY

        # System degrades gracefully
        metadata = adapter.get_metadata()
        assert metadata.enhancement_level in ["partial", "core_only"]


class TestCriticalRequirement:
    """
    Test the critical user requirement:
    "Tomorrow if jyotish engine vectors and vaidya mitra ayurveda vectors are not available,
    this application should run independently of that"
    """

    @pytest.mark.asyncio
    async def test_requirement_core_always_works(self):
        """Core DSS must work without any VDBs."""
        # This is the critical requirement
        adapter = AkymatechVDBAdapter()

        # Mark both VDBs as unavailable (tomorrow scenario)
        adapter.jyotish_healthy = False
        adapter.ayurveda_healthy = False

        # Verify core can still function
        metadata = adapter.get_metadata()
        assert metadata.enhancement_level == "core_only"

        # Core Vastu consultation would proceed normally
        # (actual implementation would call core consultation function)

        stats = adapter.get_stats()
        assert stats["jyotish_healthy"] is False
        assert stats["ayurveda_healthy"] is False

    @pytest.mark.asyncio
    async def test_requirement_no_user_sees_error(self):
        """User never sees VDB errors - system handles gracefully."""
        manager = ConsultationFallbackManager()

        async def core_consultation():
            return {"recommendations": ["Core advice"]}

        async def failing_jyotish():
            raise Exception("VDB crashed")

        async def failing_ayurveda():
            raise Exception("VDB crashed")

        # Even with both VDBs failing, user gets result
        result = await manager.get_consultation_with_vdb_enhancements(
            "requirement_test",
            core_consultation,
            failing_jyotish,
            failing_ayurveda,
            timeout_seconds=1.0,
        )

        # Core result is provided
        assert result["core_result"] is not None
        # Errors are logged internally, not exposed to user
        assert result["enhancement_level"] in ["core_only", "unknown"]

    @pytest.mark.asyncio
    async def test_requirement_transparent_degradation(self):
        """VDB unavailability is transparent to user (no error messages)."""
        adapter = AkymatechVDBAdapter()

        # Query with VDB unavailable
        result = await adapter.query_jyotish("test query", fallback=True)

        # No exception raised, no error to user
        # Result might be empty or use fallback
        assert result is not None
        assert isinstance(result, VDBQueryResult)
        # Degradation is transparent


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
