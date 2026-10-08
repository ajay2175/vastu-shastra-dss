"""
Vastu Shastra Knowledge Graph Builder

Builds a local Knowledge Graph from extracted Vastu Shastra texts using:
1. Pattern-based entity extraction (fast)
2. LLM-assisted extraction for complex cases (Claude Haiku)
3. Relation extraction with validation
4. KG construction with deduplication and consistency checks
"""

import asyncio
import json
import re
import logging
from dataclasses import dataclass, asdict, field
from typing import List, Dict, Set, Tuple, Optional
from pathlib import Path
from collections import defaultdict
from datetime import datetime
from urllib.parse import quote
import unicodedata

import anthropic

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class Entity:
    """Represents an entity in the knowledge graph"""
    id: str
    type: str
    label: str
    aliases: List[str] = field(default_factory=list)
    source_chunks: List[str] = field(default_factory=list)
    confidence: float = 0.8
    metadata: Dict = field(default_factory=dict)
    description: str = ""

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class Relation:
    """Represents a relation between two entities"""
    source_id: str
    target_id: str
    relation_type: str
    confidence: float = 0.8
    supporting_chunks: List[str] = field(default_factory=list)
    bidirectional: bool = False
    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class Chunk:
    """Represents a text chunk for extraction"""
    id: str
    text: str
    source: str = ""
    timestamp: str = ""


@dataclass
class KnowledgeGraph:
    """Represents the complete knowledge graph"""
    nodes: Dict[str, Entity]
    edges: List[Relation]
    metadata: Dict
    forward_index: Dict[str, List[str]] = field(default_factory=dict)  # source_id -> [target_ids]
    backward_index: Dict[str, List[str]] = field(default_factory=dict)  # target_id -> [source_ids]
    entity_index: Dict[str, Dict[str, Entity]] = field(default_factory=dict)  # entity_type -> {id -> Entity}

    def to_dict(self) -> Dict:
        return {
            'nodes': {k: v.to_dict() for k, v in self.nodes.items()},
            'edges': [e.to_dict() for e in self.edges],
            'metadata': self.metadata,
            'indices': {
                'forward_index': self.forward_index,
                'backward_index': self.backward_index,
                'entity_index': {
                    etype: {k: v.to_dict() for k, v in entities.items()}
                    for etype, entities in self.entity_index.items()
                }
            }
        }


# ============================================================================
# Pattern Loader
# ============================================================================

