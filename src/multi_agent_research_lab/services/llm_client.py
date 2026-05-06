"""LLM client abstraction.

Production note: agents should depend on this interface instead of importing an SDK directly.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from textwrap import shorten

from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from multi_agent_research_lab.core.config import get_settings


@dataclass(frozen=True)
class LLMResponse:
    content: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    cost_usd: float | None = None


class LLMClient:
    """Provider-agnostic LLM client with a local fallback."""

    def __init__(self) -> None:
        settings = get_settings()
        self._model = settings.openai_model
        self._api_key = settings.openai_api_key or os.getenv("OPENAI_API_KEY")

    @retry(
        retry=retry_if_exception_type(RuntimeError),
        wait=wait_exponential(multiplier=0.5, min=0.5, max=4),
        stop=stop_after_attempt(3),
        reraise=True,
    )
    def complete(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        """Return a model completion.

        Uses OpenAI when available, otherwise falls back to a deterministic local summary so
        the lab can run without external credentials.
        """

        if self._api_key:
            response = self._complete_with_openai(
                system_prompt=system_prompt, user_prompt=user_prompt)
            if response is not None:
                return response

        return self._complete_with_local_fallback(system_prompt=system_prompt, user_prompt=user_prompt)

    def _complete_with_openai(self, system_prompt: str, user_prompt: str) -> LLMResponse | None:
        try:
            from openai import OpenAI
        except Exception:
            return None

        try:
            client = OpenAI(api_key=self._api_key)
            result = client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
            content = result.choices[0].message.content or ""
            usage = getattr(result, "usage", None)
            input_tokens = getattr(usage, "prompt_tokens", None)
            output_tokens = getattr(usage, "completion_tokens", None)
            cost_usd = self._estimate_cost(input_tokens, output_tokens)
            return LLMResponse(
                content=content.strip(),
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_usd=cost_usd,
            )
        except Exception as exc:
            raise RuntimeError(f"OpenAI completion failed: {exc}") from exc

    def _complete_with_local_fallback(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        summary = self._summarize_prompts(
            system_prompt=system_prompt, user_prompt=user_prompt)
        input_tokens = self._estimate_tokens(
            system_prompt) + self._estimate_tokens(user_prompt)
        output_tokens = self._estimate_tokens(summary)
        return LLMResponse(
            content=summary,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=0.0,
        )

    def _summarize_prompts(self, system_prompt: str, user_prompt: str) -> str:
        topic = self._extract_topic(user_prompt)
        focus = shorten(" ".join(user_prompt.split()),
                        width=240, placeholder="...")
        guidance = shorten(" ".join(system_prompt.split()),
                           width=160, placeholder="...")
        return f"[local-mock:{self._model}] {topic}. Request: {focus}. Guidance: {guidance}"

    def _extract_topic(self, prompt: str) -> str:
        lowered = prompt.lower()
        if "graphrag" in lowered:
            return "GraphRAG research summary"
        if "multi-agent" in lowered or "multi agent" in lowered:
            return "multi-agent research summary"
        if "compare" in lowered:
            return "comparison summary"
        return "research summary"

    def _estimate_tokens(self, text: str) -> int:
        return max(1, len(text.split()))

    def _estimate_cost(self, input_tokens: int | None, output_tokens: int | None) -> float | None:
        if input_tokens is None or output_tokens is None:
            return None
        total_tokens = input_tokens + output_tokens
        return round(total_tokens * 0.00001, 6)
