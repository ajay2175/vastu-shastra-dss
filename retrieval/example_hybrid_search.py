"""
Example usage of the Hybrid Search system.

This demonstrates:
1. Building indices from Vastu documents
2. Performing hybrid searches
3. Analyzing results
4. Performance benchmarking
"""

import asyncio
import json
import logging
from pathlib import Path
import time

from hybrid_retriever import HybridRetriever

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


async def load_documents(chunks_path: Path, limit: int = None) -> list:
    """Load documents from chunks JSONL file."""
    documents = []

    with open(chunks_path) as f:
        for i, line in enumerate(f):
            if limit and i >= limit:
                break

            doc = json.loads(line)
            documents.append({
                "doc_id": f"chunk_{doc.get('chunk_index', i)}_{doc['source_file']}",
                "text": doc['text'],
                "metadata": {
                    "source": doc['source_file'],
                    "chapter": doc.get('chapter'),
                    "section": doc.get('section'),
                    "type": doc.get('principle_type'),
                    "entities": doc.get('entities', []),
                    "confidence": doc.get('confidence', 0.0),
                }
            })

    logger.info(f"Loaded {len(documents)} documents")
    return documents


async def load_kg(kg_path: Path) -> dict:
    """Load knowledge graph."""
    with open(kg_path) as f:
        kg_data = json.load(f)

    logger.info(f"Loaded KG with {len(kg_data.get('nodes', []))} nodes and {len(kg_data.get('edges', []))} edges")
    return kg_data


async def example_basic_search():
    """Example 1: Basic hybrid search."""
    print("\n" + "="*80)
    print("EXAMPLE 1: Basic Hybrid Search")
    print("="*80)

    # Initialize retriever
    retriever = HybridRetriever(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        db_path="./data/embeddings",
        index_path=Path("./data/bm25_index.json"),
        kg_path=Path("./data/kg/vastu_seed_kg.json"),
        dense_weight=0.5,
        sparse_weight=0.5
    )

    # Load data
    documents = await load_documents(Path("./data/chunks/chunks.jsonl"))
    kg_data = await load_kg(Path("./data/kg/vastu_seed_kg.json"))

    # Initialize and index
    await retriever.initialize(kg_data=kg_data)
    await retriever.index_documents(documents)

    # Perform search
    query = "north direction benefits"
    print(f"\nQuery: {query}")
    print("-" * 80)

    results = await retriever.search(query, top_k=5)

    print(f"Latency: {results['latency_ms']:.1f}ms")
    print(f"Results found: {len(results['results'])}")
    print(f"Sources: Dense={results['sources']['dense']}, Sparse={results['sources']['sparse']}")
    print()

    for i, result in enumerate(results['results'], 1):
        print(f"{i}. Score: {result['hybrid_score']:.3f}")
        print(f"   ID: {result['doc_id']}")
        print(f"   Sources: {result['sources']}")
        print(f"   Text: {result['text'][:150]}...")
        print()


async def example_query_types():
    """Example 2: Different query types."""
    print("\n" + "="*80)
    print("EXAMPLE 2: Different Query Types")
    print("="*80)

    retriever = HybridRetriever(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        db_path="./data/embeddings",
        index_path=Path("./data/bm25_index.json"),
        dense_weight=0.5,
        sparse_weight=0.5
    )

    documents = await load_documents(Path("./data/chunks/chunks.jsonl"))
    kg_data = await load_kg(Path("./data/kg/vastu_seed_kg.json"))

    await retriever.initialize(kg_data=kg_data)
    await retriever.index_documents(documents)

    # Test different query types
    queries = [
        {
            "type": "Simple Keyword",
            "query": "north direction water",
            "dense": True,
            "sparse": True,
            "entity": False
        },
        {
            "type": "Semantic",
            "query": "how to bring prosperity into the home",
            "dense": True,
            "sparse": False,
            "entity": False
        },
        {
            "type": "Entity-based",
            "query": "vastu dosha remedies",
            "dense": False,
            "sparse": True,
            "entity": False
        },
        {
            "type": "Boolean",
            "query": "north AND water",
            "dense": False,
            "sparse": True,
            "entity": False
        }
    ]

    for test_case in queries:
        print(f"\n{test_case['type'].upper()}")
        print(f"Query: {test_case['query']}")
        print("-" * 80)

        if test_case["type"] == "Boolean":
            results = await retriever.search_boolean(test_case['query'], top_k=3)
        else:
            results = await retriever.search(
                test_case['query'],
                top_k=3,
                use_dense=test_case['dense'],
                use_sparse=test_case['sparse'],
                use_entity=test_case['entity']
            )

        print(f"Latency: {results['latency_ms']:.1f}ms")
        print(f"Results: {len(results['results'])}")

        for i, result in enumerate(results['results'][:2], 1):
            score_key = "hybrid_score" if "hybrid_score" in result else "score"
            print(f"\n  {i}. Score: {result[score_key]:.3f}")
            print(f"     Text: {result['text'][:100]}...")