class PatternLoader:
    """Loads and manages entity extraction patterns"""

    def __init__(self, patterns_path: Path):
        self.patterns_path = patterns_path
        self.patterns = self._load_patterns()
        self.compiled_patterns = self._compile_patterns()

    def _load_patterns(self) -> Dict:
        """Load patterns from JSON file"""
        with open(self.patterns_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _compile_patterns(self) -> Dict[str, Dict]:
        """Compile regex patterns for efficiency"""
        compiled = {}
        for entity_type, config in self.patterns.items():
            compiled[entity_type] = {
                'patterns': [
                    re.compile(pattern, re.IGNORECASE | re.UNICODE)
                    for pattern in config.get('patterns', [])
                ],
                'entity_type': config.get('entity_type', entity_type),
                'core': config.get('core', False),
                'confidence': config.get('confidence', 0.8)
            }
        return compiled

    def get_entity_types(self) -> List[str]:
        """Get all entity types"""
        return list(self.patterns.keys())

    def get_patterns_for_type(self, entity_type: str) -> List:
        """Get compiled patterns for a specific entity type"""
        if entity_type in self.compiled_patterns:
            return self.compiled_patterns[entity_type]['patterns']
        return []

    def get_config(self, entity_type: str) -> Dict:
        """Get configuration for an entity type"""
        return self.compiled_patterns.get(entity_type, {})


# ============================================================================
# Entity Extraction
# ============================================================================

class EntityExtractor:
    """Extracts entities from text chunks"""

    CORE_CONFIDENCE_BOOST = 0.1

    def __init__(self, pattern_loader: PatternLoader, client: Optional[anthropic.Anthropic] = None):
        self.pattern_loader = pattern_loader
        self.client = client or anthropic.Anthropic()
        self.extracted_entities: Dict[str, Set[str]] = defaultdict(set)

    def extract_entities_by_pattern(self, chunks: List[Chunk]) -> Dict[str, List[Entity]]:
        """
        Extract entities using pattern matching (fast path)

        Returns:
            Dictionary mapping entity_type -> List[Entity]
        """
        logger.info("Starting pattern-based entity extraction...")
        entities_dict: Dict[str, List[Entity]] = defaultdict(list)
        entity_ids_seen: Dict[str, Set[str]] = defaultdict(set)

        for chunk in chunks:
            for entity_type in self.pattern_loader.get_entity_types():
                config = self.pattern_loader.get_config(entity_type)
                patterns = config.get('patterns', [])
                base_confidence = config.get('confidence', 0.8)

                for pattern in patterns:
                    matches = pattern.finditer(chunk.text)
                    for match in matches:
                        match_text = match.group(0).strip()
                        entity_id = self._generate_entity_id(entity_type, match_text)

                        # Avoid duplicates within same entity type
                        if entity_id not in entity_ids_seen[entity_type]:
                            entity = Entity(
                                id=entity_id,
                                type=entity_type,
                                label=match_text,
                                source_chunks=[chunk.id],
                                confidence=base_confidence,
                                metadata={'pattern_matched': True}
                            )
                            entities_dict[entity_type].append(entity)
                            entity_ids_seen[entity_type].add(entity_id)
                            self.extracted_entities[entity_type].add(match_text)

        # Log extraction statistics
        total_entities = sum(len(entities) for entities in entities_dict.values())
        logger.info(f"✅ Extracted {total_entities} entities across {len(entities_dict)} types")
        for etype, entities in entities_dict.items():
            logger.info(f"   {etype}: {len(entities)} entities")

        return entities_dict

    async def extract_entities_with_llm(
        self,
        chunks: List[Chunk],
        pattern_entities: Dict[str, List[Entity]],
        sample_size: int = 10
    ) -> Dict[str, List[Entity]]:
        """
        LLM-assisted extraction for ambiguous cases and missed entities

        Args:
            chunks: Text chunks to process
            pattern_entities: Already extracted entities from patterns
            sample_size: Number of chunks to sample for LLM extraction
        """
        logger.info(f"Starting LLM-assisted extraction (sampling {sample_size} chunks)...")

        # Sample chunks for LLM processing
        sample_chunks = chunks[:min(sample_size, len(chunks))]
        additional_entities: Dict[str, List[Entity]] = defaultdict(list)

        prompt_template = """Extract Vastu Shastra-related entities from the following text chunk.

Focus on these entity types:
- Directions: north, south, east, west, northeast, northwest, southeast, southwest
- Rooms: bedroom, kitchen, living room, office, pooja room, bathroom, etc.
- Doshas: vata, pitta, kapha
- Elements: earth, water, fire, air, ether
- Remedies: crystals, gemstones, mirrors, plants, lights, wind chimes
- Colors, health impacts, shapes, materials, measurements, time periods
- Water features, obstacles, principles, architectural elements

Text chunk:
{text}

Return a JSON object with the following structure:
{{
    "entities": [
        {{"label": "entity_name", "type": "entity_type", "confidence": 0.9}}
    ]
}}

Only include entities that are clearly present in the text. If no entities are found, return an empty list."""

        for chunk in sample_chunks:
            try:
                prompt = prompt_template.format(text=chunk.text[:1500])  # Limit to 1500 chars

                response = self.client.messages.create(
                    model="claude-3-5-haiku-20241022",
                    max_tokens=500,
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )

                result_text = response.content[0].text

                # Parse JSON response
                json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group(0))
                    for entity_data in result.get('entities', []):
                        entity_type = entity_data.get('type', 'unknown')
                        label = entity_data.get('label', '')
                        confidence = entity_data.get('confidence', 0.7)

                        if label and entity_type:
                            entity_id = self._generate_entity_id(entity_type, label)

                            # Check if not already extracted
                            if label not in self.extracted_entities[entity_type]:
                                entity = Entity(
                                    id=entity_id,
                                    type=entity_type,
                                    label=label,
                                    source_chunks=[chunk.id],
                                    confidence=confidence,
                                    metadata={'llm_extracted': True}
                                )
                                additional_entities[entity_type].append(entity)
                                self.extracted_entities[entity_type].add(label)

            except (json.JSONDecodeError, anthropic.APIError) as e:
                logger.warning(f"LLM extraction failed for chunk {chunk.id}: {e}")
                continue

        additional_count = sum(len(entities) for entities in additional_entities.values())
        logger.info(f"✅ LLM-assisted extraction added {additional_count} entities")

        return additional_entities

    def _generate_entity_id(self, entity_type: str, label: str) -> str:
        """Generate a unique entity ID"""
        # Normalize the label
        normalized = unicodedata.normalize('NFKD', label.lower())
        normalized = re.sub(r'[^\w\s-]', '', normalized, flags=re.UNICODE)
        normalized = re.sub(r'[-\s]+', '_', normalized.strip())

        return f"{entity_type}_{normalized}"


