"""Unified hybrid search engine combining dense and sparse retrieval with KG entity indexing."""

import asyncio
import json
import logging
import time
from collections import defaultdict
from pathlib import Path
from typing import List, Dict, Optional, Any, Set, Tuple
import re

from sentence_transformers import SentenceTransformer

from retrieval.bm25_index import BM25Index

logger = logging.getLogger(__name__)


class DenseRetriever:
    """
    Dense vector retrieval using sentence embeddings.
    Integrates with Chroma or other vector databases.
    """

    def __init__(
        self,
        model_name: str = "paraphrase-multilingual-mpnet-base-v2",
        db_path: Optional[str] = None,
    ):
        """
        Initialize dense retriever.

        Args:
            model_name: Embedding model name
            db_path: Path to Chroma database (optional)
        """
        self.model_name = model_name
        self.db_path = db_path
        self.model = None
        self.chroma_client = None
        self.collection = None
        self.documents = {}

    async def initialize(self) -> bool:
        """Initialize embedding model and database."""
        try:
            logger.info(f"Loading embedding model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)

            # Try to use Chroma if available
            try:
                import chromadb

                if self.db_path:
                    Path(self.db_path).mkdir(parents=True, exist_ok=True)
                    self.chroma_client = chromadb.PersistentClient(path=self.db_path)
                else:
                    self.chroma_client = chromadb.EphemeralClient()

                self.collection = self.chroma_client.get_or_create_collection(
                    name="vastu_shastra",
                    metadata={"hnsw:space": "cosine"},
                )
                logger.info("Chroma client initialized")
            except ImportError:
                logger.warning("chromadb not installed. Dense retriever will use in-memory storage.")
                self.chroma_client = None

            return True
        except Exception as e:
            logger.error(f"Failed to initialize dense retriever: {e}")
            return False

    async def add_documents(self, documents: List[Dict[str, Any]]) -> bool:
        """
        Add documents to dense index.

        Args:
            documents: List of documents with 'doc_id' and 'text'

        Returns:
            Success status
        """
        try:
            batch_size = 32
            ids = []
            embeddings = []
            metadatas = []
            documents_text = []

            for doc in documents:
                doc_id = doc.get("doc_id", str(len(self.documents)))
                text = doc.get("text", "")
                metadata = doc.get("metadata", {})

                if not text:
                    continue

                self.documents[doc_id] = {"text": text, "metadata": metadata}
                ids.append(doc_id)
                documents_text.append(text)
                metadatas.append(metadata)

            # Encode documents in batches
            if documents_text:
                embeddings = self.model.encode(documents_text, show_progress_bar=True)

                if self.collection:
                    # Add to Chroma
                    for i in range(0, len(ids), batch_size):
                        batch_ids = ids[i : i + batch_size]
                        batch_embeddings = embeddings[i : i + batch_size]
                        batch_metadatas = metadatas[i : i + batch_size]
                        batch_documents = documents_text[i : i + batch_size]

                        self.collection.add(
                            ids=batch_ids,
                            embeddings=batch_embeddings.tolist(),
                            metadatas=batch_metadatas,
                            documents=batch_documents,
                        )

                logger.info(f"Added {len(ids)} documents to dense index")
            return True
        except Exception as e:
            logger.error(f"Failed to add documents to dense index: {e}")
            return False

    async def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search for similar documents.

        Args:
            query: Query text
            top_k: Number of results

        Returns:
            List of search results with scores
        """
        try:
            if not self.model:
                return []

            # Encode query
            query_embedding = self.model.encode(query)

            results = []

            if self.collection:
                # Search in Chroma
                chroma_results = self.collection.query(
                    query_embeddings=[query_embedding.tolist()],
                    n_results=top_k,
                )

                if chroma_results and chroma_results["ids"]:
                    for i, doc_id in enumerate(chroma_results["ids"][0]):
                        distance = chroma_results["distances"][0][i] if chroma_results["distances"] else 1.0
                        # Convert distance to similarity (cosine distance to similarity)
                        similarity = 1 - distance if distance >= 0 else distance

                        results.append(
                            {
                                "doc_id": doc_id,
                                "score": max(0, similarity),  # Ensure non-negative
                                "text": chroma_results["documents"][0][i] if chroma_results["documents"] else "",
                                "metadata": chroma_results["metadatas"][0][i] if chroma_results["metadatas"] else {},
                                "source": "chroma",
                            }
                        )
            else:
                # Fallback: in-memory search
                from sklearn.metrics.pairwise import cosine_similarity
                import numpy as np

                query_embedding = query_embedding.reshape(1, -1)

                for doc_id, doc_data in list(self.documents.items())[:top_k * 3]:
                    doc_embedding = self.model.encode(doc_data["text"]).reshape(1, -1)
                    similarity = cosine_similarity(query_embedding, doc_embedding)[0][0]

                    results.append(
                        {
                            "doc_id": doc_id,
                            "score": float(similarity),
                            "text": doc_data["text"][:500],
                            "metadata": doc_data["metadata"],
                            "source": "memory",
                        }
                    )

            return sorted(results, key=lambda x: x["score"], reverse=True)[:top_k]
        except Exception as e:
            logger.error(f"Dense search failed: {e}")
            return []


class SparseRetriever:
    """
    Sparse keyword-based retrieval using BM25.
    """

    def __init__(self, index_path: Optional[Path] = None):
        """
        Initialize sparse retriever.

        Args:
            index_path: Path to save/load BM25 index
        """
        self.index_path = index_path
        self.index = BM25Index()

    async def add_documents(self, documents: List[Dict[str, Any]]) -> bool:
        """
        Add documents to sparse index.

        Args:
            documents: List of documents with 'doc_id' and 'text'

        Returns:
            Success status
        """
        try:
            for doc in documents:
                doc_id = doc.get("doc_id", "")
                text = doc.get("text", "")
                metadata = doc.get("metadata", {})

                if not text:
                    continue

                self.index.add_document(doc_id, text, metadata=metadata)

            self.index.build_index()
            logger.info(f"Built sparse index with {self.index.total_docs} documents")
            return True
        except Exception as e:
            logger.error(f"Failed to add documents to sparse index: {e}")
            return False

    async def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search using BM25.

        Args:
            query: Query text
            top_k: Number of results

        Returns:
            List of search results with scores
        """
        try:
            results = self.index.search(query, top_k=top_k)
            for result in results:
                result["source"] = "bm25"
            return results
        except Exception as e:
            logger.error(f"Sparse search failed: {e}")
            return []

    async def search_boolean(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search with Boolean operators."""
        try:
            results = self.index.search_boolean(query, top_k=top_k)
            for result in results:
                result["source"] = "bm25_boolean"
            return results
        except Exception as e:
            logger.error(f"Boolean search failed: {e}")
            return []

    def save(self) -> None:
        """Save BM25 index to disk."""
        if self.index_path:
            self.index.save(self.index_path)

    def load(self) -> bool:
        """Load BM25 index from disk."""
        if self.index_path and Path(self.index_path).exists():
            return self.index.load(self.index_path)
        return False


class KGEntityIndexer:
    """
    Knowledge Graph entity indexer for entity-based retrieval.
    """

    def __init__(self, kg_path: Optional[Path] = None):
        """
        Initialize entity indexer.

        Args:
            kg_path: Path to knowledge graph file
        """
        self.kg_path = kg_path
        self.entities = {}
        self.entity_docs = defaultdict(set)  # entity -> doc_ids
        self.relationships = []

    async def load_kg(self, kg_data: Dict[str, Any]) -> bool:
        """
        Load knowledge graph data.

        Args:
            kg_data: Knowledge graph with nodes and edges

        Returns:
            Success status
        """
        try:
            nodes = kg_data.get("nodes", [])
            edges = kg_data.get("edges", [])

            # Index entities
            for node in nodes:
                entity_id = node.get("id", "")
                self.entities[entity_id] = {
                    "id": entity_id,
                    "type": node.get("type", ""),
                    "properties": node.get("properties", {}),
                }

            self.relationships = edges
            logger.info(f"Loaded KG with {len(self.entities)} entities and {len(edges)} relationships")
            return True
        except Exception as e:
            logger.error(f"Failed to load KG: {e}")
            return False

    def index_entity_mentions(self, documents: List[Dict[str, Any]]) -> None:
        """
        Index entity mentions in documents.

        Args:
            documents: List of documents to index
        """
        for doc in documents:
            doc_id = doc.get("doc_id", "")
            text = doc.get("text", "").lower()

            for entity_id in self.entities:
                # Simple string matching - can be enhanced
                entity_aliases = self.entities[entity_id].get("properties", {}).get("aliases", [])
                if entity_id.lower() in text or any(alias.lower() in text for alias in entity_aliases):
                    self.entity_docs[entity_id].add(doc_id)

    async def search_by_entity(self, entity_id: str) -> List[str]:
        """Get documents for an entity."""
        return list(self.entity_docs.get(entity_id, set()))

    def get_entity_info(self, entity_id: str) -> Dict[str, Any]:
        """Get entity information."""
        return self.entities.get(entity_id, {})


class HybridRetriever:
    """
    Unified hybrid search engine combining dense, sparse, and entity retrieval.
    """

    def __init__(
        self,
        model_name: str = "paraphrase-multilingual-mpnet-base-v2",
        db_path: Optional[str] = None,
        index_path: Optional[Path] = None,
        kg_path: Optional[Path] = None,
        dense_weight: float = 0.5,
        sparse_weight: float = 0.5,
    ):
        """
        Initialize hybrid retriever.

        Args:
            model_name: Embedding model name
            db_path: Path to Chroma database
            index_path: Path to BM25 index
            kg_path: Path to knowledge graph
            dense_weight: Weight for dense results (0-1)
            sparse_weight: Weight for sparse results (0-1)
        """
        self.model_name = model_name
        self.dense_weight = dense_weight
        self.sparse_weight = sparse_weight
        self.normalize_weights()

        self.dense_retriever = DenseRetriever(model_name, db_path)
        self.sparse_retriever = SparseRetriever(index_path)
        self.kg_indexer = KGEntityIndexer(kg_path)

        self.documents = {}
        self.search_stats = {
            "total_searches": 0,
            "avg_latency_ms": 0,
            "dense_hits": 0,
            "sparse_hits": 0,
            "hybrid_hits": 0,
        }

    def normalize_weights(self) -> None:
        """Normalize weights to sum to 1.0."""
        total = self.dense_weight + self.sparse_weight
        if total > 0:
            self.dense_weight /= total
            self.sparse_weight /= total

    async def initialize(self, kg_data: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize all components."""
        try:
            # Initialize dense retriever
            if not await self.dense_retriever.initialize():
                logger.warning("Dense retriever initialization failed")

            # Load KG if provided
            if kg_data:
                await self.kg_indexer.load_kg(kg_data)

            return True
        except Exception as e:
            logger.error(f"Hybrid retriever initialization failed: {e}")
            return False

    async def index_documents(self, documents: List[Dict[str, Any]]) -> bool:
        """
        Index documents in all retrieval methods.

        Args:
            documents: List of documents with 'doc_id' and 'text'

        Returns:
            Success status
        """
        try:
            # Store documents
            for doc in documents:
                doc_id = doc.get("doc_id", "")
                self.documents[doc_id] = doc

            # Index in dense retriever
            dense_ok = await self.dense_retriever.add_documents(documents)

            # Index in sparse retriever
            sparse_ok = await self.sparse_retriever.add_documents(documents)

            # Index entity mentions in KG
            self.kg_indexer.index_entity_mentions(documents)

            logger.info(f"Indexed {len(documents)} documents (dense: {dense_ok}, sparse: {sparse_ok})")
            return dense_ok and sparse_ok
        except Exception as e:
            logger.error(f"Failed to index documents: {e}")
            return False

    async def search(
        self,
        query: str,
        top_k: int = 5,
        use_dense: bool = True,
        use_sparse: bool = True,
        use_entity: bool = False,
    ) -> Dict[str, Any]:
        """
        Perform hybrid search.

        Args:
            query: Query text
            top_k: Number of results
            use_dense: Use dense retrieval
            use_sparse: Use sparse retrieval
            use_entity: Use entity retrieval

        Returns:
            Search results with metadata
        """
        start_time = time.time()

        try:
            dense_results = []
            sparse_results = []
            entity_results = []

            # Parallel search
            tasks = []

            if use_dense:
                tasks.append(("dense", self.dense_retriever.search(query, top_k)))
            if use_sparse:
                tasks.append(("sparse", self.sparse_retriever.search(query, top_k)))

            if tasks:
                task_dict = dict(tasks)
                results = await asyncio.gather(*[task[1] for task in tasks], return_exceptions=True)

                for i, (name, _) in enumerate(tasks):
                    if isinstance(results[i], Exception):
                        logger.error(f"{name} search error: {results[i]}")
                    else:
                        if name == "dense":
                            dense_results = results[i]
                        elif name == "sparse":
                            sparse_results = results[i]

            # Combine and rank results
            combined_results = self._combine_results(dense_results, sparse_results, top_k)

            # Add entity context if requested
            if use_entity:
                combined_results = self._add_entity_context(combined_results)

            latency_ms = (time.time() - start_time) * 1000

            # Update stats
            self.search_stats["total_searches"] += 1
            self.search_stats["dense_hits"] += len(dense_results)
            self.search_stats["sparse_hits"] += len(sparse_results)
            self.search_stats["hybrid_hits"] += len(combined_results)

            return {
                "query": query,
                "results": combined_results,
                "top_k": top_k,
                "latency_ms": latency_ms,
                "sources": {
                    "dense": len(dense_results),
                    "sparse": len(sparse_results),
                },
                "stats": self.search_stats,
            }
        except Exception as e:
            logger.error(f"Hybrid search failed: {e}")
            return {
                "query": query,
                "results": [],
                "error": str(e),
                "latency_ms": (time.time() - start_time) * 1000,
            }

    def _combine_results(
        self,
        dense_results: List[Dict[str, Any]],
        sparse_results: List[Dict[str, Any]],
        top_k: int,
    ) -> List[Dict[str, Any]]:
        """Combine and re-rank dense and sparse results."""
        # Normalize scores
        dense_norm = self._normalize_scores(dense_results)
        sparse_norm = self._normalize_scores(sparse_results)

        # Create result map
        result_map = {}

        # Add dense results
        for result in dense_norm:
            doc_id = result.get("doc_id", "")
            if doc_id not in result_map:
                result_map[doc_id] = {
                    "doc_id": doc_id,
                    "text": result.get("text", ""),
                    "metadata": result.get("metadata", {}),
                    "dense_score": 0,
                    "sparse_score": 0,
                    "sources": set(),
                }
            result_map[doc_id]["dense_score"] = result.get("score", 0)
            result_map[doc_id]["sources"].add("dense")

        # Add sparse results
        for result in sparse_norm:
            doc_id = result.get("doc_id", "")
            if doc_id not in result_map:
                result_map[doc_id] = {
                    "doc_id": doc_id,
                    "text": result.get("text", ""),
                    "metadata": result.get("metadata", {}),
                    "dense_score": 0,
                    "sparse_score": 0,
                    "sources": set(),
                }
            result_map[doc_id]["sparse_score"] = result.get("score", 0)
            result_map[doc_id]["sources"].add("sparse")

        # Calculate hybrid scores
        for doc_id, result in result_map.items():
            dense_score = result["dense_score"] * self.dense_weight
            sparse_score = result["sparse_score"] * self.sparse_weight
            result["hybrid_score"] = dense_score + sparse_score
            result["sources"] = list(result["sources"])

        # Sort by hybrid score
        sorted_results = sorted(result_map.values(), key=lambda x: x.get("hybrid_score", 0), reverse=True)

        return sorted_results[:top_k]

    def _combine_results_dedup(
        self,
        dense_results: List[Dict[str, Any]],
        sparse_results: List[Dict[str, Any]],
        top_k: int,
    ) -> List[Dict[str, Any]]:
        """Combine results with deduplication by similarity."""
        all_results = dense_results + sparse_results
        if not all_results:
            return []

        # Simple deduplication: group by doc_id
        seen = set()
        combined = []

        for result in all_results:
            doc_id = result.get("doc_id", "")
            if doc_id not in seen:
                seen.add(doc_id)
                combined.append(result)

        return combined[:top_k]

    def _normalize_scores(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Normalize scores to 0-1 range."""
        if not results:
            return []

        scores = [r.get("score", 0) for r in results]
        min_score = min(scores) if scores else 0
        max_score = max(scores) if scores else 1
        score_range = max_score - min_score if max_score > min_score else 1

        normalized = []
        for result in results:
            result_copy = result.copy()
            score = result.get("score", 0)
            normalized_score = (score - min_score) / score_range if score_range > 0 else 1
            result_copy["score"] = normalized_score
            normalized.append(result_copy)

        return normalized

    def _add_entity_context(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Add entity context to results."""
        for result in results:
            text = result.get("text", "").lower()
            entities = [ent_id for ent_id in self.kg_indexer.entities if ent_id.lower() in text]

            if entities:
                result["entities"] = entities
                result["entity_context"] = [self.kg_indexer.get_entity_info(ent) for ent in entities]

        return results

    async def search_boolean(self, query: str, top_k: int = 5) -> Dict[str, Any]:
        """Search with Boolean operators (sparse only)."""
        start_time = time.time()

        try:
            sparse_results = await self.sparse_retriever.search_boolean(query, top_k)

            latency_ms = (time.time() - start_time) * 1000

            return {
                "query": query,
                "results": sparse_results,
                "top_k": top_k,
                "latency_ms": latency_ms,
                "method": "boolean",
            }
        except Exception as e:
            logger.error(f"Boolean search failed: {e}")
            return {"query": query, "results": [], "error": str(e)}

    def save(self) -> None:
        """Save indices to disk."""
        self.sparse_retriever.save()
        logger.info("Indices saved")

    def get_stats(self) -> Dict[str, Any]:
        """Get retrieval statistics."""
        return {
            "search_stats": self.search_stats,
            "dense_index_size": len(self.dense_retriever.documents),
            "sparse_index_size": self.sparse_retriever.index.total_docs,
            "kg_entities": len(self.kg_indexer.entities),
            "sparse_index_stats": self.sparse_retriever.index.get_stats(),
        }
