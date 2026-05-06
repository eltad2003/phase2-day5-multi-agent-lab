"""Benchmark skeleton for single-agent vs multi-agent."""

from time import perf_counter
from typing import Callable

from multi_agent_research_lab.core.schemas import BenchmarkMetrics
from multi_agent_research_lab.core.state import ResearchState


Runner = Callable[[str], ResearchState]


def run_benchmark(run_name: str, query: str, runner: Runner) -> tuple[ResearchState, BenchmarkMetrics]:
    """Measure latency and return a descriptive metric object."""

    started = perf_counter()
    state = runner(query)
    latency = perf_counter() - started

    # Calculate estimated cost from trace
    total_cost = 0.0
    for event in state.trace:
        payload = event.get("payload", {})
        total_cost += payload.get("estimated_cost_usd", 0.0) or 0.0

    # Heuristic for quality (e.g., source count + result length)
    quality = min(10.0, (len(state.sources) * 1.5) +
                  (len(state.final_answer or "") / 200))

    metrics = BenchmarkMetrics(
        run_name=run_name,
        latency_seconds=latency,
        estimated_cost_usd=total_cost,
        quality_score=round(quality, 1),
        notes=f"Iterations: {state.iteration}, Sources: {len(state.sources)}"
    )
    return state, metrics
