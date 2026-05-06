"""Optional critic agent skeleton for bonus work."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.errors import StudentTodoError
from multi_agent_research_lab.core.state import ResearchState


class CriticAgent(BaseAgent):
    """Optional fact-checking and safety-review agent."""

    name = "critic"

    def run(self, state: ResearchState) -> ResearchState:
        """Validate final answer and append findings."""
        llm = LLMClient()

        system_prompt = (
            "You are a rigorous fact-checker. Review the answer against research notes. "
            "Verify all claims are cited and accurate."
        )
        user_prompt = (
            f"Notes:\n{state.research_notes}\n\n"
            f"Answer:\n{state.final_answer}\n\n"
            "Review findings:"
        )

        from multi_agent_research_lab.services.llm_client import LLMClient
        llm = LLMClient()
        response = llm.complete(system_prompt, user_prompt)
        state.add_trace_event("critic_review", {"content": response.content})
        return state
