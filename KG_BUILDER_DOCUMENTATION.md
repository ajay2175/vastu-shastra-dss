# Vastu Shastra Knowledge Graph Builder

## Overview

The `kg_builder.py` module provides a complete pipeline for building a local Knowledge Graph from extracted Vastu Shastra texts. It implements:

1. **Pattern-based Entity Extraction** - Fast extraction using regex patterns
2. **LLM-assisted Extraction** - Claude Haiku for complex/ambiguous entities
3. **Relation Extraction** - Identifies connections between entities
4. **KG Construction** - Builds graph with validation, deduplication, and indexing
5. **Statistical Analysis** - Comprehensive KG metrics and quality reports

## Architecture

```
Text Chunks
    ↓
Pattern-based Entity Extraction (Fast)
    ↓
LLM-assisted Extraction (Sample-based, Claude Haiku)
    ↓
Combined Entities
    ↓
Relation Extraction
    ↓
Relations
    ↓
KG Construction
    ├─ Deduplication
    ├─ Validation
    ├─ Indexing
    └─ Statistics
    ↓
Local Knowledge Graph (JSON)
```

## Components

### Data Models

#### Entity
Represents a single entity in the knowledge graph.

```python
@dataclass
class Entity:
    id: str                    # Unique identifier (entity_type_normalized_label)
    type: str                  # Entity type (direction, room, dosha, etc.)
    label: str                 # Human-readable label
    aliases: List[str]         # Alternative names
    source_chunks: List[str]   # Chunk IDs where extracted
    confidence: float          # Confidence score (0.0-1.0)
    metadata: Dict             # Additional properties
    description: str           # Optional description
```

#### Relation
Represents a relationship between two entities.

```python
@dataclass
class Relation:
    source_id: str             # Source entity ID
    target_id: str             # Target entity ID
    relation_type: str         # Type of relation
    confidence: float          # Confidence score
    supporting_chunks: List[str]  # Chunks supporting this relation
    bidirectional: bool        # If true, relation is symmetric
    metadata: Dict             # Additional properties
```

#### KnowledgeGraph
Complete graph structure with indices.

```python
@dataclass
class KnowledgeGraph:
    nodes: Dict[str, Entity]   # Entity ID -> Entity
    edges: List[Relation]      # All relations
    metadata: Dict             # Statistics and metadata
    forward_index: Dict        # source_id -> [target_ids]
    backward_index: Dict       # target_id -> [source_ids]
    entity_index: Dict         # entity_type -> {id -> Entity}
```

### PatternLoader

Loads and manages entity extraction patterns from `entity_patterns.json`.

**Features:**
- Loads patterns for 16 entity types
- Compiles regex patterns for efficiency
- Supports case-insensitive and Unicode matching
- Provides confidence scores per entity type

**Usage:**
```python
loader = PatternLoader(Path("data/patterns/entity_patterns.json"))
entity_types = loader.get_entity_types()
patterns = loader.get_patterns_for_type("direction")
config = loader.get_config("direction")
```

### EntityExtractor

Extracts entities using patterns and LLM.

**Pattern-based Extraction:**
```python
extractor = EntityExtractor(pattern_loader, client)
entities = extractor.extract_entities_by_pattern(chunks)
# Returns: Dict[str, List[Entity]]
```

**LLM-assisted Extraction:**
```python
llm_entities = await extractor.extract_entities_with_llm(
    chunks,
    pattern_entities,
    sample_size=10  # Sample 10 chunks for LLM
)
```

**Features:**
- Fast pattern matching (primary)
- Samples chunks for LLM processing (secondary)
- Deduplicates during extraction
- Tracks confidence scores
- Logs extraction statistics

### RelationExtractor

Extracts relations between entities.

**Relation Types:**
- `HAS_ELEMENT` - Entity contains/has element
- `LOCATED_IN` - Entity located in direction/room
- `CAUSES_IMPACT` - Entity causes health/prosperity impact
- `REMEDIED_BY` - Problem remedied by entity
- `CONFLICTS_WITH` - Entities conflict with each other
- `ENHANCES` - Entity enhances another
- `BELONGS_TO` - Entity categorization/hierarchy

