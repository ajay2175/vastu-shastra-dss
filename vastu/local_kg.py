"""
Local Knowledge Graph (KG) for Vastu Shastra DSS.

Lightweight, versionable schema optimized for multi-hop reasoning and remedial suggestions.
Built with git-friendly JSON storage and efficient in-memory traversal.

Entity Types: 15+ categories covering directions, rooms, doshas, remedies, elements, etc.
Relations: 25+ relation types supporting multi-hop reasoning.
Query Engine: LocalKGQueryEngine for entity retrieval, relation discovery, and remedy suggestion.
"""

from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import json
from enum import Enum


# ============================================================================
# ENUMS & CONSTANTS
# ============================================================================

class EntityType(str, Enum):
    """15+ entity types covering Vastu domain knowledge."""
    DIRECTION = "direction"
    ROOM = "room"
    VASTU_DOSHA = "vastu_dosha"
    REMEDY = "remedy"
    ELEMENT = "element"
    COLOR = "color"
    MATERIAL = "material"
    GEOMETRIC_PRINCIPLE = "geometric_principle"
    SACRED_GEOMETRY = "sacred_geometry"
    TEXT_SOURCE = "text_source"
    DOSHA_CORRELATION = "dosha_correlation"
    HEALTH_IMPACT = "health_impact"
    CHAKRA = "chakra"
    ROOM_ELEMENT = "room_element"
    TEMPORAL_ASPECT = "temporal_aspect"


class RelationType(str, Enum):
    """25+ relation types supporting multi-hop reasoning."""
    # Structural relations
    LOCATED_IN = "LOCATED_IN"                    # room ← direction
    HAS_ELEMENT = "HAS_ELEMENT"                 # direction → element
    HAS_COLOR = "HAS_COLOR"                     # direction/element → color

    # Dosha relations
    REQUIRES_REMEDY = "REQUIRES_REMEDY"         # dosha → remedy
    CORRECTS_DOSHA = "CORRECTS_DOSHA"           # remedy → dosha
    IMPACTS_ROOM = "IMPACTS_ROOM"               # dosha → room
    AGGRAVATES_HEALTH = "AGGRAVATES_HEALTH"     # vastu_dosha → health_impact
    SUPPORTS_HEALTH = "SUPPORTS_HEALTH"         # remedy → health_impact

    # Room-direction relations
    OPTIMAL_FOR = "OPTIMAL_FOR"                 # room → direction
    AVOID_IN = "AVOID_IN"                       # room → direction

    # Chakra and energy
    ACTIVATES_CHAKRA = "ACTIVATES_CHAKRA"       # direction → chakra
    CHAKRA_GOVERNS = "CHAKRA_GOVERNS"           # chakra → body_system

    # Ayurvedic correlation
    CORRELATES_DOSHA = "CORRELATES_DOSHA"       # element/color → dosha_correlation
    BALANCES_DOSHA = "BALANCES_DOSHA"           # remedy → dosha_correlation

    # Textual and principle relations
    FOUND_IN_TEXT = "FOUND_IN_TEXT"             # principle → text_source
    SUPPORTS_PRINCIPLE = "SUPPORTS_PRINCIPLE"   # principle_A → principle_B
    CONTRADICTS_PRINCIPLE = "CONTRADICTS_PRINCIPLE"  # principle_A ← principle_B

    # Geometric and material
    SACRED_PROPORTION = "SACRED_PROPORTION"     # geometric_principle → ratio
    TEMPORAL_ALIGNMENT = "TEMPORAL_ALIGNMENT"   # direction → temporal_aspect
    MATERIAL_SUITABLE = "MATERIAL_SUITABLE"     # room → material
    COLOR_REMEDY = "COLOR_REMEDY"               # color → dosha_correlation

    # Additional relations
    REPRESENTS = "REPRESENTS"                   # symbol → concept
    COMPLEMENTS = "COMPLEMENTS"                 # element_A → element_B
    ENHANCES = "ENHANCES"                       # remedy_A → remedy_B
    SYNERGIZES_WITH = "SYNERGIZES_WITH"         # principle → principle
    CONTRADICTS_WITH = "CONTRADICTS_WITH"       # principle ← principle


# ============================================================================
# ENTITY TYPE COUNTS
# ============================================================================

