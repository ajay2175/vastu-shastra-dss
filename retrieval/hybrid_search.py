"""Hybrid search combining keyword and semantic search."""

import logging
from typing import List, Dict, Optional, Any
import re
from collections import Counter

logger = logging.getLogger(__name__)


class HybridSearcher:
    """
    Performs hybrid search combining keyword-based and semantic search.
    Useful for balancing precision and recall.
    """

    def __init__(self, semantic_weight: float = 0.6, keyword_weight: float = 0.4):
        """
        Initialize hybrid searcher.

        Args:
            semantic_weight: Weight for semantic search (0-1)
            keyword_weight: Weight for keyword search (0-1)
        """
        self.semantic_weight = semantic_weight
        self.keyword_weight = keyword_weight
        self.retriever = None

    async def hybrid_search(
        self,
        query: str,
        semantic_results: List[Dict[str, Any]],
        keyword_results: List[Dict[str, Any]],
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Combine semantic and keyword search results.

        Args:
            query: Search query
            semantic_results: Results from semantic search
            keyword_results: Results from keyword search
            top_k: Number of final results

        Returns:
            Merged and ranked results
        """
        # Normalize scores
        normalized_semantic = self._normalize_scores(semantic_results)
        normalized_keyword = self._normalize_scores(keyword_results)

        # Create result map
        result_map = {}

        # Add semantic results
        for result in normalized_semantic:
            doc_id = result.get("id", id(result))
            if doc_id not in result_map:
                result_map[doc_id] = result.copy()
            result_map[doc_id]["semantic_score"] = result.get("score", 0)

        # Add keyword results
        for result in normalized_keyword:
            doc_id = result.get("id", id(result))
            if doc_id not in result_map:
                result_map[doc_id] = result.copy()
            result_map[doc_id]["keyword_score"] = result.get("score", 0)

        # Calculate combined scores
        for doc_id, result in result_map.items():
            semantic_score = result.get("semantic_score", 0) * self.semantic_weight
            keyword_score = result.get("keyword_score", 0) * self.keyword_weight
            result["hybrid_score"] = semantic_score + keyword_score

        # Sort by hybrid score
        sorted_results = sorted(result_map.values(), key=lambda x: x.get("hybrid_score", 0), reverse=True)

        return sorted_results[:top_k]

    def keyword_search(self, query: str, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Perform keyword-based search.

        Args:
            query: Search query
            documents: Documents to search

        Returns:
            Keyword search results
        """
        query_terms = self._tokenize_query(query)
        results = []

        for doc in documents:
            content = doc.get("content", doc.get("text", "")).lower()
            score = self._calculate_keyword_score(query_terms, content)

            if score > 0:
                result_doc = doc.copy()
                result_doc["score"] = score
                results.append(result_doc)

        # Sort by score
        results.sort(key=lambda x: x.get("score", 0), reverse=True)
        return results

    def _calculate_keyword_score(self, query_terms: List[str], content: str) -> float:
        """
        Calculate keyword match score.

        Args:
            query_terms: Tokenized query terms
            content: Document content

        Returns:
            Match score (0-1)
        """
        if not query_terms or not content:
            return 0

        content_lower = content.lower()
        match_count = 0

        for term in query_terms:
            if term in content_lower:
                match_count += 1

        return match_count / len(query_terms)

    def _tokenize_query(self, query: str) -> List[str]:
        """
        Tokenize query into terms.

        Args:
            query: Query string

        Returns:
            List of terms
        """
        # Simple tokenization
        terms = re.findall(r"\b\w+\b", query.lower())
        return terms

    def _normalize_scores(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Normalize scores to 0-1 range.

        Args:
            results: Results with scores

        Returns:
            Results with normalized scores
        """
        if not results:
            return []

        scores = [r.get("score", 0) for r in results]
        min_score = min(scores) if scores else 0
        max_score = max(scores) if scores else 1

        # Avoid division by zero
        score_range = max_score - min_score if max_score > min_score else 1

        normalized = []
        for result in results:
            result_copy = result.copy()
            score = result.get("score", 0)
            normalized_score = (score - min_score) / score_range if score_range > 0 else 1
            result_copy["score"] = normalized_score
            normalized.append(result_copy)

        return normalized

    async def analyze_query(self, query: str) -> Dict[str, Any]:
        """
        Analyze query to determine search strategy.

        Args:
            query: Query string

        Returns:
            Query analysis
        """
        analysis = {
            "query": query,
            "query_length": len(query),
            "terms": self._tokenize_query(query),
            "term_count": len(self._tokenize_query(query)),
            "has_quotes": '"' in query,
            "has_wildcards": "*" in query or "?" in query,
        }

        # Determine suggested strategy
        if analysis["has_quotes"]:
            analysis["suggested_strategy"] = "keyword"
        elif analysis["term_count"] > 5:
            analysis["suggested_strategy"] = "semantic"
        else:
            analysis["suggested_strategy"] = "hybrid"

        return analysis

    def rerank_results(
        self,
        results: List[Dict[str, Any]],
        query: str,
        boost_exact_match: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Re-rank results with additional boosting.

        Args:
            results: Results to re-rank
            query: Original query
            boost_exact_match: Boost exact query matches

        Returns:
            Re-ranked results
        """
        reranked = []

        for result in results:
            result_copy = result.copy()
            current_score = result.get("score", 0)

            # Boost exact match
            if boost_exact_match:
                content = result.get("content", result.get("text", "")).lower()
                if query.lower() in content:
                    current_score *= 1.2

            result_copy["score"] = min(current_score, 1.0)  # Cap at 1.0
            reranked.append(result_copy)

        return sorted(reranked, key=lambda x: x.get("score", 0), reverse=True)

    def get_search_stats(
        self, semantic_results: List[Dict], keyword_results: List[Dict]
    ) -> Dict[str, Any]:
        """
        Get statistics about search results.

        Args:
            semantic_results: Semantic search results
            keyword_results: Keyword search results

        Returns:
            Search statistics
        """
        return {
            "semantic_count": len(semantic_results),
            "keyword_count": len(keyword_results),
            "semantic_avg_score": (
                sum(r.get("score", 0) for r in semantic_results) / len(semantic_results)
                if semantic_results
                else 0
            ),
            "keyword_avg_score": (
                sum(r.get("score", 0) for r in keyword_results) / len(keyword_results)
                if keyword_results
                else 0
            ),
        }
