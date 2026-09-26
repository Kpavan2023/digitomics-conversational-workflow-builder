from typing import Any

from pydantic import BaseModel, Field


class ExtractedIntent(BaseModel):
    """
    Represents intent information extracted from the user's
    latest message.

    The extraction layer may provide a confidence value, but
    workflow readiness is decided by the application layer.
    """

    goal: str | None = None
    confidence: float | None = None


class ExtractedTrigger(BaseModel):
    """
    Trigger information explicitly identified in the user's
    latest message.
    """

    type: str | None = None
    provider: str | None = None
    configuration: dict[str, Any] = Field(default_factory=dict)


class ExtractedCondition(BaseModel):
    """
    Condition information explicitly identified in the user's
    latest message.

    Fields may be partially populated because a user may provide
    only part of a condition in a single message.
    """

    field: str | None = None
    operator: str | None = None
    value: Any = None
    currency: str | None = None


class ExtractedAction(BaseModel):
    """
    Action information explicitly identified in the user's
    latest message.
    """

    type: str | None = None
    provider: str | None = None
    configuration: dict[str, Any] = Field(default_factory=dict)


class ExtractionResult(BaseModel):
    """
    Information extracted from the user's latest message.

    None means that the latest message did not provide
    that particular piece of information.

    Extraction is intentionally separate from canonical workflow
    state. The extractor may return partial information, while
    normalization and validation determine how that information
    affects the workflow.
    """

    intent: ExtractedIntent | None = None

    trigger: ExtractedTrigger | None = None

    condition_enabled: bool | None = None

    condition: ExtractedCondition | None = None

    action: ExtractedAction | None = None

    duplicate_handling: bool | None = None

    raw_facts: dict[str, Any] = Field(default_factory=dict)