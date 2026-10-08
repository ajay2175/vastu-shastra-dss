#!/usr/bin/env python3
"""
Example usage of the Vastu Shastra KG Builder

This script demonstrates how to:
1. Load text chunks
2. Build a knowledge graph
3. Query and analyze the KG
"""

import asyncio
import json
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from data_processing import (
    Chunk,
    build_knowledge_graph,
    load_knowledge_graph,
    get_entity_neighbors,
    search_entities_by_type,
    get_kg_statistics,
)


def create_sample_chunks() -> list:
    """Create sample text chunks for testing"""
    return [
        Chunk(
            id="chunk_1",
            text="""The north direction is associated with the water element and the planet Mercury.
            Placing a water fountain in the north brings prosperity and career advancement.
            The north-east corner is ruled by Brahma and should be kept clean and well-lit.""",
            source="vastu_text_1"
        ),
        Chunk(
            id="chunk_2",
            text="""The bedroom should be in the south-west direction for peaceful sleep.
            A brass mirror or a copper plate in the south-west enhances stability.
            Avoid placing clutter or dead plants in this room.""",
            source="vastu_text_2"
        ),
        Chunk(
            id="chunk_3",
            text="""The kitchen should ideally be in the south-east corner, ruled by the fire element.
            The cooking stove should face east for positive energy flow.
            Red and orange colors are auspicious for the kitchen.""",
            source="vastu_text_3"
        ),
        Chunk(
            id="chunk_4",
            text="""Vata dosha is associated with the air element and the north-west direction.
            Pitta dosha relates to the fire element and the south-east.
            Kapha dosha is connected to water and the north direction.""",
            source="vastu_text_4"
        ),
        Chunk(
            id="chunk_5",
            text="""Remedies for negative vastu include placing crystals, gemstones, and mirrors.
            A crystal ball in the south-west causes enhanced prosperity.
            Wind chimes in the north-west direction improve career opportunities.""",
            source="vastu_text_5"
        ),
        Chunk(
            id="chunk_6",
            text="""The living room should be in the north or east direction for positive energy.
            Place paintings of water bodies in the north to enhance wealth.
            The color blue is recommended for walls in the north-facing rooms.""",
            source="vastu_text_6"
        ),
        Chunk(
            id="chunk_7",
            text="""A pooja room or prayer room must be in the north-east direction of the house.
            Keep this room elevated and ensure natural light enters from the east.
            Avoid storing unnecessary items or clutter in the pooja room.""",
            source="vastu_text_7"
        ),
        Chunk(
            id="chunk_8",
            text="""The main entrance should ideally face north or east for prosperity.
            Doors should be in even numbers and not blocked by obstacles.
            A small water feature near the entrance attracts positive chi.""",
            source="vastu_text_8"
        ),
        Chunk(
            id="chunk_9",
            text="""Five elements balance is crucial: earth, water, fire, air, and ether.
            Each room requires appropriate element representation.
            Imbalance of elements causes health problems and negative emotions.""",
            source="vastu_text_9"
        ),
        Chunk(
            id="chunk_10",
            text="""Central pit or courtyard should be avoided as it disrupts energy flow.
            If present, keep it well-maintained with plants and water features.
            A central pillar creates blockage in positive energy circulation.""",
            source="vastu_text_10"
        )
    ]


async def main():
    """Main execution"""
    print("=" * 70)
    print("Vastu Shastra Knowledge Graph Builder - Example Usage")
    print("=" * 70)

    # Paths
    project_root = Path(__file__).parent
    patterns_path = project_root / "data" / "patterns" / "entity_patterns.json"
    output_kg_path = project_root / "data" / "kg" / "sample_kg.json"

    # Step 1: Create sample chunks
    print("\n1️⃣  Creating sample text chunks...")
    chunks = create_sample_chunks()
    print(f"   ✅ Created {len(chunks)} sample chunks")

    # Step 2: Build knowledge graph
    print("\n2️⃣  Building knowledge graph...")
    try:
        kg = await build_knowledge_graph(chunks, patterns_path, output_kg_path)
        print(f"   ✅ KG built successfully!")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return

    # Step 3: Display KG Statistics
    print("\n3️⃣  Knowledge Graph Statistics")
    print("-" * 70)
    stats = get_kg_statistics(kg)

    print(f"\n   Summary:")
    print(f"   • Total Nodes: {stats['summary']['total_nodes']}")
    print(f"   • Total Edges: {stats['summary']['total_edges']}")
    print(f"   • Average Confidence: {stats['summary']['average_confidence']:.3f}")

    print(f"\n   Entity Types ({len(stats['entity_types'])}): {', '.join(stats['entity_types'][:5])}...")
    print(f"\n   Relation Types: {', '.join(stats['relation_types'][:5])}")

    # Step 4: Sample entity queries
    print("\n4️⃣  Sample Entity Queries")
    print("-" * 70)

    # Query by type
    for entity_type in ["direction", "room", "element"]:
        entities = search_entities_by_type(kg, entity_type)
        if entities:
            print(f"\n   {entity_type.upper()} (sample 3):")
            for entity in entities[:3]:
                print(f"   • {entity.label} (confidence: {entity.confidence:.2f})")

    # Step 5: Entity neighborhood exploration
    print("\n5️⃣  Entity Neighborhood Exploration")
    print("-" * 70)

    # Find and explore a node with connections
    for entity_id, entity in kg.nodes.items():
        neighbors = get_entity_neighbors(kg, entity_id)
        if neighbors['outgoing'] or neighbors['incoming']:
            print(f"\n   Entity: {entity.label} ({entity.type})")
            if neighbors['outgoing']:
                print(f"   • Outgoing connections: {len(neighbors['outgoing'])}")
                for target_id in neighbors['outgoing'][:2]:
                    target = kg.nodes.get(target_id)
                    if target:
                        print(f"     → {target.label}")
            if neighbors['incoming']:
                print(f"   • Incoming connections: {len(neighbors['incoming'])}")
                for source_id in neighbors['incoming'][:2]:
                    source = kg.nodes.get(source_id)
                    if source:
                        print(f"     ← {source.label}")
            break  # Show just one example

    # Step 6: Save results
    print("\n6️⃣  Saving Results")
    print("-" * 70)
    print(f"   ✅ Knowledge Graph saved to: {output_kg_path}")

    # Save statistics
    stats_path = project_root / "data" / "kg" / "kg_statistics.json"
    with open(stats_path, 'w', encoding='utf-8') as f:
        # Convert stats to JSON-serializable format
        json_stats = {
            'summary': stats['summary'],
            'entity_type_count': len(stats['entity_types']),
            'entity_types': stats['entity_types'],
            'relation_type_count': len(stats['relation_types']),
            'relation_types': stats['relation_types'],
            'dense_nodes_sample': [
                {'entity_id': eid, 'connections': count}
                for eid, count in stats['dense_nodes'][:5]
            ]
        }
        json.dump(json_stats, f, indent=2, ensure_ascii=False)
    print(f"   ✅ Statistics saved to: {stats_path}")

    print("\n" + "=" * 70)
    print("✅ Example completed successfully!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
