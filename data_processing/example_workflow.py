"""
Complete workflow example for Vastu Shastra text chunking.

This script demonstrates:
1. Loading extracted texts
2. Intelligent chunking with metadata
3. Quality assurance and reporting
4. Saving chunks for RAG pipeline
"""

import asyncio
import json
from pathlib import Path
from typing import List

# Import from text processor
from text_processor import (
    ExtractedText,
    process_vastu_texts,
    load_chunks_from_jsonl,
    generate_qa_report,
    print_qa_report,
)


async def load_extracted_texts_from_file(
    json_file: Path,
) -> List[ExtractedText]:
    """Load extracted texts from JSON file format"""
    extracted_texts = []

    if json_file.exists():
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Handle both list and dict formats
            items = data if isinstance(data, list) else data.get('texts', [])
            for item in items:
                extracted_texts.append(ExtractedText(**item))

    return extracted_texts


async def workflow_example_1():
    """Example 1: Basic chunking from scratch"""
    print("\n" + "="*70)
    print("WORKFLOW EXAMPLE 1: Basic Chunking from Scratch")
    print("="*70)

    # Create sample extracted texts
    extracted_texts = [
        ExtractedText(
            text="""
            Mayamatam - The Ancient Architecture Treatise

            Chapter 1: Introduction to Vastu Principles

            The science of Vastu encompasses the five elements (panchabhuta) and their
            harmonious integration into architectural design. Each direction carries specific
            cosmic energies that must be respected.

            Verse 1: The North (Uttara) is ruled by Kubera, the lord of wealth. Water
            features in the north enhance prosperity. A well or water body in this direction
            brings abundant resources and positive cash flow to the inhabitants.

            Verse 2: The Northeast (Uttara-Purva) is the brahma sthana, the energy center.
            This corner must remain clean, light, and elevated. Heavy structures here block
            cosmic energy flow and create vastudosha.

            Verse 3: The East (Purva) faces the rising sun, symbolizing new beginnings and
            health. Place windows and doors here for vitality. The east balances vata dosha
            and promotes awakening.

            Verse 4: The Southeast (Aagneya) is the fire corner. This is suitable for
            kitchens and heating systems. Fire element remedies like lamps or copper here
            harmonize this direction.
            """,
            source_file="mayamatam_intro.pdf",
            chapter="Chapter 1: Introduction to Vastu Principles",
            page_number=1,
            confidence=0.95,
        ),
        ExtractedText(
            text="""
            Vastu Purana - Remedial Measures

            Section 2: Correcting Directional Imbalances

            When directional principles are violated, specific remedies restore balance.

            Sloka 15: If the southwest corner houses heavy materials or is depressed,
            place a stone pyramid (shila yantra) to ground earth element energy. Copper
            plates with geometric patterns also stabilize this direction.

            Sloka 16: If north lacks water, install a fountain or aquarium to activate
            wealth principles. The water must flow toward the center, not outward.

            Sloka 17: Temporal considerations affect remedy effectiveness. Perform
            remedial pujas during auspicious muhurtas. The spring equinox (vasant sampat)
            is ideal for earth element balancing.

            Sloka 18: Material selection matters profoundly. North responds to water and
            metals (silver, copper). Northeast requires stone and light materials.
            Construction during certain seasons amplifies remedy power.
            """,
            source_file="vastu_purana_remedies.pdf",
            chapter="Section 2: Correcting Directional Imbalances",
            page_number=45,
            confidence=0.92,
        ),
    ]

    # Process texts
    chunks, qa_report = await process_vastu_texts(
        extracted_texts,
        output_dir=Path("/tmp/vastu_chunks_example"),
        verbose=True,
    )

    return chunks, qa_report


async def workflow_example_2():
    """Example 2: Load chunks from file and analyze"""
    print("\n" + "="*70)
    print("WORKFLOW EXAMPLE 2: Load and Analyze Chunks")
    print("="*70)

    chunks_file = Path("/Users/ajaynawale/vastu_shastra_dss/data/chunks/chunks.jsonl")

    if not chunks_file.exists():
        print(f"⚠️  Chunks file not found: {chunks_file}")
        return

    # Load chunks
    print(f"\n📂 Loading chunks from {chunks_file}")
    chunks = await load_chunks_from_jsonl(chunks_file)
    print(f"✅ Loaded {len(chunks)} chunks")

    # Generate QA report
    qa_report = await generate_qa_report(chunks)
    await print_qa_report(qa_report)

    # Show detailed chunk analysis
    print("\n📋 Chunk Analysis:")
    print(f"\n{'Idx':<4} {'Source':<20} {'Principle':<15} {'Size':<8} {'Tokens':<7} {'Entities':<20}")
    print("-" * 80)

    for chunk in chunks[:10]:
        entity_str = ", ".join(chunk.entities[:2]) if chunk.entities else "—"
        print(f"{chunk.chunk_index:<4} {chunk.source_file:<20} {chunk.principle_type or '—':<15} "
              f"{chunk.char_count:<8} {chunk.token_estimate:<7} {entity_str:<20}")

    return chunks, qa_report