**Usage:**
```python
extractor = RelationExtractor(client)
relations = extractor.extract_relations(chunks, entities)
# Returns: List[Relation]
```

### KnowledgeGraphBuilder

Builds complete KG with validation and optimization.

**Features:**
- Entity deduplication (case-insensitive)
- Relation validation (both entities must exist)
- Duplicate relation filtering
- Builds adjacency indices
- Computes comprehensive statistics
- Generates KG metadata

**Usage:**
```python
builder = KnowledgeGraphBuilder()
kg = builder.build_kg(all_entities, relations)
```

## Entity Types (16 Total)

1. **direction** - N, S, E, W, NE, SE, SW, NW
2. **room** - Bedroom, kitchen, living room, pooja room, etc.
3. **dosha** - Vata, pitta, kapha (Ayurvedic principles)
4. **element** - Earth, water, fire, air, ether
5. **remedy** - Crystals, mirrors, plants, lights, etc.
6. **color** - Red, blue, green, yellow, white, black, etc.
7. **health_impact** - Health, wealth, relationships, career, etc.
8. **shape** - Square, circle, triangle, L-shaped, etc.
9. **material** - Marble, wood, glass, copper, brass, etc.
10. **measurement** - Dimensions and distances
11. **time_period** - Morning, evening, spring, summer, etc.
12. **energy** - Chi, prana, cosmic energy, etc.
13. **water_feature** - Fountain, pond, aquarium, etc.
14. **obstacle** - Blockage, clutter, dead plants, etc.
15. **principle** - Balance, harmony, flow, elements, etc.
16. **architectural_element** - Pillar, wall, door, window, etc.

## Relation Types (7 Total)

```
HAS_ELEMENT        | Entity has/contains element
LOCATED_IN         | Entity located in direction/room
CAUSES_IMPACT      | Entity causes impact (health/wealth/etc)
REMEDIED_BY        | Problem remedied by remedy entity
CONFLICTS_WITH     | Entities conflict/incompatible
ENHANCES           | Entity enhances another
BELONGS_TO         | Entity belongs to category/type
```

## Usage Examples

### Basic Pipeline

```python
import asyncio
from pathlib import Path
from data_processing.kg_builder import build_knowledge_graph, Chunk

# Prepare chunks
chunks = [
    Chunk(id="chunk_1", text="The north direction has water element"),
    Chunk(id="chunk_2", text="Place bedroom in south-west for peace"),
]

# Build KG
kg = asyncio.run(
    build_knowledge_graph(
        chunks,
        Path("data/patterns/entity_patterns.json"),
        Path("data/kg/local_kg.json")
    )
)

# Access results
print(f"Nodes: {len(kg.nodes)}")
print(f"Edges: {len(kg.edges)}")
print(f"Average confidence: {kg.metadata['average_confidence']}")
```

### Entity Extraction Only

```python
from data_processing.kg_builder import PatternLoader, EntityExtractor, Chunk

loader = PatternLoader(Path("data/patterns/entity_patterns.json"))
extractor = EntityExtractor(loader)

chunks = [Chunk(id="1", text="north direction water element")]
entities = extractor.extract_entities_by_pattern(chunks)

for entity_type, entity_list in entities.items():
    for entity in entity_list:
        print(f"{entity.label} ({entity.type}): {entity.confidence:.2f}")
```

### Loading and Querying KG

```python
from data_processing.kg_builder import (
    load_knowledge_graph,
    get_entity_neighbors,
    search_entities_by_type,
    get_kg_statistics
)

# Load existing KG
kg = load_knowledge_graph(Path("data/kg/local_kg.json"))

# Query by type
directions = search_entities_by_type(kg, "direction")
print(f"Found {len(directions)} directions")

# Get entity neighbors
neighbors = get_entity_neighbors(kg, "direction_north")
print(f"Outgoing: {neighbors['outgoing']}")
print(f"Incoming: {neighbors['incoming']}")

# Get statistics
stats = get_kg_statistics(kg)
print(f"Top nodes: {stats['dense_nodes'][:5]}")
```

## Configuration

Edit `config/kg_config.json` to customize:

