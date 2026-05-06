"""LangGraph workflow skeleton."""

from typing import Literal

from langgraph.graph import StateGraph, END

from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.agents.supervisor import SupervisorAgent
from multi_agent_research_lab.agents.researcher import ResearcherAgent
from multi_agent_research_lab.agents.analyst import AnalystAgent
from multi_agent_research_lab.agents.writer import WriterAgent


class MultiAgentWorkflow:
    """Builds and runs the multi-agent graph."""

    def build(self):
        """Create a LangGraph graph."""
        builder = StateGraph(ResearchState)

        # Add nodes
        builder.add_node(
            "supervisor", lambda state: SupervisorAgent().run(state))
        builder.add_node(
            "researcher", lambda state: ResearcherAgent().run(state))
        builder.add_node("analyst", lambda state: AnalystAgent().run(state))
        builder.add_node("writer", lambda state: WriterAgent().run(state))

        # Start at supervisor
        builder.set_entry_point("supervisor")

        # Define routing from supervisor
        def route(state: ResearchState) -> Literal["researcher", "analyst", "writer", "__end__"]:
            last_route = state.route_history[-1]
            if last_route == "done":
                return END
            return last_route

        builder.add_conditional_edges(
            "supervisor",
            route,
            {
                "researcher": "researcher",
                "analyst": "analyst",
                "writer": "writer",
                END: END
            }
        )

        # Worker nodes always return to supervisor
        builder.add_edge("researcher", "supervisor")
        builder.add_edge("analyst", "supervisor")
        builder.add_edge("writer", "supervisor")

        return builder.compile()

    def run(self, state: ResearchState) -> ResearchState:
        """Execute the graph and return final state."""
        graph = self.build()
        result = graph.invoke(state)
        # LangGraph invoke returns a dictionary if use StateGraph(schema)
        # We need to ensure we return a ResearchState object.
        if isinstance(result, dict):
            return ResearchState(**result)
        return result
