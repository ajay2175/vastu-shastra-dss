"""
Test and validation script for Chroma vector database.
Validates functionality and performs sample queries.
"""

import json
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from vectorization.chroma_vectorizer import ChromaVectorizer


def test_database():
    """Test database connectivity and basic functionality."""
    db_path = Path("vdb/chroma_vastu_db")

    if not db_path.exists():
        print("Error: Database not found at", db_path)
        return False

    print("Initializing vectorizer...")
    vectorizer = ChromaVectorizer(db_path=db_path, device="cpu")

    # Test 1: Get statistics
    print("\n1. Checking Database Statistics...")
    stats = vectorizer.get_stats()
    print(f"   Total Chunks: {stats.total_chunks}")
    print(f"   Chunks Embedded: {stats.chunks_embedded}")
    print(f"   Success Rate: {stats.success_rate:.1f}%")
    print(f"   Database Size: {stats.database_size_mb:.2f} MB")

    if stats.chunks_embedded == 0:
        print("   ERROR: No chunks embedded!")
        return False

    # Test 2: Sample searches
    print("\n2. Testing Similarity Search...")
    test_queries = [
        ("vastu principles and directional alignment", "Directional Principles"),
        ("temple construction and sacred geometry", "Construction"),
        ("remedial measures for vastu defects", "Remedial Measures"),
        ("northeast corner brahma sthana energy", "Energy Centers"),
        ("copper brass metal materials", "Materials"),
    ]

    all_passed = True
    for query, query_type in test_queries:
        results = vectorizer.search(query, top_k=3, threshold=0.2)

        status = "✅ PASS" if len(results) > 0 else "❌ FAIL"
        print(f"\n   {status} - {query_type}")
        print(f"      Query: '{query}'")
        print(f"      Found: {len(results)} results")

        if results:
            top_result = results[0]
            print(f"      Top Match: {top_result['similarity']:.3f} similarity")
            print(f"      Source: {top_result['metadata'].get('source_file', 'N/A')}")
            print(f"      Preview: {top_result['text'][:100]}...")
        else:
            all_passed = False

    # Test 3: Verify metadata
    print("\n3. Verifying Metadata...")
    results = vectorizer.search("vastu", top_k=1)
    if results:
        metadata = results[0]['metadata']
        required_fields = [
            'source_file', 'chapter', 'principle_type',
            'is_verse', 'char_count', 'token_estimate'
        ]

        missing = [f for f in required_fields if f not in metadata]
        if missing:
            print(f"   ❌ Missing fields: {missing}")
            all_passed = False
        else:
            print("   ✅ All metadata fields present")
            print(f"      Source: {metadata['source_file']}")
            print(f"      Chapter: {metadata['chapter']}")
            print(f"      Principle Type: {metadata['principle_type']}")
            print(f"      Is Verse: {metadata['is_verse']}")
            print(f"      Char Count: {metadata['char_count']}")
            print(f"      Token Estimate: {metadata['token_estimate']}")

    # Test 4: Check index file
    print("\n4. Verifying Index Metadata File...")
    index_file = Path("vdb/vastu_embeddings_index.json")
    if index_file.exists():
        with open(index_file, 'r') as f:
            index_data = json.load(f)

        print("   ✅ Index metadata file found")
        print(f"      Model: {index_data['vectorizer']['model']}")
        print(f"      Embedding Dim: {index_data['vectorizer']['embedding_dimension']}")
        print(f"      Total Chunks: {index_data['statistics']['total_chunks']}")
        print(f"      Database Path: {index_data['database']['path']}")
    else:
        print(f"   ❌ Index file not found: {index_file}")
        all_passed = False

    # Summary
    print("\n" + "="*70)
    if all_passed:
        print("✅ ALL TESTS PASSED")
    else:
        print("❌ SOME TESTS FAILED")
    print("="*70)

    return all_passed


def interactive_search():
    """Interactive search mode for testing queries."""
    db_path = Path("vdb/chroma_vastu_db")

    if not db_path.exists():
        print("Error: Database not found")
        return

    vectorizer = ChromaVectorizer(db_path=db_path, device="cpu")

    print("\nChroma Vector Database - Interactive Search")
    print("Type 'quit' to exit\n")

    while True:
        query = input("Enter search query: ").strip()

        if query.lower() == "quit":
            break

        if not query:
            continue

        results = vectorizer.search(query, top_k=5, threshold=0.2)

        if not results:
            print("No results found.")
        else:
            print(f"\nFound {len(results)} results:\n")
            for i, result in enumerate(results, 1):
                print(f"{i}. Similarity: {result['similarity']:.3f}")
                print(f"   Source: {result['metadata']['source_file']}")
                print(f"   Chapter: {result['metadata']['chapter']}")
                print(f"   Type: {result['metadata']['principle_type']}")
                print(f"   Text: {result['text'][:150]}...\n")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "interactive":
        interactive_search()
    else:
        success = test_database()
        sys.exit(0 if success else 1)
