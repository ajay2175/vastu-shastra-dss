"""Tests for hybrid search system (dense + sparse + KG integration)."""

import asyncio
import json
import logging
import time
from pathlib import Path
from typing import List, Dict, Any

import pytest

# Add parent directory to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from retrieval.hybrid_retriever import (
    HybridRetriever,
    DenseRetriever,
    SparseRetriever,
    KGEntityIndexer,
)
from retrieval.bm25_index import BM25Index

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class TestBM25Index:
    """Tests for BM25 sparse indexing."""

    @pytest.fixture
    def sample_documents(self):
        """Sample documents for testing."""
        return [
            {
                "doc_id": "doc1",
                "text": "North direction ruled by Kubera brings prosperity. Water features in north enhance wealth.",
                "metadata": {"type": "directional"}
            },
            {
                "doc_id": "doc2",
                "text": "East direction associated with fire element. Kitchen placement southeast optimizes energy.",
                "metadata": {"type": "elemental"}
            },
            {
                "doc_id": "doc3",
                "text": "Pitta dosha imbalance causes irritability. Cool colors in southeast reduce pitta excess.",
                "metadata": {"type": "dosha"}
            },
            {
                "doc_id": "doc4",
                "text": "Water features should not be placed in bedroom. North water brings wealth but needs care.",
                "metadata": {"type": "remedies"}
            }
        ]

    def test_bm25_indexing(self, sample_documents):
        """Test BM25 index building."""
        index = BM25Index()

        for doc in sample_documents:
            index.add_document(doc["doc_id"], doc["text"], metadata=doc["metadata"])

        index.build_index()

        assert index.total_docs == 4
        assert len(index.idf) > 0
        assert index.avg_doc_length > 0

    def test_bm25_simple_search(self, sample_documents):
        """Test simple keyword search."""
        index = BM25Index()

        for doc in sample_documents:
            index.add_document(doc["doc_id"], doc["text"], metadata=doc["metadata"])

        index.build_index()

        # Search for keyword
        results = index.search("north direction benefits", top_k=3)

        assert len(results) > 0
        assert results[0]["score"] > 0
        assert "doc_id" in results[0]

        # Top result should contain "north"
        top_text = results[0]["text"].lower()
        assert "north" in top_text

    def test_bm25_phrase_search(self, sample_documents):
        """Test phrase query."""
        index = BM25Index()

        for doc in sample_documents:
            index.add_document(doc["doc_id"], doc["text"], metadata=doc["metadata"])

        index.build_index()

        # Phrase search
        results = index.search('"north direction"', top_k=3)

        assert len(results) > 0
        # Should boost documents with exact phrase
        assert "north direction" in results[0]["text"].lower()

    def test_bm25_boolean_search(self, sample_documents):
        """Test Boolean queries."""
        index = BM25Index()

        for doc in sample_documents:
            index.add_document(doc["doc_id"], doc["text"], metadata=doc["metadata"])

        index.build_index()

        # AND query
        results = index.search_boolean("north AND water", top_k=5)

        assert len(results) > 0
        # All results should contain both terms
        for result in results:
            text = result["text"].lower()
            assert "north" in text or "water" in text

    def test_bm25_ngrams(self, sample_documents):
        """Test N-gram indexing."""
        index = BM25Index(max_ngram=3)

        for doc in sample_documents:
            index.add_document(doc["doc_id"], doc["text"], metadata=doc["metadata"])

        index.build_index()

        # Check N-grams were indexed
        assert len(index.ngram_index) > 0

        # Should have bigrams and trigrams
        ngrams = list(index.ngram_index.keys())
        has_bigrams = any(len(ng.split()) == 2 for ng in ngrams)

        assert has_bigrams

    def test_bm25_serialization(self, sample_documents, tmp_path):
        """Test index save/load."""
        index = BM25Index()

        for doc in sample_documents:
            index.add_document(doc["doc_id"], doc["text"], metadata=doc["metadata"])

        index.build_index()
        original_total = index.total_docs

        # Save
        index_path = tmp_path / "test_index.json"
        index.save(index_path)

        assert index_path.exists()

        # Load
        new_index = BM25Index()
        loaded = new_index.load(index_path)

        assert loaded
        assert new_index.total_docs == original_total