async def example_performance_benchmark():
    """Example 3: Performance benchmarking."""
    print("\n" + "="*80)
    print("EXAMPLE 3: Performance Benchmark")
    print("="*80)

    retriever = HybridRetriever(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        db_path="./data/embeddings",
        index_path=Path("./data/bm25_index.json"),
        dense_weight=0.5,
        sparse_weight=0.5
    )

    documents = await load_documents(Path("./data/chunks/chunks.jsonl"))
    kg_data = await load_kg(Path("./data/kg/vastu_seed_kg.json"))

    await retriever.initialize(kg_data=kg_data)
    await retriever.index_documents(documents)

    # Benchmark queries
    benchmark_queries = [
        "north direction benefits",
        "how to activate wealth through home design",
        "pitta dosha imbalance remedies",
        "north AND water AND NOT bedroom",
        "kitchen placement southeast fire",
    ]

    print(f"\nBenchmarking {len(benchmark_queries)} queries...")
    print("-" * 80)

    latencies = []
    results_counts = []

    for query in benchmark_queries:
        results = await retriever.search(query, top_k=5)

        latency = results['latency_ms']
        latencies.append(latency)
        results_counts.append(len(results['results']))

        print(f"Query: {query[:50]:<50} | Latency: {latency:>7.1f}ms | Results: {len(results['results'])}")

    print("-" * 80)
    print(f"Average Latency: {sum(latencies)/len(latencies):.1f}ms")
    print(f"Min Latency: {min(latencies):.1f}ms")
    print(f"Max Latency: {max(latencies):.1f}ms")
    print(f"Average Results: {sum(results_counts)/len(results_counts):.1f}")


async def example_index_statistics():
    """Example 4: Index statistics."""
    print("\n" + "="*80)
    print("EXAMPLE 4: Index Statistics")
    print("="*80)

    retriever = HybridRetriever(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        db_path="./data/embeddings",
        index_path=Path("./data/bm25_index.json"),
        dense_weight=0.5,
        sparse_weight=0.5
    )

    documents = await load_documents(Path("./data/chunks/chunks.jsonl"))
    kg_data = await load_kg(Path("./data/kg/vastu_seed_kg.json"))

    await retriever.initialize(kg_data=kg_data)
    await retriever.index_documents(documents)

    stats = retriever.get_stats()

    print("\nSearch Statistics:")
    print(f"  Total searches: {stats['search_stats']['total_searches']}")
    print(f"  Dense hits: {stats['search_stats']['dense_hits']}")
    print(f"  Sparse hits: {stats['search_stats']['sparse_hits']}")
    print(f"  Hybrid results: {stats['search_stats']['hybrid_hits']}")

    print("\nIndex Statistics:")
    print(f"  Dense index size: {stats['dense_index_size']} documents")
    print(f"  Sparse index size: {stats['sparse_index_size']} documents")
    print(f"  KG entities: {stats['kg_entities']}")

    print("\nSparse Index Details:")
    sparse_stats = stats['sparse_index_stats']
    print(f"  Total terms: {sparse_stats['total_terms']}")
    print(f"  Total N-grams: {sparse_stats['total_ngrams']}")
    print(f"  Avg doc length: {sparse_stats['avg_doc_length']:.1f} tokens")


async def example_advanced_ranking():
    """Example 5: Understanding ranking."""
    print("\n" + "="*80)
    print("EXAMPLE 5: Understanding Result Ranking")
    print("="*80)

    retriever = HybridRetriever(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        db_path="./data/embeddings",
        index_path=Path("./data/bm25_index.json"),
        dense_weight=0.5,
        sparse_weight=0.5
    )

    documents = await load_documents(Path("./data/chunks/chunks.jsonl"))
    kg_data = await load_kg(Path("./data/kg/vastu_seed_kg.json"))

    await retriever.initialize(kg_data=kg_data)
    await retriever.index_documents(documents)

    query = "north water wealth"
    print(f"\nQuery: {query}")
    print("-" * 80)

    results = await retriever.search(query, top_k=5)

    print(f"{'Rank':<5} {'Hybrid':<8} {'Dense':<8} {'Sparse':<8} {'Sources':<20} {'Preview':<40}")
    print("-" * 89)

    for i, result in enumerate(results['results'], 1):
        hybrid = result.get('hybrid_score', 0)
        dense = result.get('dense_score', 0)
        sparse = result.get('sparse_score', 0)
        sources = ", ".join(result.get('sources', []))
        preview = result['text'][:35].replace('\n', ' ')

        print(f"{i:<5} {hybrid:<8.3f} {dense:<8.3f} {sparse:<8.3f} {sources:<20} {preview:<40}")


async def main():
    """Run all examples."""
    try:
        await example_basic_search()
        await example_query_types()
        await example_performance_benchmark()
        await example_index_statistics()
        await example_advanced_ranking()

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        logger.info("Make sure you have:")
        logger.info("  - ./data/chunks/chunks.jsonl")
        logger.info("  - ./data/kg/vastu_seed_kg.json")
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())