# ============================================================================
# Relation Extraction
# ============================================================================

class RelationExtractor:
    """Extracts relations between entities"""

    # Define relation patterns
    RELATION_PATTERNS = {
        'HAS_ELEMENT': [
            r'(\w+)\s+(?:is|has|contains|comprised of|made of)\s+(\w+)',
            r'(\w+)\s+element',
        ],
        'LOCATED_IN': [
            r'(?:in|at|within|inside)\s+(?:the\s+)?(\w+)',
            r'(\w+)\s+direction',
        ],
        'CAUSES_IMPACT': [
            r'(\w+)\s+(?:causes|leads to|results in|impacts)\s+(\w+)',
            r'(\w+)\s+(?:affects|influences)\s+(\w+)',
        ],
        'REMEDIED_BY': [
            r'(?:use|place|add|install|put)\s+(\w+)\s+(?:in|at|to)\s+(?:the\s+)?(\w+)',
            r'(\w+)\s+(?:cures|treats|remedies|fixes)\s+(\w+)',
        ],
        'CONFLICTS_WITH': [
            r'(\w+)\s+(?:should not|cannot|must not be|avoid)\s+(?:near|with|next to)\s+(\w+)',
            r'(?:avoid|do not place)\s+(\w+)\s+(?:near|with)\s+(\w+)',
        ],
        'ENHANCES': [
            r'(\w+)\s+(?:enhances|improves|promotes|encourages)\s+(\w+)',
            r'(\w+)\s+(?:is good for|benefits)\s+(\w+)',
        ],
        'BELONGS_TO': [
            r'(\w+)\s+(?:belongs|relates|pertains)\s+to\s+(\w+)',
            r'(\w+)\s+(?:type|kind|category|class)\s+(?:of|to)\s+(\w+)',
        ]
    }

    def __init__(self, client: Optional[anthropic.Anthropic] = None):
        self.client = client or anthropic.Anthropic()
        self.compiled_patterns = self._compile_patterns()

    def _compile_patterns(self) -> Dict[str, List]:
        """Compile relation patterns"""
        compiled = {}
        for relation_type, patterns in self.RELATION_PATTERNS.items():
            compiled[relation_type] = [
                re.compile(pattern, re.IGNORECASE | re.UNICODE)
                for pattern in patterns
            ]
        return compiled

    def extract_relations(
        self,
        chunks: List[Chunk],
        entities: Dict[str, List[Entity]]
    ) -> List[Relation]:
        """
        Extract relations between entities

        Returns:
            List of Relation objects
        """
        logger.info("Starting relation extraction...")

        relations: List[Relation] = []
        entity_map = self._build_entity_map(entities)

        for chunk in chunks:
            for relation_type, patterns in self.compiled_patterns.items():
                for pattern in patterns:
                    matches = pattern.finditer(chunk.text)
                    for match in matches:
                        try:
                            source_text = match.group(1).strip()
                            target_text = match.group(2).strip()

                            # Find matching entities (fuzzy matching)
                            source_id = self._find_entity_id(source_text, entity_map)
                            target_id = self._find_entity_id(target_text, entity_map)

                            if source_id and target_id and source_id != target_id:
                                relation = Relation(
                                    source_id=source_id,
                                    target_id=target_id,
                                    relation_type=relation_type,
                                    confidence=0.75,
                                    supporting_chunks=[chunk.id],
                                    metadata={'pattern_matched': True}
                                )
                                relations.append(relation)
                        except (IndexError, AttributeError):
                            continue

        logger.info(f"✅ Extracted {len(relations)} relations")
        return relations

    def _build_entity_map(self, entities: Dict[str, List[Entity]]) -> Dict[str, str]:
        """Build a map from entity labels to entity IDs (case-insensitive)"""
        entity_map = {}
        for entity_type, entity_list in entities.items():
            for entity in entity_list:
                entity_map[entity.label.lower()] = entity.id
                # Also add aliases
                for alias in entity.aliases:
                    entity_map[alias.lower()] = entity.id
        return entity_map

    def _find_entity_id(self, text: str, entity_map: Dict[str, str]) -> Optional[str]:
        """Find entity ID using fuzzy matching"""
        text_lower = text.lower().strip()

        # Exact match first
        if text_lower in entity_map:
            return entity_map[text_lower]

        # Substring matching
        for entity_label, entity_id in entity_map.items():
            if text_lower in entity_label or entity_label in text_lower:
                return entity_id

        return None


