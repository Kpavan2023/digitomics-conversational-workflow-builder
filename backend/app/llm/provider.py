"""LLM provider factory — selects provider based on configuration."""

from __future__ import annotations

from app.core.config import settings
from app.llm.base import LLMProvider
from app.llm.rule_based import RuleBasedProvider


def get_llm_provider() -> LLMProvider:
    """Return the configured LLM provider instance.

    Currently only the rule-based provider is implemented. To add OpenAI or
    another provider, implement the LLMProvider interface and add a branch here.
    """
    if settings.LLM_PROVIDER == "rule_based" or not settings.OPENAI_API_KEY:
        return RuleBasedProvider()
    # Future: return OpenAIProvider(api_key=..., model=...)
    return RuleBasedProvider()