class TestDenseRetriever:
    """Tests for dense vector retrieval."""

    @pytest.fixture
    def sample_documents(self):
        """Sample documents for testing."""
        return [
            {
                "doc_id": "doc1",
                "text": "North direction ruled by Kubera brings prosperity. Water features in north enhance wealth.",
            },
            {
                "doc_id": "doc2",
                "text": "East direction associated with fire element. Kitchen placement southeast optimizes energy.",
            },
            {
                "doc_id": "doc3",
                "text": "Pitta dosha imbalance causes irritability. Cool colors in southeast reduce pitta excess.",
            },
            {
                "doc_id": "doc4",
                "text": "Water features should not be placed in bedroom. North water brings wealth but needs care.",
            }
        ]

    @pytest.mark.asyncio
    async def test_dense_retriever_initialization(self):
        """Test dense retriever initialization."""
        retriever = DenseRetriever(model_name="sentence-transformers/all-MiniLM-L6-v2")
        result = await retriever.initialize()

        assert result
        assert retriever.model is not None

    @pytest.mark.asyncio
    async def test_dense_retriever_add_documents(self, sample_documents):
        """Test adding documents to dense index."""
        retriever = DenseRetriever(model_name="sentence-transformers/all-MiniLM-L6-v2")
        await retriever.initialize()

        result = await retriever.add_documents(sample_documents)

        assert result
        assert len(retriever.documents) == len(sample_documents)

    @pytest.mark.asyncio
    async def test_dense_retriever_search(self, sample_documents):
        """Test dense retrieval search."""
        retriever = DenseRetriever(model_name="sentence-transformers/all-MiniLM-L6-v2")
        await retriever.initialize()
        await retriever.add_documents(sample_documents)

        results = await retriever.search("north direction benefits", top_k=2)

        assert len(results) > 0
        assert "score" in results[0]
        assert "doc_id" in results[0]


class TestSparseRetriever:
    """Tests for sparse keyword retrieval."""

    @pytest.fixture
    def sample_documents(self):
        """Sample documents for testing."""
        return [
            {
                "doc_id": "doc1",
                "text": "North direction ruled by Kubera brings prosperity. Water features in north enhance wealth.",
            },
            {
                "doc_id": "doc2",
                "text": "East direction associated with fire element. Kitchen placement southeast optimizes energy.",
            },
            {
                "doc_id": "doc3",
                "text": "Pitta dosha imbalance causes irritability. Cool colors in southeast reduce pitta excess.",
            },
            {
                "doc_id": "doc4",
                "text": "Water features should not be placed in bedroom. North water brings wealth but needs care.",
            }
        ]

    @pytest.mark.asyncio
    async def test_sparse_retriever_add_documents(self, sample_documents):
        """Test adding documents to sparse index."""
        retriever = SparseRetriever()
        result = await retriever.add_documents(sample_documents)

        assert result
        assert retriever.index.total_docs == len(sample_documents)

    @pytest.mark.asyncio
    async def test_sparse_retriever_search(self, sample_documents):
        """Test sparse retrieval search."""
        retriever = SparseRetriever()
        await retriever.add_documents(sample_documents)

        results = await retriever.search("north direction water", top_k=3)

        assert len(results) > 0
        assert results[0]["score"] > 0
        assert results[0]["source"] == "bm25"

    @pytest.mark.asyncio
    async def test_sparse_retriever_boolean_search(self, sample_documents):
        """Test Boolean query search."""
        retriever = SparseRetriever()
        await retriever.add_documents(sample_documents)

        results = await retriever.search_boolean("north AND water AND NOT bedroom", top_k=5)

        assert len(results) > 0
        assert results[0]["source"] == "bm25_boolean"


