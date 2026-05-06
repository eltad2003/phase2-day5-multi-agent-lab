"""Search client abstraction for ResearcherAgent."""

from __future__ import annotations

from urllib.parse import quote_plus

from multi_agent_research_lab.core.schemas import SourceDocument


class SearchClient:
    """Provider-agnostic search client with deterministic mock results."""

    def search(self, query: str, max_results: int = 5) -> list[SourceDocument]:
        """Search for documents relevant to a query.

        The starter repo uses a local mock result set so the rest of the lab can run without
        external search credentials. The structure matches a real search provider response.
        """

        keywords = self._extract_keywords(query)
        sources: list[SourceDocument] = []
        for index in range(max(1, max_results)):
            keyword = keywords[index % len(keywords)]
            sources.append(
                SourceDocument(
                    title=f"{keyword.title()} overview {index + 1}",
                    url=f"https://example.com/search/{quote_plus(keyword)}-{index + 1}",
                    snippet=(
                        f"Mock source about {keyword} and its role in {query}. "
                        f"Includes background, design tradeoffs, and evaluation notes."
                    ),
                    metadata={
                        "source": "mock-search",
                        "query": query,
                        "rank": index + 1,
                    },
                )
            )
        return sources

    def _extract_keywords(self, query: str) -> list[str]:
        words = [word.strip(".,:;!?()[]{}\"'")
                 for word in query.lower().split()]
        keywords = [word for word in words if len(word) > 3]
        if not keywords:
            return ["research"]
        deduplicated: list[str] = []
        for keyword in keywords:
            if keyword not in deduplicated:
                deduplicated.append(keyword)
        return deduplicated[:5]
