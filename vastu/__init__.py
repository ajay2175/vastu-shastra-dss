"""Vastu Shastra core module."""

# Local KG imports (primary)
from .local_kg import (
    LocalKGQueryEngine,
    KGBuilder,
    Entity,
    Relation,
    EntityType,
    RelationType,
    ENTITY_TYPE_COUNTS,
)

# Legacy imports (if available)
try:
    from .embedded_principles import VastuPrinciples
except ImportError:
    VastuPrinciples = None

try:
    from .standalone_consultation import StandaloneConsultation
except ImportError:
    StandaloneConsultation = None

try:
    from .constants import VASTU_PRINCIPLES
except ImportError:
    VASTU_PRINCIPLES = None

__all__ = [
    # Local KG classes
    "LocalKGQueryEngine",
    "KGBuilder",
    "Entity",
    "Relation",
    "EntityType",
    "RelationType",
    "ENTITY_TYPE_COUNTS",
    # Legacy (optional)
    "VastuPrinciples",
    "StandaloneConsultation",
    "VASTU_PRINCIPLES",
]