ENTITY_TYPE_COUNTS = {
    EntityType.DIRECTION: 9,                     # 8 cardinal + center
    EntityType.ROOM: 10,                         # bedroom, kitchen, etc.
    EntityType.VASTU_DOSHA: 20,                  # defects/imbalances
    EntityType.REMEDY: 15,                       # remedial measures
    EntityType.ELEMENT: 5,                       # water, fire, earth, air, space
    EntityType.COLOR: 10,                        # colors for each direction
    EntityType.MATERIAL: 8,                      # wood, stone, marble, etc.
    EntityType.GEOMETRIC_PRINCIPLE: 10,          # sacred geometry principles
    EntityType.SACRED_GEOMETRY: 8,               # geometric shapes/patterns
    EntityType.TEXT_SOURCE: 107,                 # Vastu texts
    EntityType.DOSHA_CORRELATION: 3,             # vata, pitta, kapha
    EntityType.HEALTH_IMPACT: 15,                # health conditions
    EntityType.CHAKRA: 7,                        # chakra system
    EntityType.ROOM_ELEMENT: 50,                 # room-specific elements
    EntityType.TEMPORAL_ASPECT: 12,              # time-based aspects
}


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class Entity:
    """Represents a KG entity with metadata and properties."""
    id: str
    type: str
    label: str
    properties: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Relation:
    """Represents a relationship between two entities."""
    id: str
    source: str
    target: str
    relation_type: str
    properties: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class KGMetadata:
    """Metadata about the KG."""
    version: str = "1.0"
    created: str = "2026-10-08"
    description: str = "Vastu Shastra Local Knowledge Graph"
    total_nodes: int = 0
    total_edges: int = 0
    entity_types: int = len(ENTITY_TYPE_COUNTS)
    relation_types: int = len(RelationType)


# ============================================================================
# LOCAL KG QUERY ENGINE
# ============================================================================

