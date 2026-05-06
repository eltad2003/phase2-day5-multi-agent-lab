import pytest

from multi_agent_research_lab.agents import SupervisorAgent
from multi_agent_research_lab.core.errors import StudentTodoError
from multi_agent_research_lab.core.schemas import ResearchQuery
from multi_agent_research_lab.core.state import ResearchState


def test_supervisor_logic() -> None:
    """Test the supervisor's routing logic instead of expecting a TODO error."""
    state = ResearchState(request=ResearchQuery(
        query="Explain multi-agent systems"))

    # Test 1: Should route to researcher first
    state = SupervisorAgent().run(state)
    assert state.route_history[-1] == "researcher"

    # Test 2: Should route to analyst after research
    state.research_notes = "Some notes"
    state = SupervisorAgent().run(state)
    assert state.route_history[-1] == "analyst"
