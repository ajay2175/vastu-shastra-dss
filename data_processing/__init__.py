"""
Vastu Shastra DSS Data Processing Module

Provides intelligent text chunking, entity extraction, and metadata enrichment
for Vastu Shastra classical texts.

Key Components:
- text_processor: Intelligent semantic chunking with metadata extraction
- Entity extraction: Directions, doshas, remedies, materials
- Verse detection: Sanskrit metrical pattern recognition
- QA reporting: Chunk quality analysis and distribution

Usage:
    from vastu_shastra_dss.data_processing.text_processor import (
        ExtractedText,
        process_vastu_texts,
    )

    # Process extracted texts
    extracted_texts = [
        ExtractedText(
            text="...",
            source_file="mayamatam.pdf",
            chapter="...",
        ),
    ]

    chunks, qa_report = asyncio.run(
        process_vastu_texts(extracted_texts)
    )
"""

from .text_processor import (
    # Data models
    ExtractedText,
    Chunk,
    ChunkingQAReport,
    # Processing functions
    chunk_vastu_texts,
    process_vastu_texts,
    # Utilities
    extract_entities,
    extract_sanskrit_terms,
    detect_principle_type,
    estimate_tokens,
    # I/O
    save_chunks_to_jsonl,
    load_chunks_from_jsonl,
    # QA
    generate_qa_report,
    print_qa_report,
)

from .kg_builder import (
    # Data models for KG
    Entity,
    Relation,
    KnowledgeGraph,
    # Extractors
    PatternLoader,
    EntityExtractor,
    RelationExtractor,
    KnowledgeGraphBuilder,
    # Pipeline
    build_knowledge_graph,
    load_knowledge_graph,
    # Utilities
    get_entity_neighbors,
    search_entities_by_type,
    get_kg_statistics,
)

__all__ = [
    # Text processing
    "ExtractedText",
    "Chunk",
    "ChunkingQAReport",
    "chunk_vastu_texts",
    "process_vastu_texts",
    "extract_entities",
    "extract_sanskrit_terms",
    "detect_principle_type",
    "estimate_tokens",
    "save_chunks_to_jsonl",
    "load_chunks_from_jsonl",
    "generate_qa_report",
    "print_qa_report",
    # KG building
    "Entity",
    "Relation",
    "KnowledgeGraph",
    "PatternLoader",
    "EntityExtractor",
    "RelationExtractor",
    "KnowledgeGraphBuilder",
    "build_knowledge_graph",
    "load_knowledge_graph",
    "get_entity_neighbors",
    "search_entities_by_type",
    "get_kg_statistics",
]
