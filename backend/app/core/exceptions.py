"""Application exception hierarchy."""

from typing import Any


class WorkflowBuilderError(Exception):
    """Base exception for all application errors."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class LLMError(WorkflowBuilderError):
    """LLM provider failure (timeout, invalid output, unavailable)."""


class ValidationError(WorkflowBuilderError):
    """Workflow state or schema validation failure."""


class ConversationNotFoundError(WorkflowBuilderError):
    """Conversation ID not found in the database."""


class ExtractionError(WorkflowBuilderError):
    """Information extraction failure."""


class WorkflowGenerationError(WorkflowBuilderError):
    """Workflow generation failure due to incomplete or invalid state."""