class LocalKGQueryEngine:
    """
    Lightweight in-memory KG query engine for Vastu DSS.

    Supports:
    - Entity retrieval by ID or type
    - Multi-hop traversal
    - Relation discovery
    - Remedy suggestion with confidence scores
    - Room-direction optimization
    - Health impact analysis
    """

    def __init__(self, kg_path: Optional[Path] = None):
        """Initialize the query engine from KG file."""
        self.nodes: Dict[str, Entity] = {}
        self.edges: List[Relation] = []
        self.edge_idx: Dict[Tuple[str, str], List[Relation]] = {}  # (source, target) -> [relations]
        self.entity_type_idx: Dict[str, List[Entity]] = {}  # type -> [entities]
        self.relation_type_idx: Dict[str, List[Relation]] = {}  # type -> [relations]

        if kg_path:
            self.load_from_file(kg_path)

    def load_from_file(self, kg_path: Path) -> None:
        """Load KG from JSON file."""
        with open(kg_path, 'r', encoding='utf-8') as f:
            kg_data = json.load(f)

        # Load nodes
        for node_data in kg_data.get('nodes', []):
            entity = Entity(
                id=node_data['id'],
                type=node_data['type'],
                label=node_data['label'],
                properties=node_data.get('properties', {})
            )
            self.nodes[entity.id] = entity

            # Index by type
            if entity.type not in self.entity_type_idx:
                self.entity_type_idx[entity.type] = []
            self.entity_type_idx[entity.type].append(entity)

        # Load edges
        for edge_data in kg_data.get('edges', []):
            relation = Relation(
                id=edge_data['id'],
                source=edge_data['source'],
                target=edge_data['target'],
                relation_type=edge_data['relation'],
                properties=edge_data.get('properties', {})
            )
            self.edges.append(relation)

            # Index by (source, target)
            key = (relation.source, relation.target)
            if key not in self.edge_idx:
                self.edge_idx[key] = []
            self.edge_idx[key].append(relation)

            # Index by relation type
            if relation.relation_type not in self.relation_type_idx:
                self.relation_type_idx[relation.relation_type] = []
            self.relation_type_idx[relation.relation_type].append(relation)

    # ========================================================================
    # ENTITY RETRIEVAL
    # ========================================================================

    def get_entity(self, entity_id: str) -> Optional[Entity]:
        """Get entity by ID."""
        return self.nodes.get(entity_id)

    def find_by_type(self, entity_type: str) -> List[Entity]:
        """Find all entities of a given type."""
        return self.entity_type_idx.get(entity_type, [])

    def find_by_label(self, label: str) -> List[Entity]:
        """Find entities by label (case-insensitive partial match)."""
        label_lower = label.lower()
        return [e for e in self.nodes.values() if label_lower in e.label.lower()]

    # ========================================================================
    # RELATION QUERIES
    # ========================================================================

    def get_entity_relations(self, entity_id: str, relation_type: Optional[str] = None) -> List[Relation]:
        """Get relations for an entity (outgoing edges)."""
        if relation_type:
            return [
                r for r in self.edges
                if r.source == entity_id and r.relation_type == relation_type
            ]
        return [r for r in self.edges if r.source == entity_id]

    def get_incoming_relations(self, entity_id: str, relation_type: Optional[str] = None) -> List[Relation]:
        """Get incoming relations to an entity."""
        if relation_type:
            return [
                r for r in self.edges
                if r.target == entity_id and r.relation_type == relation_type
            ]
        return [r for r in self.edges if r.target == entity_id]

    def find_relations_between(self, entity_a: str, entity_b: str) -> List[Relation]:
        """Find all direct relations between two entities."""
        return self.edge_idx.get((entity_a, entity_b), [])

    def find_relations_by_type(self, relation_type: str) -> List[Relation]:
        """Find all relations of a given type."""
        return self.relation_type_idx.get(relation_type, [])

    # ========================================================================
    # MULTI-HOP TRAVERSAL
    # ========================================================================

    def multi_hop_traverse(
        self,
        entity_ids: List[str],
        max_hops: int = 2,
        relation_types: Optional[List[str]] = None,
        visited: Optional[Set[str]] = None
    ) -> List[Entity]:
        """
        Multi-hop traversal from entity IDs.

        Args:
            entity_ids: Starting entity IDs
            max_hops: Maximum traversal depth
            relation_types: Filter by specific relation types (None = all)
            visited: Track visited entities to avoid cycles

        Returns:
            List of entities reachable within max_hops
        """
        if visited is None:
            visited = set()

        if max_hops <= 0:
            return []

        result = []
        new_entities = set()

        for entity_id in entity_ids:
            if entity_id in visited:
                continue
            visited.add(entity_id)

            relations = self.get_entity_relations(entity_id)
            if relation_types:
                relations = [r for r in relations if r.relation_type in relation_types]

            for relation in relations:
                if relation.target not in visited:
                    new_entities.add(relation.target)
                    entity = self.get_entity(relation.target)
                    if entity:
                        result.append(entity)

        # Recursive traversal
        if max_hops > 1 and new_entities:
            result.extend(self.multi_hop_traverse(
                list(new_entities),
                max_hops - 1,
                relation_types,
                visited
            ))

        return result

    # ========================================================================
    # DOSHA & REMEDY QUERIES
    # ========================================================================

    def suggest_remedies(self, dosha_id: str, max_suggestions: int = 5) -> List[Tuple[Entity, float]]:
        """
        Suggest remedies for a Vastu dosha.

        Returns:
            List of (remedy_entity, confidence_score) tuples
        """
        remedies_with_score = []

        # Direct remedies via REQUIRES_REMEDY relation
        relations = self.get_entity_relations(dosha_id, RelationType.REQUIRES_REMEDY.value)
        for relation in relations:
            remedy = self.get_entity(relation.target)
            if remedy:
                confidence = relation.properties.get('confidence', 0.85)
                remedies_with_score.append((remedy, confidence))

        # Sort by confidence and return top suggestions
        remedies_with_score.sort(key=lambda x: x[1], reverse=True)
        return remedies_with_score[:max_suggestions]

    def get_dosha_chain(self, dosha_id: str) -> Dict[str, Any]:
        """
        Get comprehensive dosha analysis chain:
        dosha -> symptoms -> health_impacts -> remedies -> supporting_elements
        """
        dosha = self.get_entity(dosha_id)
        if not dosha:
            return {}

        return {
            "dosha": dosha.to_dict(),
            "health_impacts": self._get_targets(dosha_id, RelationType.AGGRAVATES_HEALTH.value),
            "remedies": self._get_targets(dosha_id, RelationType.REQUIRES_REMEDY.value),
            "affected_rooms": self._get_targets(dosha_id, RelationType.IMPACTS_ROOM.value),
        }

    # ========================================================================
    # ROOM & DIRECTION OPTIMIZATION
    # ========================================================================

    def optimal_direction_for_room(self, room_type: str) -> Optional[Entity]:
        """
        Get optimal direction for a room type.

        Args:
            room_type: Room type (e.g., "bedroom", "kitchen")

        Returns:
            Optimal direction entity or None
        """
        # Find room entity by label
        rooms = self.find_by_label(room_type)
        if not rooms:
            return None

        room = rooms[0]

        # Get optimal direction via OPTIMAL_FOR relation (inverse)
        incoming = self.get_incoming_relations(room.id, RelationType.OPTIMAL_FOR.value)
        if incoming:
            direction = self.get_entity(incoming[0].source)
            return direction

        return None

    def get_directions_for_room(self, room_id: str) -> Dict[str, List[Entity]]:
        """
        Get optimal and avoid directions for a room.

        Returns:
            {"optimal": [entities], "avoid": [entities]}
        """
        optimal = self._get_targets(room_id, RelationType.OPTIMAL_FOR.value)
        avoid = self._get_targets(room_id, RelationType.AVOID_IN.value)

        return {
            "optimal": optimal,
            "avoid": avoid
        }

    # ========================================================================
    # ELEMENT & COLOR ANALYSIS
    # ========================================================================

    def get_direction_properties(self, direction_id: str) -> Dict[str, Any]:
        """
        Get comprehensive properties of a direction:
        element, colors, chakra, dosha correlation, etc.
        """
        direction = self.get_entity(direction_id)
        if not direction:
            return {}

        return {
            "direction": direction.to_dict(),
            "element": self._get_single_target(direction_id, RelationType.HAS_ELEMENT.value),
            "colors": self._get_targets(direction_id, RelationType.HAS_COLOR.value),
            "chakra": self._get_single_target(direction_id, RelationType.ACTIVATES_CHAKRA.value),
            "temporal": self._get_single_target(direction_id, RelationType.TEMPORAL_ALIGNMENT.value),
            "optimal_rooms": self._get_targets_of_incoming(direction_id, RelationType.OPTIMAL_FOR.value),
        }

    def get_element_correlations(self, element_id: str) -> Dict[str, Any]:
        """
        Get element's correlations: colors, doshas, properties
        """
        element = self.get_entity(element_id)
        if not element:
            return {}

        return {
            "element": element.to_dict(),
            "colors": self._get_targets(element_id, RelationType.HAS_COLOR.value),
            "dosha_impact": self._get_targets(element_id, RelationType.CORRELATES_DOSHA.value),
            "complements": self._get_targets(element_id, RelationType.COMPLEMENTS.value),
        }

    # ========================================================================
    # HEALTH IMPACT ANALYSIS
    # ========================================================================

    def health_impacts_for_dosha(self, dosha_id: str) -> List[Entity]:
        """Get health impacts of a Vastu dosha."""
        return self._get_targets(dosha_id, RelationType.AGGRAVATES_HEALTH.value)

    def health_support_for_remedy(self, remedy_id: str) -> List[Entity]:
        """Get health conditions supported by a remedy."""
        return self._get_targets(remedy_id, RelationType.SUPPORTS_HEALTH.value)

    # ========================================================================
    # PRINCIPLE & TEXT RELATIONS
    # ========================================================================

    def get_principle_sources(self, principle_id: str) -> List[Entity]:
        """Get text sources where principle is mentioned."""
        return self._get_targets(principle_id, RelationType.FOUND_IN_TEXT.value)

    def get_supporting_principles(self, principle_id: str) -> List[Entity]:
        """Get principles that support this principle."""
        return self._get_targets(principle_id, RelationType.SUPPORTS_PRINCIPLE.value)

    def get_contradicting_principles(self, principle_id: str) -> List[Entity]:
        """Get principles that contradict this principle."""
        return self._get_targets(principle_id, RelationType.CONTRADICTS_PRINCIPLE.value)

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    def _get_targets(self, entity_id: str, relation_type: str) -> List[Entity]:
        """Get all target entities for a given relation type."""
        relations = self.get_entity_relations(entity_id, relation_type)
        targets = []
        for relation in relations:
            target = self.get_entity(relation.target)
            if target:
                targets.append(target)
        return targets

    def _get_single_target(self, entity_id: str, relation_type: str) -> Optional[Entity]:
        """Get first target entity for a given relation type."""
        targets = self._get_targets(entity_id, relation_type)
        return targets[0] if targets else None

    def _get_targets_of_incoming(self, entity_id: str, relation_type: str) -> List[Entity]:
        """Get source entities of incoming relations (inverse relation)."""
        relations = self.get_incoming_relations(entity_id, relation_type)
        targets = []
        for relation in relations:
            source = self.get_entity(relation.source)
            if source:
                targets.append(source)
        return targets

    # ========================================================================
    # KG STATISTICS
    # ========================================================================

    def get_kg_stats(self) -> Dict[str, Any]:
        """Get statistics about the loaded KG."""
        return {
            "total_nodes": len(self.nodes),
            "total_edges": len(self.edges),
            "entity_types": len(self.entity_type_idx),
            "relation_types": len(self.relation_type_idx),
            "nodes_by_type": {
                etype: len(entities)
                for etype, entities in self.entity_type_idx.items()
            },
            "relations_by_type": {
                rtype: len(relations)
                for rtype, relations in self.relation_type_idx.items()
            }
        }

    def export_subgraph(self, entity_ids: List[str], max_hops: int = 1) -> Dict[str, Any]:
        """Export a subgraph around given entities (for validation/testing)."""
        entities = [self.get_entity(eid) for eid in entity_ids if self.get_entity(eid)]

        # Find all edges within this subgraph
        entity_set = set(entity_ids)
        traversed = self.multi_hop_traverse(entity_ids, max_hops)
        for entity in traversed:
            entity_set.add(entity.id)

        edges = [e for e in self.edges if e.source in entity_set and e.target in entity_set]

        return {
            "metadata": {
                "entity_count": len(entity_set),
                "edge_count": len(edges),
                "max_hops": max_hops
            },
            "nodes": [e.to_dict() for e in entities + traversed],
            "edges": [e.to_dict() for e in edges]
        }