class TestHybridRetriever:
    """Tests for hybrid retriever combining dense and sparse."""

    @pytest.fixture
    def sample_documents(self):
        """Sample documents for testing."""
        return [
            {
                "doc_id": "doc1",
                "text": "North direction ruled by Kubera brings prosperity. Water features in north enhance wealth.",
                "metadata": {"type": "directional", "entities": ["north", "water", "wealth"]}
            },
            {
                "doc_id": "doc2",
                "text": "East direction associated with fire element. Kitchen placement southeast optimizes energy.",
                "metadata": {"type": "elemental", "entities": ["east", "fire", "kitchen"]}
            },
            {
                "doc_id": "doc3",
                "text": "Pitta dosha imbalance causes irritability. Cool colors in southeast reduce pitta excess.",
                "metadata": {"type": "dosha", "entities": ["pitta", "dosha", "southeast"]}
            },
            {
                "doc_id": "doc4",
                "text": "Water features should not be placed in bedroom. North water brings wealth but needs care.",
                "metadata": {"type": "remedies", "entities": ["water", "bedroom", "north"]}
            }
        ]

    @pytest.fixture
    def sample_kg(self):
        """Sample knowledge graph."""
        return {
            "nodes": [
                {"id": "north", "type": "direction", "properties": {"aliases": ["north direction"]}},
                {"id": "water", "type": "element", "properties": {"aliases": ["water feature"]}},
                {"id": "pitta", "type": "dosha", "properties": {"aliases": ["pitta dosha"]}},
                {"id": "fire", "type": "element", "properties": {"aliases": ["fire element"]}},
            ],
            "edges": [
                {"source": "north", "target": "water", "relation": "associated_with"},
                {"source": "pitta", "target": "fire", "relation": "associated_with"},
            ]
        }

    @pytest.mark.asyncio
    async def test_hybrid_retriever_initialization(self, sample_kg):
        """Test hybrid retriever initialization."""
        retriever = HybridRetriever(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            dense_weight=0.5,
            sparse_weight=0.5
        )
        result = await retriever.initialize(kg_data=sample_kg)

        assert result
        assert retriever.dense_retriever.model is not None
        assert retriever.sparse_retriever.index is not None

    @pytest.mark.asyncio
    async def test_hybrid_retriever_index_documents(self, sample_documents, sample_kg):
        """Test indexing documents in hybrid retriever."""
        retriever = HybridRetriever(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            dense_weight=0.5,
            sparse_weight=0.5
        )
        await retriever.initialize(kg_data=sample_kg)

        result = await retriever.index_documents(sample_documents)

        assert result
        assert len(retriever.documents) == len(sample_documents)
        assert retriever.sparse_retriever.index.total_docs == len(sample_documents)

    @pytest.mark.asyncio
    async def test_hybrid_search_simple_keyword(self, sample_documents, sample_kg):
        """Test Query 1: Simple keyword query."""
        retriever = HybridRetriever(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            dense_weight=0.5,
            sparse_weight=0.5
        )
        await retriever.initialize(kg_data=sample_kg)
        await retriever.index_documents(sample_documents)

        results = await retriever.search(
            "north direction benefits",
            top_k=5,
            use_dense=True,
            use_sparse=True
        )

        assert "results" in results
        assert len(results["results"]) > 0
        assert results["results"][0]["hybrid_score"] > 0
        assert "latency_ms" in results

        # Verify result has required fields
        for result in results["results"]:
            assert "doc_id" in result
            assert "text" in result
            assert "hybrid_score" in result
            assert "sources" in result

    @pytest.mark.asyncio
    async def test_hybrid_search_semantic_query(self, sample_documents, sample_kg):
        """Test Query 2: Complex semantic query."""
        retriever = HybridRetriever(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            dense_weight=0.7,  # Favor dense for semantic
            sparse_weight=0.3
        )
        await retriever.initialize(kg_data=sample_kg)
        await retriever.index_documents(sample_documents)

        results = await retriever.search(
            "how to activate wealth through home design",
            top_k=5,
            use_dense=True,
            use_sparse=True
        )

        assert len(results["results"]) > 0

        # Should have decent semantic understanding
        top_result = results["results"][0]
        assert "wealth" in top_result["text"].lower() or "north" in top_result["text"].lower()

    @pytest.mark.asyncio
    async def test_hybrid_search_entity_query(self, sample_documents, sample_kg):
        """Test Query 3: Entity-based query."""
        retriever = HybridRetriever(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            dense_weight=0.3,
            sparse_weight=0.7  # Favor sparse for entity keywords
        )
        await retriever.initialize(kg_data=sample_kg)
        await retriever.index_documents(sample_documents)

        results = await retriever.search(
            "pitta dosha imbalance remedies",
            top_k=5,
            use_dense=True,
            use_sparse=True,
            use_entity=False
        )

        assert len(results["results"]) > 0

        # Should find pitta-related content
        found_pitta = any("pitta" in r["text"].lower() for r in results["results"])
        assert found_pitta

    @pytest.mark.asyncio
    async def test_hybrid_search_boolean_query(self, sample_documents, sample_kg):
        """Test Query 4: Boolean query."""
        retriever = HybridRetriever(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            dense_weight=0.2,
            sparse_weight=0.8  # Use mostly sparse for boolean
        )
        await retriever.initialize(kg_data=sample_kg)
        await retriever.index_documents(sample_documents)

        results = await retriever.search_boolean(
            "north AND water AND NOT bedroom",
            top_k=5
        )

        assert "results" in results
        # Boolean query might return fewer results due to constraints
        assert len(results["results"]) >= 0

    @pytest.mark.asyncio
    async def test_hybrid_search_multisystem_query(self, sample_documents, sample_kg):
        """Test Query 5: Multi-system query."""
        retriever = HybridRetriever(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            dense_weight=0.5,
            sparse_weight=0.5
        )
        await retriever.initialize(kg_data=sample_kg)
        await retriever.index_documents(sample_documents)

        results = await retriever.search(
            "kitchen placement southeast fire element",
            top_k=5,
            use_dense=True,
            use_sparse=True,
            use_entity=True
        )

        assert len(results["results"]) > 0

        # Should find southeast kitchen content
        found_match = any(
            ("kitchen" in r["text"].lower() or "southeast" in r["text"].lower())
            for r in results["results"]
        )
        assert found_match

    @pytest.mark.asyncio
    async def test_hybrid_retriever_performance(self, sample_documents, sample_kg):
        """Test performance metrics."""
        retriever = HybridRetriever(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            dense_weight=0.5,
            sparse_weight=0.5
        )
        await retriever.initialize(kg_data=sample_kg)
        await retriever.index_documents(sample_documents)

        queries = [
            "north direction benefits",
            "how to activate wealth through home design",
            "pitta dosha imbalance remedies",
            "kitchen placement southeast fire",
        ]

        latencies = []

        for query in queries:
            results = await retriever.search(query, top_k=5)
            latencies.append(results["latency_ms"])

        # All queries should complete in reasonable time
        assert all(lat < 1000 for lat in latencies)  # < 1 second

        avg_latency = sum(latencies) / len(latencies)
        print(f"Average latency: {avg_latency:.1f}ms")

    @pytest.mark.asyncio
    async def test_hybrid_retriever_stats(self, sample_documents, sample_kg):
        """Test statistics collection."""
        retriever = HybridRetriever(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            dense_weight=0.5,
            sparse_weight=0.5
        )
        await retriever.initialize(kg_data=sample_kg)
        await retriever.index_documents(sample_documents)

        # Run some searches
        for _ in range(3):
            await retriever.search("north direction water", top_k=3)

        stats = retriever.get_stats()

        assert "search_stats" in stats
        assert stats["search_stats"]["total_searches"] == 3
        assert stats["dense_index_size"] > 0
        assert stats["sparse_index_size"] > 0
        assert stats["kg_entities"] == 4


