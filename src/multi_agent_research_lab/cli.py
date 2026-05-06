"""Command-line entrypoint for the lab starter."""

from typing import Annotated
from time import perf_counter

import typer
from rich.console import Console
from rich.panel import Panel

from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.errors import StudentTodoError
from multi_agent_research_lab.core.schemas import ResearchQuery
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.graph.workflow import MultiAgentWorkflow
from multi_agent_research_lab.observability.logging import configure_logging
from multi_agent_research_lab.observability.tracing import trace_span
from multi_agent_research_lab.services.llm_client import LLMClient
from multi_agent_research_lab.services.search_client import SearchClient
from multi_agent_research_lab.evaluation.benchmark import run_benchmark
from multi_agent_research_lab.evaluation.report import render_markdown_report

app = typer.Typer(help="Multi-Agent Research Lab starter CLI")
console = Console()


def _init() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)


@app.command()
def baseline(
    query: Annotated[str, typer.Option("--query", "-q", help="Research query")],
) -> None:
    """Run a minimal single-agent baseline."""

    _init()
    with trace_span("baseline_run", {"query": query}) as span:
        started_at = perf_counter()
        request = ResearchQuery(query=query)
        state = ResearchState(request=request)
        state.record_route("baseline")

        search_client = SearchClient()
        llm_client = LLMClient()

        sources = search_client.search(
            request.query, max_results=request.max_sources)
        state.sources = sources
        research_notes = "\n".join(
            f"- {source.title}: {source.snippet} ({source.url})" for source in sources
        )
        state.research_notes = research_notes

        system_prompt = (
            "You are a concise research assistant. Synthesize a technically accurate answer "
            "using the provided sources, and cite them explicitly by title and URL."
        )
        user_prompt = (
            f"Question: {request.query}\n\n"
            f"Audience: {request.audience}\n\n"
            f"Sources:\n{research_notes}"
        )
        response = llm_client.complete(
            system_prompt=system_prompt, user_prompt=user_prompt)
        state.final_answer = response.content
        state.add_trace_event(
            "baseline_metrics",
            {
                "latency_seconds": round(perf_counter() - started_at, 3),
                "input_tokens": response.input_tokens,
                "output_tokens": response.output_tokens,
                "estimated_cost_usd": response.cost_usd,
                "source_count": len(sources),
            },
        )

        console.print(Panel.fit(state.final_answer,
                      title="Single-Agent Baseline"))
        console.print(
            Panel.fit(
                f"Latency: {state.trace[-1]['payload']['latency_seconds']}s\n"
                f"Sources: {len(state.sources)}\n"
                f"Estimated cost: {response.cost_usd or 0.0}",
                title="Baseline Metrics",
            )
        )
        span["attributes"].update({
            "latency": state.trace[-1]["payload"]["latency_seconds"],
            "sources": len(state.sources),
            "cost": response.cost_usd or 0.0
        })


@app.command("multi-agent")
def multi_agent(
    query: Annotated[str, typer.Option("--query", "-q", help="Research query")],
) -> None:
    """Run the multi-agent workflow skeleton."""

    _init()
    state = ResearchState(request=ResearchQuery(query=query))
    workflow = MultiAgentWorkflow()
    try:
        result = workflow.run(state)
    except StudentTodoError as exc:
        console.print(
            Panel.fit(str(exc), title="Expected TODO", style="yellow"))
        raise typer.Exit(code=2) from exc
    console.print(result.model_dump_json(indent=2))


@app.command()
def benchmark(
    query: Annotated[str, typer.Option("--query", "-q", help="Research query")],
) -> None:
    """Run both baseline and multi-agent and generate a report."""

    _init()
    with trace_span("benchmark_suite", {"query": query}) as suite_span:
        console.print("[bold]Starting Benchmark...[/bold]")

        def baseline_runner(q: str):
            with trace_span("benchmark_baseline", {"query": q}) as b_span:
                request = ResearchQuery(query=q)
                state = ResearchState(request=request)
                sc = SearchClient()
                lc = LLMClient()
                sources = sc.search(q)
                state.sources = sources
                res_notes = "\n".join([f"- {s.title}" for s in sources])
                state.research_notes = res_notes
                resp = lc.complete("concise research",
                                   f"Query: {q}\nSources: {res_notes}")
                state.final_answer = resp.content
                state.add_trace_event(
                    "metrics", {"estimated_cost_usd": resp.cost_usd})
                b_span["attributes"]["cost"] = resp.cost_usd or 0.0
                return state

        def multi_agent_runner(q: str):
            with trace_span("benchmark_multi_agent", {"query": q}):
                state = ResearchState(request=ResearchQuery(query=q))
                return MultiAgentWorkflow().run(state)

        results = []

        console.print("Running Baseline...")
        s1, m1 = run_benchmark("Single-Agent (Baseline)",
                               query, baseline_runner)
        results.append(m1)

        console.print("Running Multi-Agent...")
        s2, m2 = run_benchmark("Multi-Agent Workflow",
                               query, multi_agent_runner)
        results.append(m2)

        report = render_markdown_report(results)

        report_path = "reports/benchmark_report.md"
        from pathlib import Path
        Path("reports").mkdir(exist_ok=True)
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report)

        suite_span["attributes"]["report_path"] = report_path
        suite_span["attributes"]["baseline_quality"] = m1.quality_score
        suite_span["attributes"]["multi_agent_quality"] = m2.quality_score
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)

    console.print(Panel.fit(f"Report saved to {report_path}", style="green"))
    console.print(report)


if __name__ == "__main__":
    app()
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)

    console.print(Panel.fit(f"Report saved to {report_path}", style="green"))
    console.print(report)
