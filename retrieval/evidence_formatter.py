"""Evidence formatter for RAG results."""

import logging
from typing import List, Dict, Optional, Any

logger = logging.getLogger(__name__)


class EvidenceFormatter:
    """
    Formats retrieved evidence for use in Claude prompts.
    Handles chunking, summarization, and context building.
    """

    def __init__(self, max_context_tokens: int = 10000):
        """
        Initialize evidence formatter.

        Args:
            max_context_tokens: Maximum tokens for context
        """
        self.max_context_tokens = max_context_tokens
        self.chunks_per_context = 5

    def format_evidence(self, retrieval_results: List[Dict[str, Any]]) -> str:
        """
        Format retrieved evidence into a readable context string.

        Args:
            retrieval_results: List of retrieval results

        Returns:
            Formatted evidence text
        """
        if not retrieval_results:
            return ""

        formatted = "RETRIEVED EVIDENCE:\n" + "=" * 50 + "\n\n"

        for i, result in enumerate(retrieval_results, 1):
            content = result.get("content", result.get("text", ""))
            metadata = result.get("metadata", {})
            score = result.get("score", 0)

            formatted += f"[Evidence {i}] (Score: {score:.2f})\n"
            if metadata.get("source"):
                formatted += f"Source: {metadata['source']}\n"
            if metadata.get("section"):
                formatted += f"Section: {metadata['section']}\n"

            # Truncate content if too long
            if len(content) > 500:
                content = content[:500] + "..."

            formatted += f"{content}\n"
            formatted += "-" * 30 + "\n\n"

        return formatted

    def format_evidence_compact(self, retrieval_results: List[Dict[str, Any]]) -> str:
        """
        Format evidence in compact form.

        Args:
            retrieval_results: List of retrieval results

        Returns:
            Compact formatted evidence
        """
        if not retrieval_results:
            return ""

        formatted = "Evidence: "
        snippets = []

        for result in retrieval_results[:3]:  # Limit to top 3
            content = result.get("content", result.get("text", ""))
            if len(content) > 100:
                content = content[:100] + "..."
            snippets.append(content)

        formatted += " | ".join(snippets)
        return formatted

    def format_evidence_with_metadata(self, retrieval_results: List[Dict[str, Any]]) -> List[Dict]:
        """
        Format evidence preserving metadata.

        Args:
            retrieval_results: List of retrieval results

        Returns:
            List of evidence items with metadata
        """
        formatted_items = []

        for result in retrieval_results:
            item = {
                "content": result.get("content", result.get("text", "")),
                "score": result.get("score", 0),
                "source": result.get("metadata", {}).get("source", "unknown"),
                "section": result.get("metadata", {}).get("section", "unknown"),
                "metadata": result.get("metadata", {}),
            }
            formatted_items.append(item)

        return formatted_items

    def build_context_string(
        self,
        retrieval_results: List[Dict[str, Any]],
        query: str,
        include_query: bool = True,
    ) -> str:
        """
        Build a complete context string for Claude prompt.

        Args:
            retrieval_results: Retrieved evidence
            query: Original query
            include_query: Whether to include the query

        Returns:
            Complete context string
        """
        context = ""

        if include_query:
            context += f"Query: {query}\n"
            context += "=" * 50 + "\n\n"

        context += self.format_evidence(retrieval_results)

        return context

    def filter_by_score(
        self, retrieval_results: List[Dict[str, Any]], threshold: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Filter retrieval results by similarity score.

        Args:
            retrieval_results: Retrieved results
            threshold: Score threshold

        Returns:
            Filtered results
        """
        filtered = [r for r in retrieval_results if r.get("score", 0) >= threshold]
        logger.info(f"Filtered {len(retrieval_results)} results to {len(filtered)} above threshold {threshold}")
        return filtered

    def deduplicate_results(self, retrieval_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Remove duplicate or near-duplicate results.

        Args:
            retrieval_results: Retrieved results

        Returns:
            Deduplicated results
        """
        seen_content = set()
        deduplicated = []

        for result in retrieval_results:
            content = result.get("content", result.get("text", ""))
            # Simple deduplication by exact match
            content_hash = hash(content[:100])  # Use first 100 chars for hash

            if content_hash not in seen_content:
                seen_content.add(content_hash)
                deduplicated.append(result)

        logger.info(f"Deduplicated {len(retrieval_results)} results to {len(deduplicated)}")
        return deduplicated

    def rank_by_relevance(
        self,
        retrieval_results: List[Dict[str, Any]],
        query: str,
    ) -> List[Dict[str, Any]]:
        """
        Re-rank results by relevance to query.

        Args:
            retrieval_results: Retrieved results
            query: Original query

        Returns:
            Re-ranked results
        """
        # Simple re-ranking by score (already done by retriever)
        # Can be extended with more sophisticated ranking
        ranked = sorted(retrieval_results, key=lambda x: x.get("score", 0), reverse=True)
        return ranked

    def create_evidence_summary(self, retrieval_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create a summary of evidence results.

        Args:
            retrieval_results: Retrieved results

        Returns:
            Summary dictionary
        """
        summary = {
            "total_results": len(retrieval_results),
            "average_score": 0,
            "sources": set(),
            "sections": set(),
            "top_content_samples": [],
        }

        if retrieval_results:
            scores = [r.get("score", 0) for r in retrieval_results]
            summary["average_score"] = sum(scores) / len(scores)

            for result in retrieval_results:
                metadata = result.get("metadata", {})
                if metadata.get("source"):
                    summary["sources"].add(metadata["source"])
                if metadata.get("section"):
                    summary["sections"].add(metadata["section"])

                # Keep top samples
                if len(summary["top_content_samples"]) < 3:
                    summary["top_content_samples"].append(
                        result.get("content", result.get("text", ""))[:200]
                    )

        summary["sources"] = list(summary["sources"])
        summary["sections"] = list(summary["sections"])

        return summary
