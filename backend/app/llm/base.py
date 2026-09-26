"""
Abstract LLM provider interface.

The application communicates with language models through this
interface. This keeps the rest of the application independent
of a specific LLM provider.

The LLM is responsible for understanding natural language and
extracting information. The application remains responsible for
canonical state, requirements, validation, ambiguity, and
workflow readiness.
"""

from __future__ import annotations

import abc

from app.schemas.extraction import ExtractionResult
from app.schemas.workflow import WorkflowState


class LLMProvider(abc.ABC):
    """
    Abstract interface for language-model providers.
    """

    @abc.abstractmethod
    async def extract_information(
        self,
        user_message: str,
        current_state: WorkflowState,
    ) -> ExtractionResult:
        """
        Extract information explicitly provided by the user.

        The implementation must not invent missing information.

        Parameters
        ----------
        user_message:
            The user's latest message.

        current_state:
            Current canonical workflow state, which can provide
            conversational context for interpreting short answers.

        Returns
        -------
        ExtractionResult
            Structured information extracted from the message.
        """
        raise NotImplementedError

    @abc.abstractmethod
    async def detect_ambiguity(
        self,
        user_message: str,
        current_state: WorkflowState,
    ) -> list[str]:
        """
        Detect ambiguous language in the user's message.

        This is a language-understanding capability. Final
        application-level ambiguity and conflict validation is
        handled by the deterministic ambiguity service.
        """
        raise NotImplementedError

    @abc.abstractmethod
    async def generate_question(
        self,
        missing_field: str,
        context: WorkflowState,
    ) -> str:
        """
        Generate a natural-language clarification question for
        missing information.
        """
        raise NotImplementedError