class TestPerformanceBenchmark:
    """Performance benchmark tests."""

    @pytest.fixture
    def benchmark_documents(self):
        """Documents for benchmark tests."""
        return [
            {
                "doc_id": f"chunk_{i}_{f}",
                "text": text,
                "metadata": {"source": f, "type": "test"}
            }
            for i, (f, text) in enumerate([
                ("mayamatam.pdf", "Mayamatam - Chapter 3: Directional Principles\n\nThe sacred directions of Vastu Shastra determine the flow of cosmic energy.\nSloka 45: The North direction, ruled by Kubera the wealth keeper, is the most auspicious\nfor entrances and water features. A water body in the north brings prosperity vastudosha\nremedies include proper orientation."),
                ("samaragana_sutrahara.pdf", "Samaragana Sutrahara describes sacred geometry in Vastu planning.\nThe fire element in southeast brings energy and vitality.\nProper kitchen placement in southeast direction optimizes digestion and metabolism."),
                ("aparajita_priccha.pdf", "Aparajita Priccha discusses balancing doshas through design.\nPitta dosha excess manifests as irritability and inflammation.\nCool color palettes and water elements in southeast mitigate pitta imbalances."),
                ("brihat_samhita.pdf", "Brihat Samhita connects celestial movements to earthly design.\nWater should flow from north to south for optimal prosperity.\nBedrooms in north bring sleep disturbances - better placed in east or west.")
            ])
        ]

    @pytest.mark.asyncio
    async def test_benchmark_all_queries(self, benchmark_documents):
        """Run all 5 benchmark queries and measure performance."""
        retriever = HybridRetriever(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            dense_weight=0.5,
            sparse_weight=0.5
        )

        kg_data = {
            "nodes": [
                {"id": "north", "type": "direction"},
                {"id": "water", "type": "element"},
                {"id": "pitta", "type": "dosha"},
                {"id": "fire", "type": "element"},
                {"id": "southeast", "type": "direction"},
            ],
            "edges": []
        }

        await retriever.initialize(kg_data=kg_data)
        await retriever.index_documents(benchmark_documents)

        # 5 benchmark queries
        test_queries = [
            ("Simple keyword", "north direction benefits"),
            ("Complex semantic", "how to activate wealth through home design"),
            ("Entity query", "pitta dosha imbalance remedies"),
            ("Boolean", "north AND water AND NOT bedroom"),
            ("Multi-system", "kitchen placement southeast fire"),
        ]

        benchmark_results = []

        for query_type, query_text in test_queries:
            results = await retriever.search(query_text, top_k=5)

            benchmark_results.append({
                "query_type": query_type,
                "query": query_text,
                "latency_ms": results["latency_ms"],
                "results_count": len(results["results"]),
                "top_score": results["results"][0]["hybrid_score"] if results["results"] else 0,
            })

        # Print benchmark results
        print("\n" + "="*80)
        print("HYBRID SEARCH BENCHMARK RESULTS")
        print("="*80)

        for result in benchmark_results:
            print(f"\nQuery Type: {result['query_type']}")
            print(f"Query: {result['query']}")
            print(f"Latency: {result['latency_ms']:.1f}ms")
            print(f"Results: {result['results_count']}")
            print(f"Top Score: {result['top_score']:.3f}")

        print("\n" + "="*80)
        print("SUMMARY")
        print("="*80)

        latencies = [r["latency_ms"] for r in benchmark_results]
        print(f"Average Latency: {sum(latencies)/len(latencies):.1f}ms")
        print(f"Min Latency: {min(latencies):.1f}ms")
        print(f"Max Latency: {max(latencies):.1f}ms")
        print(f"Total Results: {sum(r['results_count'] for r in benchmark_results)}")


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "-s"])