async def workflow_example_3():
    """Example 3: Filter and extract specific principles"""
    print("\n" + "="*70)
    print("WORKFLOW EXAMPLE 3: Filter and Extract Specific Principles")
    print("="*70)

    chunks_file = Path("/Users/ajaynawale/vastu_shastra_dss/data/chunks/chunks.jsonl")

    if not chunks_file.exists():
        print(f"⚠️  Chunks file not found: {chunks_file}")
        return

    chunks = await load_chunks_from_jsonl(chunks_file)

    # Filter by principle type
    principle_types = {}
    for chunk in chunks:
        if chunk.principle_type:
            if chunk.principle_type not in principle_types:
                principle_types[chunk.principle_type] = []
            principle_types[chunk.principle_type].append(chunk)

    print(f"\n🎯 Chunks by Principle Type:")
    for principle, principle_chunks in sorted(principle_types.items()):
        print(f"\n   {principle.upper()}: {len(principle_chunks)} chunks")
        for chunk in principle_chunks[:2]:
            print(f"      • {chunk.chapter or 'N/A'}")
            print(f"        Text: {chunk.text[:80]}...")

    # Filter by entity
    entity_counts = {}
    for chunk in chunks:
        for entity in chunk.entities:
            if entity not in entity_counts:
                entity_counts[entity] = []
            entity_counts[entity].append(chunk)

    print(f"\n🏷️  Top Entities:")
    for entity, entity_chunks in sorted(
        entity_counts.items(),
        key=lambda x: len(x[1]),
        reverse=True
    )[:10]:
        print(f"   {entity}: {len(entity_chunks)} occurrences")


async def workflow_example_4():
    """Example 4: Export for RAG pipeline"""
    print("\n" + "="*70)
    print("WORKFLOW EXAMPLE 4: Export Chunks for RAG Pipeline")
    print("="*70)

    chunks_file = Path("/Users/ajaynawale/vastu_shastra_dss/data/chunks/chunks.jsonl")

    if not chunks_file.exists():
        print(f"⚠️  Chunks file not found: {chunks_file}")
        return

    chunks = await load_chunks_from_jsonl(chunks_file)

    # Create RAG-ready export (text + metadata)
    rag_export = []
    for chunk in chunks:
        rag_item = {
            "id": chunk.chunk_index,
            "text": chunk.text,
            "metadata": {
                "source": chunk.source_file,
                "chapter": chunk.chapter,
                "section": chunk.section,
                "verse_number": chunk.verse_number,
                "is_verse": chunk.is_verse,
                "principle_type": chunk.principle_type,
                "entities": chunk.entities,
                "sanskrit_terms": chunk.sanskrit_terms,
                "confidence": chunk.confidence,
            }
        }
        rag_export.append(rag_item)

    # Save RAG export
    export_file = Path("/tmp/vastu_rag_export.jsonl")
    print(f"\n💾 Saving RAG export to {export_file}")

    with open(export_file, 'w', encoding='utf-8') as f:
        for item in rag_export:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')

    print(f"✅ Exported {len(rag_export)} items")

    # Create sample Qdrant payload
    sample_payload = {
        "collection_name": "vastu_texts_v1",
        "description": "Vastu Shastra classical texts with semantic chunking",
        "chunk_count": len(chunks),
        "vector_dimension": 768,
        "embedding_model": "paraphrase-multilingual-mpnet-base-v2",
        "field_indexes": [
            {
                "field": "principle_type",
                "type": "keyword",
                "description": "Type of Vastu principle"
            },
            {
                "field": "entities",
                "type": "keyword",
                "description": "Extracted entities (directions, doshas, etc)"
            },
            {
                "field": "source_file",
                "type": "keyword",
                "description": "Source document"
            }
        ],
        "sample_chunks": [
            {
                "id": chunk.chunk_index,
                "text": chunk.text[:100],
                "entities": chunk.entities,
                "principle_type": chunk.principle_type,
            }
            for chunk in chunks[:3]
        ]
    }

    config_file = Path("/tmp/vastu_qdrant_config.json")
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(sample_payload, f, ensure_ascii=False, indent=2)

    print(f"✅ Created Qdrant configuration: {config_file}")


async def main():
    """Run all workflow examples"""

    print("\n" + "█" * 70)
    print("VASTU SHASTRA TEXT PROCESSOR - WORKFLOW EXAMPLES")
    print("█" * 70)

    # Run examples
    try:
        # Example 1: Fresh chunking
        await workflow_example_1()

        # Example 2: Load and analyze
        await workflow_example_2()

        # Example 3: Filter by principles/entities
        await workflow_example_3()

        # Example 4: Export for RAG
        await workflow_example_4()

        print("\n" + "█" * 70)
        print("✅ ALL EXAMPLES COMPLETED")
        print("█" * 70 + "\n")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
