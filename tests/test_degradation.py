"""Tests for graceful degradation functionality."""

import pytest
from vdb.graceful_fallback import GracefulFallback, FallbackStrategy
from vdb.adapter import QdrantAdapter, ChromaAdapter


@pytest.fixture
def fallback_system():
    """Create a graceful fallback system."""
    return GracefulFallback(strategy=FallbackStrategy.SECONDARY_FALLBACK)


def test_fallback_initialization(fallback_system):
    """Test fallback system initialization."""
    assert fallback_system is not None
    assert fallback_system.strategy == FallbackStrategy.SECONDARY_FALLBACK
    assert fallback_system.fallback_active is False


def test_set_primary_adapter(fallback_system):
    """Test setting primary adapter."""
    adapter = QdrantAdapter("http://localhost:6333", "test_key", "test_collection")
    fallback_system.set_primary(adapter)
    assert fallback_system.primary_db is not None


def test_set_secondary_adapter(fallback_system):
    """Test setting secondary adapter."""
    adapter = ChromaAdapter("/tmp/chroma", "test_collection")
    fallback_system.set_secondary(adapter)
    assert fallback_system.secondary_db is not None


def test_cache_operations(fallback_system):
    """Test cache operations."""
    results = [{"id": 1, "content": "test"}]
    fallback_system.cache_results("query1", results)

    cached = fallback_system.get_cached_results("query1")
    assert cached == results


def test_fallback_status(fallback_system):
    """Test getting fallback status."""
    status = fallback_system.get_fallback_status()

    assert "fallback_active" in status
    assert "strategy" in status
    assert status["fallback_active"] is False


@pytest.mark.asyncio
async def test_reset_fallback(fallback_system):
    """Test resetting fallback state."""
    fallback_system.fallback_active = True
    fallback_system.fallback_reason = "Test reason"

    await fallback_system.reset_fallback()

    assert fallback_system.fallback_active is False
    assert fallback_system.fallback_reason is None