# ============================================================================
# KG Construction & Deduplication
# ============================================================================

class KnowledgeGraphBuilder:
    """Builds and validates the complete knowledge graph"""

    def __init__(self):
        self.deduplication_threshold = 0.85

    def build_kg(
        self,
        all_entities: Dict[str, List[Entity]],
        relations: List[Relation]
    ) -> KnowledgeGraph:
        """
        Build complete KG with deduplication and validation
        """
        logger.info("Building knowledge graph...")

        # Deduplicate entities
        deduplicated_entities = self._deduplicate_entities(all_entities)
        logger.info(f"✅ Deduplicated entities: {len(deduplicated_entities)} unique entities")

        # Build node map
        nodes = {entity.id: entity for entity in deduplicated_entities}

        # Validate and filter relations
        valid_relations = self._validate_relations(relations, nodes)
        logger.info(f"✅ Validated relations: {len(valid_relations)} valid relations")

        # Build indices
        entity_index = self._build_entity_index(nodes)
        forward_index, backward_index = self._build_adjacency_indices(valid_relations)

        # Compute statistics
        metadata = self._compute_metadata(nodes, valid_relations)

        kg = KnowledgeGraph(
            nodes=nodes,
            edges=valid_relations,
            metadata=metadata,
            forward_index=forward_index,
            backward_index=backward_index,
            entity_index=entity_index
        )

        logger.info(f"✅ Knowledge Graph built: {len(nodes)} nodes, {len(valid_relations)} edges")
        return kg

    def _deduplicate_entities(self, all_entities: Dict[str, List[Entity]]) -> List[Entity]:
        """
        Deduplicate entities across types

        Merges similar entities (e.g., 'north' and 'North') into a single entity
        """
        seen_labels = {}
        deduplicated = []

        for entity_type, entities in all_entities.items():
            for entity in entities:
                label_normalized = entity.label.lower().strip()

                if label_normalized not in seen_labels:
                    seen_labels[label_normalized] = entity
                    deduplicated.append(entity)
                else:
                    # Merge with existing entity
                    existing = seen_labels[label_normalized]
                    existing.source_chunks.extend(entity.source_chunks)
                    existing.confidence = max(existing.confidence, entity.confidence)
                    existing.aliases.append(entity.label)

        return deduplicated

    def _validate_relations(self, relations: List[Relation], nodes: Dict[str, Entity]) -> List[Relation]:
        """
        Validate relations - ensure both source and target exist in nodes
        Remove duplicate relations
        """
        valid_relations = []
        seen_relations = set()

        for relation in relations:
            # Check if both entities exist
            if relation.source_id in nodes and relation.target_id in nodes:
                # Check for duplicates
                relation_key = (relation.source_id, relation.target_id, relation.relation_type)
                if relation_key not in seen_relations:
                    valid_relations.append(relation)
                    seen_relations.add(relation_key)

        return valid_relations

    def _build_entity_index(self, nodes: Dict[str, Entity]) -> Dict[str, Dict[str, Entity]]:
        """Build index of entities by type"""
        index: Dict[str, Dict[str, Entity]] = defaultdict(dict)
        for entity in nodes.values():
            index[entity.type][entity.id] = entity
        return dict(index)

    def _build_adjacency_indices(
        self,
        relations: List[Relation]
    ) -> Tuple[Dict[str, List[str]], Dict[str, List[str]]]:
        """Build forward and backward adjacency indices"""
        forward_index: Dict[str, List[str]] = defaultdict(list)
        backward_index: Dict[str, List[str]] = defaultdict(list)

        for relation in relations:
            forward_index[relation.source_id].append(relation.target_id)
            if relation.bidirectional:
                backward_index[relation.source_id].append(relation.target_id)
            backward_index[relation.target_id].append(relation.source_id)

        return dict(forward_index), dict(backward_index)

    def _compute_metadata(
        self,
        nodes: Dict[str, Entity],
        relations: List[Relation]
    ) -> Dict:
        """Compute KG statistics and metadata"""
        entity_types = defaultdict(int)
        relation_types = defaultdict(int)
        total_confidence = 0

        for entity in nodes.values():
            entity_types[entity.type] += 1
            total_confidence += entity.confidence

        for relation in relations:
            relation_types[relation.relation_type] += 1

        avg_confidence = total_confidence / len(nodes) if nodes else 0

        return {
            'timestamp': datetime.now().isoformat(),
            'total_nodes': len(nodes),
            'total_edges': len(relations),
            'entity_type_counts': dict(entity_types),
            'relation_type_counts': dict(relation_types),
            'average_confidence': round(avg_confidence, 3),
            'node_degree_stats': self._compute_degree_stats(nodes, relations)
        }

    def _compute_degree_stats(
        self,
        nodes: Dict[str, Entity],
        relations: List[Relation]
    ) -> Dict:
        """Compute node degree statistics"""
        in_degree = defaultdict(int)
        out_degree = defaultdict(int)

        for relation in relations:
            out_degree[relation.source_id] += 1
            in_degree[relation.target_id] += 1

        degrees = list(in_degree.values()) + list(out_degree.values())

        return {
            'avg_degree': round(sum(degrees) / len(degrees), 2) if degrees else 0,
            'max_in_degree': max(in_degree.values()) if in_degree else 0,
            'max_out_degree': max(out_degree.values()) if out_degree else 0,
        }


