"""
Chroma Vector Database Setup for Vastu Shastra Texts
Complete pipeline from raw texts to embedded vector database.
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import List, Dict, Tuple
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from data_processing.text_processor import ExtractedText, chunk_vastu_texts, save_chunks_to_jsonl
from vectorization.chroma_vectorizer import ChromaVectorizer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class VastuVectorDBSetup:
    """
    Complete setup pipeline for Vastu vector database.
    """

    def __init__(
        self,
        raw_texts_dir: Path,
        output_dir: Path,
        batch_size: int = 1000
    ):
        """
        Initialize setup.

        Args:
            raw_texts_dir: Directory containing raw .txt files
            output_dir: Directory for vector database output
            batch_size: Batch size for vectorization
        """
        self.raw_texts_dir = Path(raw_texts_dir)
        self.output_dir = Path(output_dir)
        self.batch_size = batch_size

        self.output_dir.mkdir(parents=True, exist_ok=True)

    def load_raw_texts(self) -> List[ExtractedText]:
        """
        Load all raw text files from directory.

        Returns:
            List of ExtractedText objects
        """
        logger.info(f"Loading raw texts from {self.raw_texts_dir}")

        extracted_texts = []
        text_files = list(self.raw_texts_dir.glob("*.txt"))

        logger.info(f"Found {len(text_files)} text files")

        for file_path in sorted(text_files):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()

                if not content:
                    logger.warning(f"Empty file: {file_path.name}")
                    continue

                # Extract metadata from file (header lines)
                lines = content.split('\n')
                title = file_path.stem
                chapter = None
                section = None

                # Try to parse metadata from file header
                for line in lines[:10]:
                    if line.startswith('Title:'):
                        title = line.replace('Title:', '').strip()
                    elif line.startswith('Chapter:'):
                        chapter = line.replace('Chapter:', '').strip()
                    elif line.startswith('Section:'):
                        section = line.replace('Section:', '').strip()

                extracted = ExtractedText(
                    text=content,
                    source_file=file_path.name,
                    chapter=chapter or title,
                    section=section,
                    confidence=0.95
                )

                extracted_texts.append(extracted)
                logger.info(
                    f"Loaded: {file_path.name} "
                    f"({len(content)} chars)"
                )

            except Exception as e:
                logger.error(f"Error loading {file_path.name}: {e}")

        logger.info(f"Successfully loaded {len(extracted_texts)} texts")
        return extracted_texts

    async def chunk_and_save(
        self,
        extracted_texts: List[ExtractedText],
        chunks_output: Path
    ) -> List[Dict]:
        """
        Chunk texts and save to JSONL format.

        Args:
            extracted_texts: List of extracted texts
            chunks_output: Output path for chunks

        Returns:
            List of chunk dictionaries
        """
        logger.info(f"Chunking {len(extracted_texts)} texts...")

        # Use text processor to chunk
        chunks = await chunk_vastu_texts(
            extracted_texts,
            target_size=1200,
            max_size=2000,
            min_size=500
        )

        logger.info(f"Generated {len(chunks)} chunks")

        # Save to JSONL
        chunks_output.parent.mkdir(parents=True, exist_ok=True)
        saved_count = await save_chunks_to_jsonl(chunks, chunks_output)
        logger.info(f"Saved {saved_count} chunks to {chunks_output}")

        # Convert chunks to dict format for vectorizer
        chunk_dicts = [
            {
                'id': f"chunk_{chunk.chunk_index}",
                'text': chunk.text,
                'source_file': chunk.source_file,
                'chapter': chunk.chapter,
                'section': chunk.section,
                'principle_type': chunk.principle_type,
                'is_verse': chunk.is_verse,
                'char_count': chunk.char_count,
                'token_estimate': chunk.token_estimate,
                'verse_number': chunk.verse_number,
                'entities': chunk.entities,
                'sanskrit_terms': chunk.sanskrit_terms,
            }
            for chunk in chunks
        ]

        return chunk_dicts

    def vectorize_chunks(
        self,
        chunks: List[Dict],
        db_path: Path
    ) -> Tuple[int, int, float]:
        """
        Vectorize chunks and create Chroma database.

        Args:
            chunks: List of chunk dictionaries
            db_path: Path for database

        Returns:
            Tuple of (successful, failed, time)
        """
        logger.info(f"Vectorizing {len(chunks)} chunks...")

        vectorizer = ChromaVectorizer(
            db_path=db_path,
            batch_size=self.batch_size,
            device="cpu"
        )

        # Create collection
        vectorizer.create_collection(collection_name="vastu_texts")

        # Vectorize
        successful, failed, total_time = vectorizer.vectorize_chunks(chunks)

        # Save metadata
        metadata_path = self.output_dir / "vastu_embeddings_index.json"
        vectorizer.save_index_metadata(metadata_path)

        # Print stats
        vectorizer.print_stats()

        return successful, failed, total_time

    def validate_database(self, db_path: Path) -> bool:
        """
        Validate the created database.

        Args:
            db_path: Path to database

        Returns:
            True if valid, False otherwise
        """
        logger.info("Validating database...")

        try:
            # Load vectorizer to access collection
            vectorizer = ChromaVectorizer(db_path=db_path)

            # Test queries
            test_queries = [
                "vastu principles and directional alignment",
                "temple construction and sacred geometry",
                "remedial measures for vastu defects"
            ]

            logger.info("Testing similarity search...")
            for query in test_queries:
                results = vectorizer.search(query, top_k=3)
                logger.info(f"Query: '{query}' - Found {len(results)} results")

                if results:
                    for i, result in enumerate(results[:1]):
                        logger.debug(
                            f"  Result {i+1}: Similarity={result['similarity']:.3f}, "
                            f"Source={result['metadata'].get('source_file', 'N/A')}"
                        )

            logger.info("Database validation successful")
            return True

        except Exception as e:
            logger.error(f"Validation failed: {e}")
            return False

    async def run_full_pipeline(self) -> Dict:
        """
        Run complete pipeline: load -> chunk -> vectorize.

        Returns:
            Dictionary with results
        """
        logger.info("="*70)
        logger.info("VASTU VECTOR DATABASE SETUP - COMPLETE PIPELINE")
        logger.info("="*70)

        try:
            # Step 1: Load raw texts
            logger.info("\nStep 1: Loading raw texts...")
            extracted_texts = self.load_raw_texts()

            if not extracted_texts:
                logger.error("No texts loaded")
                return {'success': False, 'error': 'No texts loaded'}

            # Step 2: Chunk texts
            logger.info("\nStep 2: Chunking texts...")
            chunks_output = self.output_dir / "chunks.jsonl"
            chunks = await self.chunk_and_save(extracted_texts, chunks_output)

            if not chunks:
                logger.error("No chunks generated")
                return {'success': False, 'error': 'No chunks generated'}

            # Step 3: Vectorize chunks
            logger.info("\nStep 3: Vectorizing chunks...")
            db_path = self.output_dir / "chroma_vastu_db"
            successful, failed, vectorization_time = self.vectorize_chunks(
                chunks,
                db_path
            )

            # Step 4: Validate database
            logger.info("\nStep 4: Validating database...")
            valid = self.validate_database(db_path)

            # Results
            results = {
                'success': valid,
                'stats': {
                    'texts_loaded': len(extracted_texts),
                    'chunks_generated': len(chunks),
                    'chunks_vectorized': successful,
                    'chunks_failed': failed,
                    'vectorization_time': vectorization_time,
                    'database_path': str(db_path),
                    'chunks_file': str(chunks_output),
                }
            }

            logger.info("\n" + "="*70)
            logger.info("PIPELINE COMPLETE")
            logger.info("="*70)
            logger.info(f"Texts Loaded: {len(extracted_texts)}")
            logger.info(f"Chunks Generated: {len(chunks)}")
            logger.info(f"Chunks Vectorized: {successful}")
            logger.info(f"Chunks Failed: {failed}")
            logger.info(f"Vectorization Time: {vectorization_time:.2f}s")
            logger.info(f"Database Location: {db_path}")

            return results

        except Exception as e:
            logger.error(f"Pipeline failed: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}


async def main():
    """Main entry point."""
    # Paths
    raw_texts_dir = Path("/Users/ajaynawale/vastu_shastra_dss/data/raw_texts")
    output_dir = Path("/Users/ajaynawale/vastu_shastra_dss/vdb/chroma_vastu_db")

    # Setup
    setup = VastuVectorDBSetup(
        raw_texts_dir=raw_texts_dir,
        output_dir=output_dir.parent,
        batch_size=1000
    )

    # Run pipeline
    results = await setup.run_full_pipeline()

    # Print results
    if results['success']:
        print("\n✅ Setup successful!")
        print(json.dumps(results['stats'], indent=2))
    else:
        print(f"\n❌ Setup failed: {results.get('error', 'Unknown error')}")
        return 1

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
