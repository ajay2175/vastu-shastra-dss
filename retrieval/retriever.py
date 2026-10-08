"""Retriever for evidence collection from vector databases."""

import logging
from typing import List, Dict, Optional, Any
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class Retriever:
    """
    Retrieves evidence from vector databases for RAG.
    Handles embedding generation and similarity search.
    """

    def __init__(self, model_name: str = "paraphrase-multilingual-mpnet-base-v2", top_k: int = 5):
        """
        Initialize retriever.

        Args:
            model_name: Name of embedding model
            top_k: Default number of results to retrieve
        """
        self.model_name = model_name
        self.top_k = top_k
        self.model = None
        self.db_adapter = None
        self.initialized = False

    async def initialize(self, db_adapter: Any) -> bool:
        """
        Initialize retriever with database adapter.

        Args:
            db_adapter: Vector database adapter

        Returns:
            Success status
        """
        try:
            self.db_adapter = db_adapter
            # Load embedding model
            logger.info(f"Loading embedding model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            self.initialized = True
            logger.info("Retriever initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Retriever initialization failed: {e}")
            return False

    async def retrieve(
        self, query: str, top_k: Optional[int] = None, filters: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Retrieve evidence for a query.

        Args:
            query: Query text
            top_k: Number of results to retrieve
            filters: Optional filters

        Returns:
            Retrieval results
        """
        if not self.initialized:
            logger.warning("Retriever not initialized")
            return {
                "error": "Retriever not initialized",
                "results": [],
                "query": query,
            }

        try:
            # Generate query embedding
            query_embedding = self.model.encode(query)

            # Search database
            top_k = top_k or self.top_k
            results = await self.db_adapter.search(query_embedding, top_k=top_k, filter_dict=filters)

            return {
                "query": query,
                "results": results,
                "count": len(results),
                "top_k": top_k,
            }

        except Exception as e:
            logger.error(f"Retrieval error: {e}")
            return {
                "error": str(e),
                "results": [],
                "query": query,
            }

    async def retrieve_batch(
        self, queries: List[str], top_k: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve evidence for multiple queries.

        Args:
            queries: List of queries
            top_k: Number of results per query

        Returns:
            List of retrieval results
        """
        results = []
        for query in queries:
            result = await self.retrieve(query, top_k=top_k)
            results.append(result)
        return results

    async def retrieve_similar_documents(
        self, document_embedding: List[float], top_k: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve similar documents to a given embedding.

        Args:
            document_embedding: Document embedding vector
            top_k: Number of results

        Returns:
            Similar documents
        """
        if not self.db_adapter:
            logger.warning("Database adapter not set")
            return []

        try:
            top_k = top_k or self.top_k
            results = await self.db_adapter.search(document_embedding, top_k=top_k)
            return results
        except Exception as e:
            logger.error(f"Error retrieving similar documents: {e}")
            return []

    def encode_text(self, text: str) -> List[float]:
        """
        Encode text to embedding vector.

        Args:
            text: Text to encode

        Returns:
            Embedding vector
        """
        if not self.initialized:
            logger.warning("Retriever not initialized")
            return []

        try:
            embedding = self.model.encode(text)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Encoding error: {e}")
            return []

    def encode_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Encode multiple texts to embeddings.

        Args:
            texts: Texts to encode

        Returns:
            List of embedding vectors
        """
        if not self.initialized:
            logger.warning("Retriever not initialized")
            return []

        try:
            embeddings = self.model.encode(texts)
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"Batch encoding error: {e}")
            return []

    async def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings."""
        if not self.initialized:
            return 0

        try:
            # Test embedding
            test_embedding = self.model.encode("test")
            return len(test_embedding)
        except Exception as e:
            logger.error(f"Error getting embedding dimension: {e}")
            return 0
