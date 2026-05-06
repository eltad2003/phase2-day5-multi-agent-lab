"""Researcher agent skeleton."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.search_client import SearchClient


class ResearcherAgent(BaseAgent):
    """Collects sources and creates concise research notes."""

    name = "researcher"

    def run(self, state: ResearchState) -> ResearchState:
        """Populate `state.sources` and `state.research_notes`."""
        search_client = SearchClient()
        sources = search_client.search(
            state.request.query, max_results=state.request.max_sources)

        state.sources = sources
        state.research_notes = "\n".join(
            f"- {s.title}: {s.snippet} ({s.url})" for s in sources
        )

        state.add_trace_event("researcher_complete", {
                              "source_count": len(sources)})
        return state