# ============================================================================
# Main Pipeline
# ============================================================================

async def build_knowledge_graph(
    chunks: List[Chunk],
    patterns_path: Path,
    output_path: Path
) -> KnowledgeGraph:
    """
    Complete KG building pipeline

    Args:
        chunks: Text chunks to process
        patterns_path: Path to entity patterns JSON
        output_path: Path to save KG JSON

    Returns:
        Constructed KnowledgeGraph
    """
    try:
        # Initialize components
        pattern_loader = PatternLoader(patterns_path)
        client = anthropic.Anthropic()

        # Step 1: Pattern-based entity extraction
        entity_extractor = EntityExtractor(pattern_loader, client)
        pattern_entities = entity_extractor.extract_entities_by_pattern(chunks)

        # Step 2: LLM-assisted extraction
        llm_entities = await entity_extractor.extract_entities_with_llm(
            chunks,
            pattern_entities,
            sample_size=min(10, len(chunks))
        )

        # Combine entities
        all_entities = {}
        for etype in pattern_loader.get_entity_types():
            all_entities[etype] = pattern_entities.get(etype, []) + llm_entities.get(etype, [])

        # Step 3: Relation extraction
        relation_extractor = RelationExtractor(client)
        relations = relation_extractor.extract_relations(chunks, all_entities)

        # Step 4: KG construction
        kg_builder = KnowledgeGraphBuilder()
        kg = kg_builder.build_kg(all_entities, relations)

        # Step 5: Save KG
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(kg.to_dict(), f, indent=2, ensure_ascii=False)

        logger.info(f"✅ KG saved to {output_path}")

        # Log summary
        logger.info("\n" + "="*60)
        logger.info("KNOWLEDGE GRAPH CONSTRUCTION SUMMARY")
        logger.info("="*60)
        logger.info(f"Total Nodes: {kg.metadata['total_nodes']}")
        logger.info(f"Total Edges: {kg.metadata['total_edges']}")
        logger.info(f"Entity Types: {len(kg.metadata['entity_type_counts'])}")
        logger.info(f"Relation Types: {len(kg.metadata['relation_type_counts'])}")
        logger.info(f"Average Confidence: {kg.metadata['average_confidence']:.3f}")
        logger.info("\nEntity Type Distribution:")
        for etype, count in sorted(kg.metadata['entity_type_counts'].items()):
            logger.info(f"  {etype}: {count}")
        logger.info("\nRelation Type Distribution:")
        for rtype, count in sorted(kg.metadata['relation_type_counts'].items()):
            logger.info(f"  {rtype}: {count}")
        logger.info("="*60 + "\n")

        return kg

    except Exception as e:
        logger.error(f"Failed to build knowledge graph: {e}", exc_info=True)
        raise


