"""
Chroma Vector Database Vectorizer for Vastu Shastra Texts
Embedded local vector database with bilingual support.
"""

import json
import time
import logging
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

import numpy as np
from sentence_transformers import SentenceTransformer
import chromadb

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class VectorizationStats:
    """Statistics about vectorization process"""
    total_chunks: int
    chunks_embedded: int
    chunks_failed: int
    total_characters: int
    total_tokens: int
    total_embedding_time: float
    avg_embedding_time_per_chunk: float
    embedding_dimensions: int
    database_size_mb: float
    success_rate: float
    batch_count: int
    avg_batch_size: int
    timestamp: str


class ChromaVectorizer:
    """
    Complete Chroma vectorizer for Vastu Shastra texts.
    Handles batch processing, bilingual embeddings, and error handling.
    """

    def __init__(
        self,
        db_path: Path,
        model_name: str = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
        batch_size: int = 1000,
        device: str = "cpu"
    ):
        """
        Initialize vectorizer.

        Args:
            db_path: Path to store Chroma database
            model_name: Sentence transformer model for embeddings
            batch_size: Number of chunks to process in parallel
            device: 'cpu' or 'cuda' for computation
        """
        self.db_path = Path(db_path)
        self.db_path.mkdir(parents=True, exist_ok=True)

        # Load embedding model
        logger.info(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name, device=device)
        self.embedding_dim = self.model.get_sentence_embedding_dimension()
        logger.info(f"Embedding dimension: {self.embedding_dim}")

        self.batch_size = batch_size
        self.device = device

        # Initialize Chroma client
        self.client = chromadb.PersistentClient(path=str(self.db_path / "chroma_db"))
        self.collection = None

        # Stats tracking
        self.stats = {
            'total_chunks': 0,
            'chunks_embedded': 0,
            'chunks_failed': 0,
            'total_characters': 0,
            'total_tokens': 0,
            'total_time': 0.0,
            'batches': 0,
            'errors': []
        }

    def create_collection(self, collection_name: str = "vastu_texts") -> None:
        """Create or get Chroma collection."""
        logger.info(f"Creating collection: {collection_name}")

        # Delete existing collection if it exists
        try:
            self.client.delete_collection(name=collection_name)
            logger.info("Deleted existing collection")
        except Exception as e:
            logger.debug(f"No existing collection to delete: {e}")

        # Create new collection with metadata
        self.collection = self.client.create_collection(
            name=collection_name,
            metadata={
                "hnsw:space": "cosine",
                "description": "Vastu Shastra texts with multilingual embeddings",
                "model": "paraphrase-multilingual-mpnet-base-v2",
                "embedding_dimension": self.embedding_dim,
                "created_at": datetime.now().isoformat()
            }
        )
        logger.info(f"Collection created: {collection_name}")

    def embed_batch(self, texts: List[str]) -> np.ndarray:
        """
        Embed a batch of texts using sentence-transformers.

        Args:
            texts: List of text strings to embed

        Returns:
            NumPy array of embeddings
        """
        if not texts:
            return np.array([])

        try:
            # Encode with attention to multilingual content
            embeddings = self.model.encode(
                texts,
                batch_size=32,
                show_progress_bar=False,
                convert_to_numpy=True
            )
            return embeddings
        except Exception as e:
            logger.error(f"Error embedding batch: {e}")
            return np.array([])

    def vectorize_chunks(
        self,
        chunks: List[Dict],
        progress_interval: int = 100
    ) -> Tuple[int, int, float]:
        """
        Vectorize a list of chunks and store in Chroma.

        Args:
            chunks: List of chunk dictionaries with 'text', 'id', and metadata
            progress_interval: Print progress every N chunks

        Returns:
            Tuple of (successful_count, failed_count, total_time)
        """
        if not chunks:
            logger.warning("No chunks to vectorize")
            return 0, 0, 0.0

        logger.info(f"Starting vectorization of {len(chunks)} chunks")
        self.stats['total_chunks'] = len(chunks)

        start_time = time.time()
        batch_texts = []
        batch_data = []
        successful = 0
        failed = 0

        for idx, chunk in enumerate(chunks):
            try:
                text = chunk.get('text', '').strip()
                chunk_id = chunk.get('id', f"chunk_{idx}")

                if not text:
                    logger.warning(f"Empty text in chunk {chunk_id}")
                    failed += 1
                    continue

                # Prepare metadata (Chroma requires non-None values)
                metadata = {
                    'source_file': chunk.get('source_file') or '',
                    'chapter': chunk.get('chapter') or '',
                    'principle_type': chunk.get('principle_type') or '',
                    'is_verse': str(chunk.get('is_verse', False)),
                    'char_count': str(chunk.get('char_count', 0)),
                    'token_estimate': str(chunk.get('token_estimate', 0)),
                    'verse_number': str(chunk.get('verse_number') or ''),
                }

                batch_texts.append(text)
                batch_data.append({
                    'id': chunk_id,
                    'text': text,
                    'metadata': metadata,
                    'char_count': chunk.get('char_count', 0),
                    'token_estimate': chunk.get('token_estimate', 0),
                })

                # Track stats
                self.stats['total_characters'] += len(text)
                self.stats['total_tokens'] += chunk.get('token_estimate', 0)

                # Process batch when reaches batch size
                if len(batch_texts) >= self.batch_size or idx == len(chunks) - 1:
                    embedded = self._process_batch(batch_texts, batch_data)
                    successful += embedded
                    failed += len(batch_texts) - embedded

                    batch_texts = []
                    batch_data = []
                    self.stats['batches'] += 1

                    if (idx + 1) % progress_interval == 0:
                        elapsed = time.time() - start_time
                        logger.info(
                            f"Progress: {idx + 1}/{len(chunks)} "
                            f"({100 * (idx + 1) / len(chunks):.1f}%) "
                            f"Successful: {successful}, Failed: {failed}, "
                            f"Time: {elapsed:.1f}s"
                        )

            except Exception as e:
                logger.error(f"Error processing chunk {idx}: {e}")
                failed += 1
                self.stats['errors'].append({
                    'chunk_idx': idx,
                    'error': str(e)
                })

        total_time = time.time() - start_time
        self.stats['chunks_embedded'] = successful
        self.stats['chunks_failed'] = failed
        self.stats['total_time'] = total_time

        logger.info(
            f"Vectorization complete: {successful} successful, "
            f"{failed} failed in {total_time:.1f}s"
        )

        return successful, failed, total_time

    def _process_batch(self, texts: List[str], batch_data: List[Dict]) -> int:
        """
        Process a single batch: embed and add to collection.

        Args:
            texts: List of text strings
            batch_data: List of data dictionaries with metadata

        Returns:
            Number of successfully processed items
        """
        try:
            # Embed batch
            embeddings = self.embed_batch(texts)

            if len(embeddings) == 0:
                logger.error(f"Failed to embed batch of {len(texts)} texts")
                return 0

            # Add to collection
            ids = [d['id'] for d in batch_data]
            metadatas = [d['metadata'] for d in batch_data]
            documents = [d['text'] for d in batch_data]

            self.collection.add(
                ids=ids,
                embeddings=embeddings.tolist(),
                documents=documents,
                metadatas=metadatas
            )

            logger.debug(f"Added {len(texts)} embeddings to collection")
            return len(texts)

        except Exception as e:
            logger.error(f"Batch processing error: {e}")
            return 0

    def search(
        self,
        query_text: str,
        top_k: int = 5,
        threshold: float = 0.3
    ) -> List[Dict]:
        """
        Search for similar chunks.

        Args:
            query_text: Query string
            top_k: Number of results to return
            threshold: Minimum similarity score (0-1)

        Returns:
            List of matching chunks with scores
        """
        # Load collection if not initialized
        if not self.collection:
            try:
                self.collection = self.client.get_collection(name="vastu_texts")
                logger.info("Loaded existing collection: vastu_texts")
            except Exception as e:
                logger.error(f"Cannot load collection: {e}")
                return []

        try:
            # Embed query
            query_embedding = self.embed_batch([query_text])

            if len(query_embedding) == 0:
                logger.error("Failed to embed query")
                return []

            # Search
            results = self.collection.query(
                query_embeddings=query_embedding.tolist(),
                n_results=top_k
            )

            # Process results
            matches = []
            if results['ids'] and len(results['ids']) > 0:
                for i, (chunk_id, distance) in enumerate(
                    zip(results['ids'][0], results['distances'][0])
                ):
                    # Convert distance to similarity (cosine)
                    similarity = 1 - distance

                    if similarity >= threshold:
                        matches.append({
                            'id': chunk_id,
                            'text': results['documents'][0][i],
                            'similarity': float(similarity),
                            'metadata': results['metadatas'][0][i]
                        })

            logger.debug(f"Found {len(matches)} matches for query")
            return matches

        except Exception as e:
            logger.error(f"Search error: {e}")
            return []

    def get_stats(self) -> VectorizationStats:
        """Generate vectorization statistics."""
        # Try to load from metadata file first (check both locations)
        metadata_file = self.db_path / "vastu_embeddings_index.json"
        if not metadata_file.exists():
            metadata_file = self.db_path.parent / "vastu_embeddings_index.json"

        if metadata_file.exists() and self.stats['total_chunks'] == 0:
            try:
                with open(metadata_file, 'r') as f:
                    data = json.load(f)
                    stats_data = data.get('statistics', {})
                    self.stats.update({
                        'total_chunks': stats_data.get('total_chunks', 0),
                        'chunks_embedded': stats_data.get('chunks_embedded', 0),
                        'chunks_failed': stats_data.get('chunks_failed', 0),
                        'total_characters': stats_data.get('total_characters', 0),
                        'total_tokens': stats_data.get('total_tokens', 0),
                        'total_time': stats_data.get('total_embedding_time', 0),
                        'batches': 1,  # Estimated
                    })
            except Exception as e:
                logger.debug(f"Could not load stats from metadata: {e}")

        avg_batch_size = (
            self.stats['total_chunks'] / self.stats['batches']
            if self.stats['batches'] > 0 else 0
        )
        avg_time_per_chunk = (
            self.stats['total_time'] / self.stats['chunks_embedded']
            if self.stats['chunks_embedded'] > 0 else 0
        )
        success_rate = (
            100 * self.stats['chunks_embedded'] / self.stats['total_chunks']
            if self.stats['total_chunks'] > 0 else 0
        )

        # Estimate database size
        db_size_mb = 0
        try:
            db_dir = self.db_path / "chroma_db"
            if db_dir.exists():
                total_size = sum(
                    f.stat().st_size
                    for f in db_dir.rglob('*')
                    if f.is_file()
                )
                db_size_mb = total_size / (1024 * 1024)
        except Exception as e:
            logger.warning(f"Could not calculate DB size: {e}")

        return VectorizationStats(
            total_chunks=self.stats['total_chunks'],
            chunks_embedded=self.stats['chunks_embedded'],
            chunks_failed=self.stats['chunks_failed'],
            total_characters=self.stats['total_characters'],
            total_tokens=self.stats['total_tokens'],
            total_embedding_time=self.stats['total_time'],
            avg_embedding_time_per_chunk=avg_time_per_chunk,
            embedding_dimensions=self.embedding_dim,
            database_size_mb=db_size_mb,
            success_rate=success_rate,
            batch_count=self.stats['batches'],
            avg_batch_size=int(avg_batch_size),
            timestamp=datetime.now().isoformat()
        )

    def save_index_metadata(self, output_path: Path) -> None:
        """
        Save index metadata to JSON file.

        Args:
            output_path: Path to save metadata
        """
        stats = self.get_stats()
        metadata = {
            'vectorizer': {
                'model': 'sentence-transformers/paraphrase-multilingual-mpnet-base-v2',
                'embedding_dimension': self.embedding_dim,
                'device': self.device,
                'batch_size': self.batch_size,
            },
            'statistics': asdict(stats),
            'database': {
                'path': str(self.db_path),
                'collection_name': 'vastu_texts',
                'backend': 'chroma'
            }
        }

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        logger.info(f"Index metadata saved to {output_path}")

    def print_stats(self) -> None:
        """Print formatted statistics."""
        stats = self.get_stats()

        print("\n" + "="*70)
        print("CHROMA VECTORIZATION STATISTICS")
        print("="*70)

        print(f"\nProcessing Statistics:")
        print(f"  Total Chunks:                {stats.total_chunks:,}")
        print(f"  Chunks Embedded:             {stats.chunks_embedded:,}")
        print(f"  Chunks Failed:               {stats.chunks_failed:,}")
        print(f"  Success Rate:                {stats.success_rate:.1f}%")

        print(f"\nContent Statistics:")
        print(f"  Total Characters:            {stats.total_characters:,}")
        print(f"  Total Tokens (estimated):    {stats.total_tokens:,}")
        print(f"  Average Chars per Chunk:     {stats.total_characters / stats.chunks_embedded if stats.chunks_embedded > 0 else 0:.0f}")

        print(f"\nEmbedding Statistics:")
        print(f"  Embedding Dimension:         {stats.embedding_dimensions}")
        print(f"  Total Embedding Time:        {stats.total_embedding_time:.2f}s")
        print(f"  Avg Time per Chunk:          {stats.avg_embedding_time_per_chunk:.4f}s")
        print(f"  Chunks per Second:           {stats.chunks_embedded / stats.total_embedding_time if stats.total_embedding_time > 0 else 0:.1f}")

        print(f"\nBatch Processing:")
        print(f"  Total Batches:               {stats.batch_count}")
        print(f"  Average Batch Size:          {stats.avg_batch_size}")

        print(f"\nDatabase:")
        print(f"  Location:                    {self.db_path / 'chroma_db'}")
        print(f"  Estimated Size:              {stats.database_size_mb:.2f} MB")

        print(f"\nTimestamp:                     {stats.timestamp}")
        print("="*70 + "\n")
