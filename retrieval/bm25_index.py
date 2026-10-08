"""BM25 sparse index for keyword-based retrieval with N-gram support."""

import json
import logging
import math
import pickle
from collections import Counter, defaultdict
from pathlib import Path
from typing import List, Dict, Optional, Set, Tuple, Any
import re

logger = logging.getLogger(__name__)


class BM25Index:
    """
    BM25 implementation for keyword-based retrieval.
    Supports phrase queries, N-grams, and TF-IDF scoring.
    """

    def __init__(
        self,
        k1: float = 1.5,
        b: float = 0.75,
        min_term_freq: int = 1,
        max_ngram: int = 3,
    ):
        """
        Initialize BM25 index.

        Args:
            k1: BM25 saturation parameter (default: 1.5)
            b: BM25 length normalization parameter (default: 0.75)
            min_term_freq: Minimum term frequency to include
            max_ngram: Maximum N-gram size (1-3)
        """
        self.k1 = k1
        self.b = b
        self.min_term_freq = min_term_freq
        self.max_ngram = max_ngram

        # Index structures
        self.documents: Dict[str, Dict[str, Any]] = {}  # doc_id -> doc data
        self.inverted_index: Dict[str, Set[str]] = defaultdict(set)  # term -> doc_ids
        self.term_freq: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))  # doc_id -> term -> count
        self.doc_lengths: Dict[str, int] = {}  # doc_id -> length
        self.doc_field_lengths: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))  # doc_id -> field -> length
        self.idf: Dict[str, float] = {}  # term -> idf
        self.total_docs = 0
        self.avg_doc_length = 0.0

        # N-gram index
        self.ngram_index: Dict[str, Set[str]] = defaultdict(set)  # ngram -> doc_ids
        self.phrase_index: Dict[str, Set[str]] = defaultdict(set)  # phrase -> doc_ids

        # Statistics
        self.index_stats = {
            "total_docs": 0,
            "total_terms": 0,
            "total_ngrams": 0,
            "avg_doc_length": 0.0,
            "index_size_mb": 0.0,
        }

    def add_document(
        self,
        doc_id: str,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
        fields: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        Add a document to the index.

        Args:
            doc_id: Unique document identifier
            text: Document text to index
            metadata: Additional metadata
            fields: Field-specific text (title, content, etc.)
        """
        if not text:
            logger.warning(f"Skipping empty document: {doc_id}")
            return

        # Store document
        self.documents[doc_id] = {
            "text": text,
            "metadata": metadata or {},
            "fields": fields or {},
        }

        # Tokenize main text
        tokens = self._tokenize(text)
        self.doc_lengths[doc_id] = len(tokens)

        # Index tokens
        for token in tokens:
            self.term_freq[doc_id][token] += 1
            self.inverted_index[token].add(doc_id)

        # Index N-grams
        self._index_ngrams(doc_id, tokens)

        # Index fields separately
        if fields:
            for field_name, field_text in fields.items():
                field_tokens = self._tokenize(field_text)
                self.doc_field_lengths[doc_id][field_name] = len(field_tokens)
                for token in field_tokens:
                    # Boost field tokens by field name
                    boosted_token = f"{field_name}:{token}"
                    self.term_freq[doc_id][boosted_token] += 1
                    self.inverted_index[boosted_token].add(doc_id)

        self.total_docs += 1

    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text into terms."""
        # Convert to lowercase
        text = text.lower()
        # Remove special characters, keep alphanumeric and spaces
        text = re.sub(r"[^\w\s]", " ", text)
        # Split into tokens
        tokens = text.split()
        return [t for t in tokens if len(t) > 1]  # Filter single char tokens

    def _index_ngrams(self, doc_id: str, tokens: List[str]) -> None:
        """Index N-grams from tokens."""
        # Unigrams already indexed via term_freq
        # Add bigrams and trigrams
        for n in range(2, min(self.max_ngram + 1, len(tokens) + 1)):
            for i in range(len(tokens) - n + 1):
                ngram = " ".join(tokens[i : i + n])
                self.ngram_index[ngram].add(doc_id)

    def build_index(self) -> None:
        """
        Build the index after adding all documents.
        Calculates IDF and other statistics.
        """
        if not self.documents:
            logger.warning("No documents to index")
            return

        # Calculate IDF
        self.idf = {}
        for term, doc_set in self.inverted_index.items():
            # IDF = log(N / df)
            df = len(doc_set)
            if df >= self.min_term_freq:
                self.idf[term] = math.log(self.total_docs / df)
            else:
                # Remove low-frequency terms
                del self.inverted_index[term]

        # Calculate average document length
        if self.doc_lengths:
            self.avg_doc_length = sum(self.doc_lengths.values()) / len(self.doc_lengths)

        # Update statistics
        self.index_stats = {
            "total_docs": self.total_docs,
            "total_terms": len(self.idf),
            "total_ngrams": len(self.ngram_index),
            "avg_doc_length": self.avg_doc_length,
        }

        logger.info(f"Index built: {self.total_docs} docs, {len(self.idf)} terms, {len(self.ngram_index)} ngrams")

    def search(self, query: str, top_k: int = 10, use_ngrams: bool = True) -> List[Dict[str, Any]]:
        """
        Search for documents matching the query.

        Args:
            query: Search query
            top_k: Number of results to return
            use_ngrams: Whether to use N-gram matching

        Returns:
            List of search results ranked by score
        """
        if not self.idf:
            logger.warning("Index not built. Call build_index() first.")
            return []

        # Parse query
        query_tokens = self._tokenize(query)
        if not query_tokens:
            return []

        # Check for phrase query (quoted terms)
        phrase_match = self._search_phrase(query, use_ngrams)

        # Regular BM25 search
        bm25_scores = self._calculate_bm25_scores(query_tokens)

        # Combine results
        results = self._combine_results(bm25_scores, phrase_match)

        # Sort by score
        results = sorted(results, key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    def _calculate_bm25_scores(self, query_tokens: List[str]) -> Dict[str, float]:
        """Calculate BM25 scores for documents."""
        scores = defaultdict(float)

        for query_term in query_tokens:
            if query_term not in self.idf:
                continue

            idf = self.idf[query_term]
            doc_set = self.inverted_index.get(query_term, set())

            for doc_id in doc_set:
                freq = self.term_freq[doc_id].get(query_term, 0)
                doc_length = self.doc_lengths[doc_id]

                # BM25 formula
                numerator = freq * (self.k1 + 1)
                denominator = freq + self.k1 * (1 - self.b + self.b * (doc_length / self.avg_doc_length))

                score = idf * (numerator / denominator)
                scores[doc_id] += score

        return scores

    def _search_phrase(self, query: str, use_ngrams: bool = True) -> Dict[str, float]:
        """Search for phrase queries (quoted terms)."""
        scores = defaultdict(float)

        # Extract quoted phrases
        phrases = re.findall(r'"([^"]+)"', query)

        for phrase in phrases:
            phrase_tokens = self._tokenize(phrase)
            phrase_ngram = " ".join(phrase_tokens)

            if phrase_ngram in self.ngram_index:
                # Boost documents containing the phrase
                for doc_id in self.ngram_index[phrase_ngram]:
                    scores[doc_id] += len(phrase_tokens) * 2  # Boost phrase matches

        return scores

    def _combine_results(
        self, bm25_scores: Dict[str, float], phrase_scores: Dict[str, float]
    ) -> List[Dict[str, Any]]:
        """Combine BM25 and phrase scores."""
        all_doc_ids = set(bm25_scores.keys()) | set(phrase_scores.keys())
        results = []

        for doc_id in all_doc_ids:
            bm25_score = bm25_scores.get(doc_id, 0)
            phrase_score = phrase_scores.get(doc_id, 0)
            combined_score = bm25_score + phrase_score

            results.append(
                {
                    "doc_id": doc_id,
                    "score": combined_score,
                    "bm25_score": bm25_score,
                    "phrase_score": phrase_score,
                    "text": self.documents[doc_id]["text"][:500],  # Preview
                    "metadata": self.documents[doc_id]["metadata"],
                }
            )

        return results

    def search_boolean(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Support Boolean queries with AND, OR, NOT.

        Example:
            "north AND water" - docs with both terms
            "north OR west" - docs with either term
            "north NOT bedroom" - docs with north but not bedroom

        Args:
            query: Boolean query string
            top_k: Number of results

        Returns:
            Matching documents
        """
        # Parse Boolean query
        # Simple implementation - can be extended
        parts = re.split(r"\s+(AND|OR|NOT)\s+", query.lower())

        if len(parts) == 1:
            # No Boolean operators, treat as regular search
            return self.search(query, top_k)

        # Process Boolean query
        result_set = None
        current_op = "AND"

        for i, part in enumerate(parts):
            if part in ("AND", "OR", "NOT"):
                current_op = part
            else:
                term = part.strip()
                if term not in self.idf:
                    continue

                term_docs = self.inverted_index[term]

                if result_set is None:
                    result_set = term_docs.copy()
                elif current_op == "AND":
                    result_set = result_set & term_docs
                elif current_op == "OR":
                    result_set = result_set | term_docs
                elif current_op == "NOT":
                    result_set = result_set - term_docs

        if result_set is None:
            return []

        # Score the result set
        query_tokens = self._tokenize(query.replace(" AND ", " ").replace(" OR ", " ").replace(" NOT ", " "))
        scores = self._calculate_bm25_scores(query_tokens)

        results = [
            {
                "doc_id": doc_id,
                "score": scores.get(doc_id, 0),
                "text": self.documents[doc_id]["text"][:500],
                "metadata": self.documents[doc_id]["metadata"],
            }
            for doc_id in result_set
        ]

        return sorted(results, key=lambda x: x["score"], reverse=True)[:top_k]

    def save(self, path: Path) -> None:
        """Save index to disk."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        index_data = {
            "documents": self.documents,
            "inverted_index": {k: list(v) for k, v in self.inverted_index.items()},
            "term_freq": dict(self.term_freq),
            "doc_lengths": self.doc_lengths,
            "idf": self.idf,
            "ngram_index": {k: list(v) for k, v in self.ngram_index.items()},
            "params": {
                "k1": self.k1,
                "b": self.b,
                "min_term_freq": self.min_term_freq,
                "max_ngram": self.max_ngram,
            },
            "stats": self.index_stats,
        }

        with open(path, "w") as f:
            json.dump(index_data, f, indent=2)

        logger.info(f"Index saved to {path}")

    def load(self, path: Path) -> bool:
        """Load index from disk."""
        path = Path(path)
        if not path.exists():
            logger.error(f"Index file not found: {path}")
            return False

        try:
            with open(path, "r") as f:
                index_data = json.load(f)

            self.documents = index_data["documents"]
            self.inverted_index = {k: set(v) for k, v in index_data["inverted_index"].items()}
            self.term_freq = defaultdict(lambda: defaultdict(int), {k: defaultdict(int, v) for k, v in index_data["term_freq"].items()})
            self.doc_lengths = index_data["doc_lengths"]
            self.idf = index_data["idf"]
            self.ngram_index = {k: set(v) for k, v in index_data["ngram_index"].items()}

            # Restore parameters
            params = index_data.get("params", {})
            self.k1 = params.get("k1", 1.5)
            self.b = params.get("b", 0.75)
            self.min_term_freq = params.get("min_term_freq", 1)
            self.max_ngram = params.get("max_ngram", 3)

            # Restore statistics
            self.total_docs = len(self.documents)
            if self.doc_lengths:
                self.avg_doc_length = sum(self.doc_lengths.values()) / len(self.doc_lengths)
            self.index_stats = index_data.get("stats", {})

            logger.info(f"Index loaded from {path}")
            return True
        except Exception as e:
            logger.error(f"Failed to load index: {e}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        """Get index statistics."""
        return {
            **self.index_stats,
            "parameters": {
                "k1": self.k1,
                "b": self.b,
                "min_term_freq": self.min_term_freq,
                "max_ngram": self.max_ngram,
            },
        }
