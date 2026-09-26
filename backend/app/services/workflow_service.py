"""Workflow service — generates a structured workflow graph from workflow state."""

from __future__ import annotations

from app.schemas.workflow import (
    GeneratedWorkflow,
    WorkflowEdge,
    WorkflowMetadata,
    WorkflowNode,
    WorkflowState,
)


class WorkflowService:
    """Generate a machine-readable workflow graph from validated state."""

    def generate(self, state: WorkflowState) -> GeneratedWorkflow:
        """
        Generate a workflow graph from the canonical workflow state.

        This method only transforms collected information into a
        structured representation. It does not execute the workflow
        or call external services.
        """

        nodes: list[WorkflowNode] = []
        edges: list[WorkflowEdge] = []

        # ---------------------------------------------------------
        # Trigger
        # ---------------------------------------------------------

        trigger_id = "trigger_1"

        trigger_label = self._build_trigger_label(state)

        trigger_configuration = {
            "type": state.trigger.type,
            "provider": state.trigger.provider,
            **state.trigger.configuration,
        }

        # Preserve the duplicate-invoice decision in the generated
        # workflow when the user has explicitly answered it.
        if state.duplicate_handling is not None:
            trigger_configuration["duplicate_handling"] = {
                "enabled": state.duplicate_handling,
                "strategy": (
                    "ignore"
                    if state.duplicate_handling
                    else "process"
                ),
            }

        nodes.append(
            WorkflowNode(
                id=trigger_id,
                type="trigger",
                label=trigger_label,
                configuration=trigger_configuration,
            )
        )

        previous_node_id = trigger_id

        # ---------------------------------------------------------
        # Conditions
        # ---------------------------------------------------------

        for index, condition in enumerate(state.conditions, start=1):
            condition_id = f"condition_{index}"

            nodes.append(
                WorkflowNode(
                    id=condition_id,
                    type="condition",
                    label=self._build_condition_label(condition),
                    configuration={
                        "field": condition.field,
                        "operator": condition.operator,
                        "value": condition.value,
                        "currency": condition.currency,
                    },
                )
            )

            edges.append(
                WorkflowEdge(
                    from_node=previous_node_id,
                    to_node=condition_id,
                )
            )

            previous_node_id = condition_id

        # ---------------------------------------------------------
        # Actions
        # ---------------------------------------------------------

        for index, action in enumerate(state.actions, start=1):
            action_id = f"action_{index}"

            nodes.append(
                WorkflowNode(
                    id=action_id,
                    type="action",
                    label=self._build_action_label(action),
                    configuration={
                        "type": action.type,
                        "provider": action.provider,
                        **action.configuration,
                    },
                )
            )

            edges.append(
                WorkflowEdge(
                    from_node=previous_node_id,
                    to_node=action_id,
                )
            )

            previous_node_id = action_id

        # ---------------------------------------------------------
        # End
        # ---------------------------------------------------------

        end_id = "end_1"

        nodes.append(
            WorkflowNode(
                id=end_id,
                type="end",
                label="End",
                configuration={},
            )
        )

        edges.append(
            WorkflowEdge(
                from_node=previous_node_id,
                to_node=end_id,
            )
        )

        # ---------------------------------------------------------
        # Metadata
        # ---------------------------------------------------------

        return GeneratedWorkflow(
            nodes=nodes,
            edges=edges,
            metadata=WorkflowMetadata(
                name=self._build_workflow_name(state),
                description=state.intent.goal,
            ),
        )

    # -------------------------------------------------------------
    # Label helpers
    # -------------------------------------------------------------

    def _build_trigger_label(self, state: WorkflowState) -> str:
        trigger = state.trigger

        if trigger.provider:
            return f"{trigger.provider} — {trigger.type or 'Trigger'}"

        return trigger.type or "Trigger"

    def _build_condition_label(self, condition) -> str:
        value = condition.value

        if condition.currency:
            value = f"{condition.currency} {value}"

        return (
            f"{condition.field} "
            f"{condition.operator} "
            f"{value}"
        )

    def _build_action_label(self, action) -> str:
        if action.provider:
            return f"{action.provider} — {action.type}"

        return action.type

    def _build_workflow_name(self, state: WorkflowState) -> str:
        if state.intent.goal:
            return state.intent.goal

        return "Generated Workflow"


# -----------------------------------------------------------------
# Convenience function for existing callers.
# -----------------------------------------------------------------

_workflow_service = WorkflowService()


def generate_workflow(state: WorkflowState) -> GeneratedWorkflow:
    """Generate a structured workflow from the canonical state."""
    return _workflow_service.generate(state)