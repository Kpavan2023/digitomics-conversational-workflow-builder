"""Service responsible for extracting workflow-relevant information."""

from __future__ import annotations

from app.llm.base import LLMProvider
from app.schemas.extraction import ExtractionResult
from app.schemas.workflow import WorkflowState


async def extract_information(
    user_message: str,
    state: WorkflowState,
    llm: LLMProvider,
) -> ExtractionResult:
    """
    Extract workflow-relevant facts from the user's latest message.

    The LLM is responsible for understanding the user's language.
    The canonical workflow state remains owned by the application.
    """
    return await llm.extract_information(
        user_message=user_message,
        current_state=state,
    )