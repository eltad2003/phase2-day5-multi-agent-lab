"""Benchmark report rendering."""

from multi_agent_research_lab.core.schemas import BenchmarkMetrics


def render_markdown_report(metrics: list[BenchmarkMetrics]) -> str:
    """Render benchmark metrics to markdown with analysis."""

    lines = [
        "# Multi-Agent Research Lab: Benchmark Report",
        "",
        "## Performance Metrics",
        "",
        "| Run | Latency (s) | Cost (USD) | Quality | Notes |",
        "|---|---:|---:|---:|---|",
    ]
    for item in metrics:
        cost = "" if item.estimated_cost_usd is None else f"${item.estimated_cost_usd:.4f}"
        quality = "" if item.quality_score is None else f"{item.quality_score:.1f}/10"
        lines.append(
            f"| {item.run_name} | {item.latency_seconds:.2f} | {cost} | {quality} | {item.notes} |")

    lines.extend([
        "",
        "## Analysis",
        "",
        "### Single-Agent Baseline",
        "- **Pros**: Low latency, lower cost.",
        "- **Cons**: Shallow analysis, limited source verification.",
        "",
        "### Multi-Agent Workflow",
        "- **Pros**: Deeper insights, role-based checks, better handling of complex queries.",
        "- **Cons**: Higher latency due to orchestration, slightly higher cost.",
        "",
        "### Recommendation",
        "Use **multi-agent** for high-quality research and complex analysis. Use **single-agent** for simple facts.",
    ])
    return "\n".join(lines) + "\n"
