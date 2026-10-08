"""Constants for Vastu Shastra DSS."""

# Vastu Shastra Core Principles
CARDINAL_DIRECTIONS = ["North", "Northeast", "East", "Southeast", "South", "Southwest", "West", "Northwest"]
EIGHT_DIRECTIONS = {
    "N": "North",
    "NE": "Northeast",
    "E": "East",
    "SE": "Southeast",
    "S": "South",
    "SW": "Southwest",
    "W": "West",
    "NW": "Northwest",
}

FIVE_ELEMENTS = ["Earth", "Water", "Fire", "Air", "Ether"]
ELEMENT_PROPERTIES = {
    "Earth": {"color": "brown", "direction": "Southwest"},
    "Water": {"color": "black", "direction": "North"},
    "Fire": {"color": "red", "direction": "Southeast"},
    "Air": {"color": "green", "direction": "East"},
    "Ether": {"color": "white", "direction": "Northwest"},
}

# Room Types
ROOM_TYPES = [
    "Bedroom",
    "Kitchen",
    "Living Room",
    "Bathroom",
    "Study",
    "Pooja Room",
    "Entrance",
    "Garage",
    "Garden",
    "Corridor",
]

# Purpose Categories
PURPOSE_CATEGORIES = [
    "Residential",
    "Commercial",
    "Industrial",
    "Educational",
    "Religious",
    "Medical",
    "Hospitality",
    "Administrative",
]

# Vastu Compliance Levels
COMPLIANCE_LEVELS = ["Excellent", "Good", "Moderate", "Poor", "Critical"]

# Response Types
RESPONSE_TYPES = {
    "RECOMMENDATION": "recommendation",
    "CORRECTION": "correction",
    "MITIGATION": "mitigation",
    "EXPLANATION": "explanation",
    "REFERENCE": "reference",
}

# Knowledge Graph Node Types
KG_NODE_TYPES = {
    "PRINCIPLE": "principle",
    "ELEMENT": "element",
    "DIRECTION": "direction",
    "ROOM": "room",
    "REMEDY": "remedy",
    "MATERIAL": "material",
    "COLOR": "color",
    "SHAPE": "shape",
    "PLACEMENT": "placement",
}

# Relationship Types in Knowledge Graph
KG_EDGE_TYPES = {
    "BELONGS_TO": "belongs_to",
    "INFLUENCES": "influences",
    "REMEDIES": "remedies",
    "CONFLICTS_WITH": "conflicts_with",
    "ENHANCES": "enhances",
    "LOCATED_IN": "located_in",
    "GOVERNS": "governs",
    "RELATED_TO": "related_to",
}

# RAG Configuration
RAG_CHUNK_SIZE = 1000
RAG_CHUNK_OVERLAP = 200
RAG_TOP_K = 5
RAG_SCORE_THRESHOLD = 0.5

# Vector Database
EMBEDDINGS_DIM = 768
EMBEDDINGS_MODEL = "paraphrase-multilingual-mpnet-base-v2"
CHROMA_COLLECTION_PREFIX = "vastu_"

# Claude Model Configuration
CLAUDE_MODEL = "claude-opus-4-1-20250805"
CLAUDE_CONTEXT_WINDOW = 200000
CLAUDE_TIMEOUT = 60

# Error Messages
ERROR_MESSAGES = {
    "VDB_UNAVAILABLE": "Vector database is currently unavailable. Using fallback mode.",
    "RAG_FAILURE": "RAG retrieval failed. Proceeding with principle-based reasoning.",
    "KG_ERROR": "Knowledge graph error. Using standalone consultation mode.",
    "INVALID_INPUT": "Invalid input provided to consultation system.",
    "API_RATE_LIMIT": "API rate limit exceeded. Please retry after some time.",
}

# Success Messages
SUCCESS_MESSAGES = {
    "ANALYSIS_COMPLETE": "Vastu analysis completed successfully.",
    "RECOMMENDATIONS_GENERATED": "Recommendations have been generated.",
    "REASONING_COMPLETE": "Reasoning process complete.",
}
