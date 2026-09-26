"""Normalization service for merging extracted facts into canonical workflow state."""

from __future__ import annotations

from copy import deepcopy

from app.schemas.extraction import ExtractionResult
from app.schemas.workflow import (
    Action,
    Condition,
    Intent,
    Trigger,
    WorkflowState,
)


class NormalizationService:
    """
    Converts extracted information into the canonical WorkflowState
    representation and merges it with the existing state.

    The existing state is never replaced blindly.

    Known information is preserved unless the latest extraction
    explicitly provides an updated value.
    """

    def normalize_and_merge(
        self,
        current_state: WorkflowState,
        extraction: ExtractionResult,
    ) -> WorkflowState:
        """
        Merge the latest extraction into the current workflow state.
        """

        state = deepcopy(current_state)

        # ---------------------------------------------------------
        # Intent
        # ---------------------------------------------------------
        if extraction.intent is not None:
            state.intent = self._merge_intent(
                state.intent,
                extraction.intent,
            )

        # ---------------------------------------------------------
        # Trigger
        # ---------------------------------------------------------
        if extraction.trigger is not None:
            state.trigger = self._merge_trigger(
                state.trigger,
                extraction.trigger,
            )

        # ---------------------------------------------------------
        # Condition decision
        #
        # None means that the latest message did not contain a
        # condition decision, so the existing value must be preserved.
        # ---------------------------------------------------------
        if extraction.condition_enabled is not None:
            state.condition_enabled = (
                extraction.condition_enabled
            )

        # ---------------------------------------------------------
        # Condition
        # ---------------------------------------------------------
        if extraction.condition is not None:
            condition = self._normalize_condition(
                extraction.condition
            )

            state.conditions = self._merge_condition(
                state.conditions,
                condition,
            )

            # A concrete condition explicitly means that the
            # workflow uses a condition.
            state.condition_enabled = True

        # ---------------------------------------------------------
        # Action
        # ---------------------------------------------------------
        if extraction.action is not None:
            action = self._normalize_action(
                extraction.action
            )

            state.actions = self._merge_action(
                state.actions,
                action,
            )

        # ---------------------------------------------------------
        # Duplicate handling
        #
        # None means that the latest message did not provide a
        # duplicate-handling decision, so the existing value must
        # be preserved.
        # ---------------------------------------------------------
        if extraction.duplicate_handling is not None:
            state.duplicate_handling = (
                extraction.duplicate_handling
            )

        # ---------------------------------------------------------
        # A successful state update creates a new state version.
        # ---------------------------------------------------------
        state.version += 1

        return state

    # =============================================================
    # Intent
    # =============================================================

    def _merge_intent(
        self,
        current: Intent,
        extracted,
    ) -> Intent:
        """
        Merge extracted intent into the canonical Intent model.

        Missing values from the latest extraction do not erase
        information that was already collected.
        """

        return Intent(
            goal=(
                extracted.goal
                if extracted.goal is not None
                else current.goal
            ),
            confidence=(
                extracted.confidence
                if extracted.confidence is not None
                else current.confidence
            ),
        )

    # =============================================================
    # Trigger
    # =============================================================

    def _merge_trigger(
        self,
        current: Trigger,
        extracted,
    ) -> Trigger:
        """
        Merge a partially extracted trigger with the existing trigger.

        Existing values are preserved when the latest extraction
        does not provide a replacement.
        """

        return Trigger(
            type=(
                extracted.type
                if extracted.type is not None
                else current.type
            ),
            provider=(
                extracted.provider
                if extracted.provider is not None
                else current.provider
            ),
            configuration={
                **current.configuration,
                **extracted.configuration,
            },
        )

    # =============================================================
    # Condition
    # =============================================================

    def _normalize_condition(
        self,
        extracted,
    ) -> Condition:
        """
        Convert an extracted condition into the canonical
        Condition schema.

        Conditions must be complete before they are stored
        in the canonical state.
        """

        if extracted.field is None:
            raise ValueError(
                "Condition field is required for normalization."
            )

        if extracted.operator is None:
            raise ValueError(
                "Condition operator is required for normalization."
            )

        if extracted.value is None:
            raise ValueError(
                "Condition value is required for normalization."
            )

        return Condition(
            field=extracted.field,
            operator=extracted.operator,
            value=extracted.value,
            currency=extracted.currency,
        )

    def _merge_condition(
        self,
        existing: list[Condition],
        new_condition: Condition,
    ) -> list[Condition]:
        """
        Update an existing condition when it targets the same field.

        Otherwise, append the new condition.
        """

        merged = list(existing)

        for index, condition in enumerate(merged):
            same_field = (
                condition.field == new_condition.field
            )

            if same_field:
                merged[index] = new_condition
                return merged

        merged.append(new_condition)

        return merged

    # =============================================================
    # Action
    # =============================================================

    def _normalize_action(
        self,
        extracted,
    ) -> Action:
        """
        Convert an extracted action into the canonical Action schema.
        """

        if extracted.type is None:
            raise ValueError(
                "Action type is required for normalization."
            )

        return Action(
            type=extracted.type,
            provider=extracted.provider,
            configuration=extracted.configuration,
        )

    def _merge_action(
        self,
        existing: list[Action],
        new_action: Action,
    ) -> list[Action]:
        """
        Merge a newly extracted action into an existing action.

        If an existing action has the same type, newly provided fields
        such as provider and configuration complete that action rather
        than creating a duplicate action.
        """

        merged = list(existing)

        for index, action in enumerate(merged):

            # ---------------------------------------------------------
            # Same action type means this may be an update to the
            # existing action.
            # ---------------------------------------------------------

            if action.type != new_action.type:
                continue

            # ---------------------------------------------------------
            # Merge provider.
            #
            # A newly provided provider should complete a previously
            # missing provider.
            # ---------------------------------------------------------

            provider = (
                new_action.provider
                if new_action.provider is not None
                else action.provider
            )

            # ---------------------------------------------------------
            # Merge configuration.
            # ---------------------------------------------------------

            configuration = {
                **action.configuration,
                **new_action.configuration,
            }

            merged[index] = Action(
                type=action.type,
                provider=provider,
                configuration=configuration,
            )

            return merged

        # No matching action type exists.
        merged.append(new_action)

        return merged