```json
{
  "kg_builder": {
    "entity_extraction": {
      "pattern_based_enabled": true,
      "llm_assisted_enabled": true,
      "llm_sample_size": 10,
      "confidence_threshold": 0.6
    },
    "relation_extraction": {
      "enabled": true,
      "confidence_threshold": 0.5,
      "bidirectional_relations": ["HAS_ELEMENT", "BELONGS_TO"]
    },
    "kg_construction": {
      "deduplication_enabled": true,
      "deduplication_threshold": 0.85,
      "validation_enabled": true
    }
  }
}
```

## Performance Characteristics

### Extraction Speed
- **Pattern-based:** ~1000-2000 entities/second
- **LLM-assisted:** ~5-10 entities/second (sampled)
- **Relation extraction:** ~500-1000 relations/second

### Resource Requirements
- **Memory:** 100-200 MB for 1000-1500 nodes
- **API Calls:** Claude Haiku only for sampled chunks (configurable)
- **Processing Time:** 30-45 minutes for typical corpus

### Target KG Size
- **Nodes:** 1000-1500 entities
- **Edges:** 2000-3000 relations
- **Entity Types:** 16
- **Relation Types:** 7

## Output Files

### local_kg.json
Complete Knowledge Graph in JSON format:
```json
{
  "nodes": {
    "direction_north": {
      "id": "direction_north",
      "type": "direction",
      "label": "north",
      ...
    },
    ...
  },
  "edges": [
    {
      "source_id": "direction_north",
      "target_id": "element_water",
      "relation_type": "HAS_ELEMENT",
      ...
    },
    ...
  ],
  "metadata": {
    "total_nodes": 1234,
    "total_edges": 2567,
    "entity_type_counts": {...},
    "relation_type_counts": {...},
    "average_confidence": 0.823,
    "node_degree_stats": {...}
  },
  "indices": {
    "forward_index": {...},
    "backward_index": {...},
    "entity_index": {...}
  }
}
```

### kg_statistics.json
Summary statistics for KG quality analysis.

## Quality Assurance

### Extraction Validation
1. ✅ Pattern matching with confidence scoring
2. ✅ LLM validation for complex cases
3. ✅ Deduplication of similar entities
4. ✅ Confidence-based filtering

### Relation Validation
1. ✅ Both source and target entities exist
2. ✅ No duplicate relations
3. ✅ Bidirectional consistency
4. ✅ Relation type validation

### KG Validation
1. ✅ No orphaned nodes
2. ✅ Cycle detection
3. ✅ Connectivity analysis
4. ✅ Statistical consistency

## Troubleshooting

### No entities extracted
1. Check entity patterns are loaded
2. Verify text contains pattern matches
3. Lower confidence threshold in config
4. Enable LLM-assisted extraction

### Low confidence scores
1. Adjust pattern-based confidence in patterns.json
2. Increase LLM sample size
3. Check text formatting/encoding

### Missing relations
1. Verify relation patterns are comprehensive
2. Check entity matching (IDs might not match)
3. Increase relation confidence threshold
4. Manually review extracted chunks

## Integration with RAG

The KG can be integrated with Retrieval-Augmented Generation:

```python
# Use KG for narrowing search space
relevant_entities = search_entities_by_type(kg, "remedy")
relevant_chunks = set()
for entity in relevant_entities:
    relevant_chunks.update(entity.source_chunks)

# Narrow RAG search to relevant chunks
search_results = qdrant_search(query, filter_by_ids=relevant_chunks)
```

## Future Enhancements

1. **Hierarchical Entity Types** - Support taxonomy
2. **Entity Properties** - Rich attributes per entity
3. **Weighted Relations** - Relation strength scores
4. **Temporal Relations** - Time-based constraints
5. **Cross-lingual Support** - Sanskrit/Hindi/English
6. **Graph Algorithms** - PageRank, community detection
7. **Visualization** - Interactive graph exploration
8. **Export Formats** - RDF, Neo4j, GraphML

## References

- Entity patterns: `data/patterns/entity_patterns.json`
- Configuration: `config/kg_config.json`
- Example usage: `examples_kg_builder_usage.py`
- Full API: See docstrings in `kg_builder.py`
