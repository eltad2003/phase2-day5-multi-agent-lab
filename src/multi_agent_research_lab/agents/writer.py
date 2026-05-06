"""Writer agent skeleton."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.llm_client import LLMClient


class WriterAgent(BaseAgent):
    """Produces final answer from research and analysis notes."""

    name = "writer"

    def run(self, state: ResearchState) -> ResearchState:
        """Populate `state.final_answer`."""
        llm = LLMClient()

        system_prompt = (
            "You are a professional writer. Synthesize the research and analysis into a "
            "clear, comprehensive answer. Cite the specific sources provided in the research notes."
        )
        user_prompt = (
            f"Original Query: {state.request.query}\n"
            f"Research Notes:\n{state.research_notes}\n"
            f"Analysis insights:\n{state.analysis_notes}\n\n"
            "Final Answer:"
        )

        response = llm.complete(system_prompt, user_prompt)
        state.final_answer = response.content

        state.add_trace_event("writer_complete", {
                              "input_tokens": response.input_tokens})
        return state
