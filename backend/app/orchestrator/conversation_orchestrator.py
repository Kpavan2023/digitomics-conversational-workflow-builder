"""Conversation orchestrator.

Coordinates the complete conversational workflow-building pipeline:

1. Extract information from the user's message.
2. Normalize and merge extracted facts into canonical state.
3. Evaluate ambiguities and conflicts.
4. Evaluate workflow requirements.
5. Ask the next clarification question when information is missing.
6. Validate the workflow when all required information is available.
7. Generate the final structured workflow.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from app.llm.base import LLMProvider
from app.schemas.conversation import Conversation
from app.schemas.message import Message, MessageRole
from app.schemas.requirement import (
    Requirement,
    RequirementStatus,
)
from app.schemas.workflow import (
    GeneratedWorkflow,
    WorkflowState,
    WorkflowStatus,
)

from app.services.ambiguity_service import AmbiguityService
from app.services.extraction_service import extract_information
from app.services.normalization_service import NormalizationService
from app.services.question_service import QuestionService
from app.services.requirement_service import RequirementService
from app.services.validation_service import ValidationService
from app.services.workflow_service import WorkflowService


class ConversationOrchestrator:
    """Coordinates the complete workflow-building conversation."""

    def __init__(self, llm: LLMProvider) -> None:
        self.llm = llm

        self.normalization_service = NormalizationService()
        self.ambiguity_service = AmbiguityService()
        self.requirement_service = RequirementService()
        self.question_service = QuestionService()
        self.validation_service = ValidationService()
        self.workflow_service = WorkflowService()

    async def process_message(
        self,
        conversation: Conversation,
        user_text: str,
    ) -> tuple[
        Conversation,
        str,
        GeneratedWorkflow | None,
        list[Requirement],
    ]:
        """Process one user message through the complete pipeline."""

        # ---------------------------------------------------------
        # 1. Extract information from the latest user message
        # ---------------------------------------------------------

        extraction = await extract_information(
            user_message=user_text,
            state=conversation.state,
            llm=self.llm,
        )

        # ---------------------------------------------------------
        # 2. Merge extracted information into canonical state
        # ---------------------------------------------------------

        state = self.normalization_service.normalize_and_merge(
            current_state=conversation.state,
            extraction=extraction,
        )

        # ---------------------------------------------------------
        # 3. Evaluate ambiguities and conflicts
        # ---------------------------------------------------------

        ambiguities, conflicts = self.ambiguity_service.evaluate(
            state
        )

        state.ambiguities = ambiguities
        state.conflicts = conflicts

        # ---------------------------------------------------------
        # 4. Evaluate workflow requirements
        # ---------------------------------------------------------
        #
        # Requirements must always be calculated from the current
        # canonical WorkflowState.
        #
        # Do NOT read requirements from WorkflowState because the
        # canonical state does not store a "requirements" field.
        # RequirementService is the source of truth.
        # ---------------------------------------------------------

        requirements = self.requirement_service.evaluate(state)

        # ---------------------------------------------------------
        # Store unresolved requirement IDs in the canonical state
        # ---------------------------------------------------------

        state.missing_requirements = [
            requirement.id
            for requirement in requirements
            if (
                requirement.required
                and requirement.status
                in {
                    RequirementStatus.MISSING,
                    RequirementStatus.AMBIGUOUS,
                    RequirementStatus.CONFLICTING,
                }
            )
        ]

        # ---------------------------------------------------------
        # 5. Decide what should happen next
        # ---------------------------------------------------------

        workflow: GeneratedWorkflow | None = None

        # ---------------------------------------------------------
        # Case A: Conflicting information
        # ---------------------------------------------------------

        if conflicts:
            state.status = WorkflowStatus.COLLECTING

            assistant_message = self._build_conflict_question(
                conflicts
            )

        # ---------------------------------------------------------
        # Case B: Ambiguous information
        # ---------------------------------------------------------

        elif ambiguities:
            state.status = WorkflowStatus.COLLECTING

            assistant_message = self._build_ambiguity_question(
                ambiguities
            )

        # ---------------------------------------------------------
        # Case C: All required information has been collected
        # ---------------------------------------------------------

        elif not self._has_unresolved_required_requirements(
            requirements
        ):
            state.status = WorkflowStatus.READY

            valid = self.validation_service.is_workflow_complete(
                state
            )

            if not valid:
                state.status = WorkflowStatus.COLLECTING

                assistant_message = (
                    "I have the main information, but the workflow "
                    "still needs some details before it can be generated."
                )

            else:
                # -------------------------------------------------
                # Generate candidate workflow
                # -------------------------------------------------

                candidate_workflow = self.workflow_service.generate(
                    state
                )

                # -------------------------------------------------
                # Validate generated workflow
                # -------------------------------------------------

                workflow_valid, errors = (
                    self.validation_service.validate_workflow(
                        candidate_workflow,
                        state,
                    )
                )

                if not workflow_valid:
                    state.status = WorkflowStatus.COLLECTING

                    assistant_message = (
                        "I have most of the required information, "
                        "but the workflow still has some issues to resolve: "
                        f"{'; '.join(errors)}"
                    )

                else:
                    # ---------------------------------------------
                    # Workflow successfully generated
                    # ---------------------------------------------

                    state.status = WorkflowStatus.GENERATED

                    # No requirement is being collected anymore.
                    state.active_requirement_id = None

                    # There should be no unresolved requirements
                    # when the workflow has been successfully generated.
                    state.missing_requirements = []

                    workflow = candidate_workflow

                    assistant_message = (
                        "All required information has been collected. "
                        "I've generated the workflow."
                    )

        # ---------------------------------------------------------
        # Case D: Information is still missing
        # ---------------------------------------------------------

        else:
            state.status = WorkflowStatus.COLLECTING

            assistant_message = await self._get_next_question(
                state=state,
                requirements=requirements,
            )

        # ---------------------------------------------------------
        # 6. Persist conversation messages and state
        # ---------------------------------------------------------

        user_message = self._make_message(
            role=MessageRole.USER,
            content=user_text,
        )

        assistant_message_model = self._make_message(
            role=MessageRole.ASSISTANT,
            content=assistant_message,
        )

        updated_conversation = conversation.model_copy(
            deep=True
        )

        updated_conversation.state = state

        updated_conversation.messages = [
            *conversation.messages,
            user_message,
            assistant_message_model,
        ]

        updated_conversation.updated_at = datetime.now(
            timezone.utc
        )

        return (
            updated_conversation,
            assistant_message,
            workflow,
            requirements,
        )

    # =============================================================
    # Requirement handling
    # =============================================================

    async def _get_next_question(
        self,
        state: WorkflowState,
        requirements: list[Requirement],
    ) -> str:
        """
        Select the next eligible clarification requirement.

        The selected requirement becomes the active conversational
        requirement so the application knows which piece of
        information is currently being collected.
        """

        requirement = self.question_service.get_next_requirement(
            state=state,
            requirements=requirements,
        )

        if requirement is None:
            state.active_requirement_id = None

            return (
                "I need a little more information before "
                "I can build the workflow."
            )

        # ---------------------------------------------------------
        # Remember the current conversational step
        # ---------------------------------------------------------

        state.active_requirement_id = requirement.id

        return (
            requirement.question
            or requirement.description
        )

    # =============================================================
    # Conflict handling
    # =============================================================

    def _build_conflict_question(
        self,
        conflicts: list[str],
    ) -> str:
        """Build a clarification question for a conflict."""

        conflict = conflicts[0]

        return (
            "I found a conflict in the information provided: "
            f"{conflict} Which value should I use?"
        )

    # =============================================================
    # Ambiguity handling
    # =============================================================

    def _build_ambiguity_question(
        self,
        ambiguities: list[str],
    ) -> str:
        """Build a clarification question for an ambiguity."""

        ambiguity = ambiguities[0]

        return (
            f"I need to clarify one detail: {ambiguity}"
        )

    # =============================================================
    # Requirement helpers
    # =============================================================

    @staticmethod
    def _has_unresolved_required_requirements(
        requirements: list[Requirement],
    ) -> bool:
        """
        Return True when at least one required requirement
        remains unresolved.
        """

        return any(
            requirement.required
            and requirement.status != RequirementStatus.SATISFIED
            for requirement in requirements
        )

    # =============================================================
    # Message helper
    # =============================================================

    @staticmethod
    def _make_message(
        role: MessageRole,
        content: str,
    ) -> Message:
        """Create a conversation message."""

        return Message(
            id=str(uuid.uuid4()),
            role=role,
            content=content,
            created_at=datetime.now(timezone.utc),
        )


async def process_message(
    conversation: Conversation,
    user_text: str,
    llm: LLMProvider,
) -> tuple[
    Conversation,
    str,
    GeneratedWorkflow | None,
    list[Requirement],
]:
    """
    Convenience wrapper for processing a conversation message.
    """

    orchestrator = ConversationOrchestrator(llm)

    return await orchestrator.process_message(
        conversation=conversation,
        user_text=user_text,
    )