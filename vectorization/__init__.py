"""
Vectorization module for Vastu Shastra DSS.
Handles conversion of text chunks to vector embeddings using Chroma.
"""

from .chroma_vectorizer import ChromaVectorizer, VectorizationStats

__all__ = [
    'ChromaVectorizer',
    'VectorizationStats',
]