# ============================================================================
# KG BUILDER UTILITIES
# ============================================================================

class KGBuilder:
    """Utility class for building and validating KG files."""

    @staticmethod
    def create_empty_kg() -> Dict[str, Any]:
        """Create an empty KG structure."""
        return {
            "metadata": asdict(KGMetadata()),
            "nodes": [],
            "edges": []
        }

    @staticmethod
    def add_node(kg: Dict[str, Any], node: Entity) -> None:
        """Add a node to KG."""
        kg["nodes"].append(node.to_dict())
        kg["metadata"]["total_nodes"] = len(kg["nodes"])

    @staticmethod
    def add_edge(kg: Dict[str, Any], edge: Relation) -> None:
        """Add an edge to KG."""
        kg["edges"].append(edge.to_dict())
        kg["metadata"]["total_edges"] = len(kg["edges"])

    @staticmethod
    def validate_kg(kg: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate KG structure and references.

        Returns:
            (is_valid, error_messages)
        """
        errors = []
        node_ids = set(n["id"] for n in kg.get("nodes", []))

        # Check edges reference valid nodes
        for edge in kg.get("edges", []):
            if edge["source"] not in node_ids:
                errors.append(f"Edge {edge['id']}: source {edge['source']} not found")
            if edge["target"] not in node_ids:
                errors.append(f"Edge {edge['id']}: target {edge['target']} not found")

        return len(errors) == 0, errors

    @staticmethod
    def save_kg(kg: Dict[str, Any], output_path: Path) -> None:
        """Save KG to JSON file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(kg, f, indent=2, ensure_ascii=False)

    @staticmethod
    def load_kg(kg_path: Path) -> Dict[str, Any]:
        """Load KG from JSON file."""
        with open(kg_path, 'r', encoding='utf-8') as f:
            return json.load(f)


if __name__ == "__main__":
    # Example usage
    print("Vastu Shastra Local KG Module")
    print(f"Entity Types: {len(ENTITY_TYPE_COUNTS)}")
    print(f"Relation Types: {len(RelationType)}")
    print(f"\nEntity Type Counts:")
    for etype, count in ENTITY_TYPE_COUNTS.items():
        print(f"  {etype.value}: {count}")