# ============================================================================
# Utility Functions
# ============================================================================

def load_knowledge_graph(kg_path: Path) -> KnowledgeGraph:
    """Load a previously saved knowledge graph"""
    with open(kg_path, 'r', encoding='utf-8') as f:
        kg_dict = json.load(f)

    # Reconstruct KG objects
    nodes = {
        entity_id: Entity(**entity_data)
        for entity_id, entity_data in kg_dict['nodes'].items()
    }

    edges = [Relation(**relation_data) for relation_data in kg_dict['edges']]

    return KnowledgeGraph(
        nodes=nodes,
        edges=edges,
        metadata=kg_dict.get('metadata', {}),
        forward_index=kg_dict.get('indices', {}).get('forward_index', {}),
        backward_index=kg_dict.get('indices', {}).get('backward_index', {}),
        entity_index=kg_dict.get('indices', {}).get('entity_index', {})
    )


def get_entity_neighbors(kg: KnowledgeGraph, entity_id: str) -> Dict[str, List[str]]:
    """Get all neighbors of an entity (both forward and backward)"""
    return {
        'outgoing': kg.forward_index.get(entity_id, []),
        'incoming': kg.backward_index.get(entity_id, [])
    }


def search_entities_by_type(kg: KnowledgeGraph, entity_type: str) -> List[Entity]:
    """Search entities by type"""
    return list(kg.entity_index.get(entity_type, {}).values())


def get_kg_statistics(kg: KnowledgeGraph) -> Dict:
    """Get comprehensive KG statistics"""
    return {
        'summary': kg.metadata,
        'entity_types': list(kg.entity_index.keys()),
        'relation_types': list(set(edge.relation_type for edge in kg.edges)),
        'dense_nodes': sorted(
            [(eid, len(kg.forward_index.get(eid, [])))
             for eid in kg.nodes.keys()],
            key=lambda x: x[1],
            reverse=True
        )[:10]  # Top 10 most connected nodes
    }


if __name__ == "__main__":
    # Example usage
    import sys

    if len(sys.argv) < 2:
        print("Usage: python kg_builder.py <chunks_json_file> [output_path]")
        sys.exit(1)

    chunks_file = Path(sys.argv[1])
    output_file = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("local_kg.json")
    patterns_file = Path(__file__).parent.parent / "data" / "patterns" / "entity_patterns.json"

    # Load chunks
    with open(chunks_file, 'r', encoding='utf-8') as f:
        chunks_data = json.load(f)

    chunks = [
        Chunk(id=c['id'], text=c['text'], source=c.get('source', ''))
        for c in chunks_data
    ]

    # Run pipeline
    kg = asyncio.run(build_knowledge_graph(chunks, patterns_file, output_file))
    print(f"\n✅ Knowledge Graph built successfully!")
    print(f"   Nodes: {kg.metadata['total_nodes']}")
    print(f"   Edges: {kg.metadata['total_edges']}")
