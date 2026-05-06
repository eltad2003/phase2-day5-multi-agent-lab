"""Analyst agent skeleton."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.llm_client import LLMClient


class AnalystAgent(BaseAgent):
    """Turns research notes into structured insights."""

    name = "analyst"

    def run(self, state: ResearchState) -> ResearchState:
        """Populate `state.analysis_notes`."""
        llm = LLMClient()

        system_prompt = (
            "You are a strategic analyst. Your task is to extract key claims and "
            "provide structured insights from research notes. Focus on accuracy and relevance."
        )
        user_prompt = f"Research Notes:\n{state.research_notes}\n\nExtract key insights/claims:"

        response = llm.complete(system_prompt, user_prompt)
        state.analysis_notes = response.content

        state.add_trace_event("analyst_complete", {
                              "input_tokens": response.input_tokens})
        return state
