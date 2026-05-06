from __future__ import annotations

import os
from collections.abc import Iterator
from contextlib import contextmanager
from time import perf_counter
from typing import Any

from multi_agent_research_lab.core.config import get_settings


@contextmanager
def trace_span(name: str, attributes: dict[str, Any] | None = None) -> Iterator[dict[str, Any]]:
    """Span context with Langfuse integration fallback."""

    settings = get_settings()
    langfuse_public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
    langfuse_secret_key = os.getenv("LANGFUSE_SECRET_KEY")
    langfuse_host = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")

    langfuse = None
    if langfuse_public_key and langfuse_secret_key:
        try:
            from langfuse import Langfuse
            langfuse = Langfuse(langfuse_public_key,
                                langfuse_secret_key, langfuse_host)
        except ImportError:
            pass

    started = perf_counter()
    span: dict[str, Any] = {
        "name": name, "attributes": attributes or {}, "duration_seconds": None}

    # Langfuse span start
    lf_span = None
    if langfuse:
        lf_span = langfuse.span(
            name=name,
            metadata=attributes
        )

    try:
        yield span
    finally:
        duration = perf_counter() - started
        span["duration_seconds"] = duration
        if lf_span:
            lf_span.end(metadata={"duration_seconds": duration})
            langfuse.flush()
