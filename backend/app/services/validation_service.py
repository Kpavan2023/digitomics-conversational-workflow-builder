"""Deterministic validation for workflow state and generated workflows."""

from __future__ import annotations

from app.schemas.workflow import GeneratedWorkflow, WorkflowState
from app.services.requirement_service import RequirementService


class ValidationService:
    """Validates workflow readiness and generated workflow structure."""

    def __init__(self) -> None:
        self.requirement_service = RequirementService()

    def is_workflow_complete(self, state: WorkflowState) -> bool:
        """
        Determine whether enough information has been collected
        to generate the workflow.

        This decision is deterministic and does not depend on
        the LLM deciding that the workflow is complete.
        """
        if state.conflicts:
            return False

        if state.ambiguities:
            return False

        requirements = self.requirement_service.evaluate(state)

        return not any(
            requirement.required and requirement.status != "satisfied"
            for requirement in requirements
        )

    def validate_workflow(
        self,
        workflow: GeneratedWorkflow,
        state: WorkflowState,
    ) -> tuple[bool, list[str]]:
        """
        Validate the final generated workflow against the
        collected workflow state.
        """

        errors: list[str] = []

        # ---------------------------------------------------------
        # State-level validation
        # ---------------------------------------------------------

        if not state.trigger.type:
            errors.append("Missing trigger type.")

        if not state.actions:
            errors.append("Workflow must contain at least one action.")

        if state.conflicts:
            errors.append(
                f"Unresolved conflicts: {len(state.conflicts)}"
            )

        if state.ambiguities:
            errors.append(
                f"Unresolved ambiguities: {len(state.ambiguities)}"
            )

        requirements = self.requirement_service.evaluate(state)

        unresolved_required = [
            requirement
            for requirement in requirements
            if requirement.required
            and requirement.status != "satisfied"
        ]

        for requirement in unresolved_required:
            errors.append(
                f"Unresolved required requirement: {requirement.id}"
            )

        # ---------------------------------------------------------
        # Graph structure validation
        # ---------------------------------------------------------

        node_ids = [node.id for node in workflow.nodes]

        if len(node_ids) != len(set(node_ids)):
            errors.append("Duplicate node IDs found.")

        for edge in workflow.edges:
            if edge.from_node not in node_ids:
                errors.append(
                    f"Edge references unknown source node: {edge.from_node}"
                )

            if edge.to_node not in node_ids:
                errors.append(
                    f"Edge references unknown target node: {edge.to_node}"
                )

        # ---------------------------------------------------------
        # Required graph nodes
        # ---------------------------------------------------------

        has_trigger = any(
            node.type == "trigger"
            for node in workflow.nodes
        )

        has_action = any(
            node.type == "action"
            for node in workflow.nodes
        )

        if not has_trigger:
            errors.append(
                "Workflow must have at least one trigger node."
            )

        if not has_action:
            errors.append(
                "Workflow must have at least one action node."
            )

        return len(errors) == 0, errors


# -----------------------------------------------------------------
# Backward-compatible function wrappers for existing callers.
# These can be removed once all callers are migrated to the class.
# -----------------------------------------------------------------

_validation_service = ValidationService()


def is_workflow_complete(state: WorkflowState) -> bool:
    return _validation_service.is_workflow_complete(state)


def validate_workflow(
    workflow: GeneratedWorkflow,
    state: WorkflowState,
) -> tuple[bool, list[str]]:
    return _validation_service.validate_workflow(workflow, state)