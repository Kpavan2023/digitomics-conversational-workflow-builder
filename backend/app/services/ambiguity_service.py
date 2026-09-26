from app.schemas.workflow import WorkflowState


class AmbiguityService:
    """
    Detects ambiguity and conflicts in the canonical workflow state.

    This service does not decide what the user meant.
    It only identifies situations that require clarification.
    """

    def evaluate(self, state: WorkflowState) -> tuple[list[str], list[str]]:
        """
        Return:

        ambiguities:
            Information that is unclear or insufficiently specific.

        conflicts:
            Information that contains incompatible conditions.
        """

        ambiguities: list[str] = []
        conflicts: list[str] = []

        ambiguities.extend(
            self._find_trigger_ambiguities(state)
        )

        ambiguities.extend(
            self._find_condition_ambiguities(state)
        )

        ambiguities.extend(
            self._find_action_ambiguities(state)
        )

        conflicts.extend(
            self._find_condition_conflicts(state)
        )

        return ambiguities, conflicts

    # =============================================================
    # Trigger ambiguity
    # =============================================================

    def _find_trigger_ambiguities(
        self,
        state: WorkflowState,
    ) -> list[str]:

        ambiguities: list[str] = []

        if state.trigger.type == "schedule":
            configuration = state.trigger.configuration

            if not configuration:
                ambiguities.append(
                    "The schedule trigger does not contain scheduling details."
                )

        return ambiguities

    # =============================================================
    # Condition ambiguity
    # =============================================================

    def _find_condition_ambiguities(
        self,
        state: WorkflowState,
    ) -> list[str]:

        ambiguities: list[str] = []

        for index, condition in enumerate(state.conditions):

            if not condition.field:
                ambiguities.append(
                    f"Condition {index + 1} does not specify a field."
                )

            if not condition.operator:
                ambiguities.append(
                    f"Condition {index + 1} does not specify an operator."
                )

            if condition.value is None:
                ambiguities.append(
                    f"Condition {index + 1} does not specify a value."
                )

        return ambiguities

    # =============================================================
    # Action ambiguity
    # =============================================================

    def _find_action_ambiguities(
        self,
        state: WorkflowState,
    ) -> list[str]:

        ambiguities: list[str] = []

        for index, action in enumerate(state.actions):

            if not action.type:
                ambiguities.append(
                    f"Action {index + 1} does not specify an action type."
                )

            if action.type == "notification" and not action.provider:
                ambiguities.append(
                    f"Notification action {index + 1} does not specify a provider."
                )

        return ambiguities

    # =============================================================
    # Condition conflicts
    # =============================================================

    def _find_condition_conflicts(
        self,
        state: WorkflowState,
    ) -> list[str]:

        conflicts: list[str] = []

        for index, first in enumerate(state.conditions):

            for second in state.conditions[index + 1:]:

                if first.field != second.field:
                    continue

                if self._conditions_are_contradictory(
                    first.operator,
                    first.value,
                    second.operator,
                    second.value,
                ):
                    conflicts.append(
                        (
                            f"Conflicting conditions for "
                            f"'{first.field}': "
                            f"{first.operator} {first.value} "
                            f"and "
                            f"{second.operator} {second.value}."
                        )
                    )

        return conflicts

    def _conditions_are_contradictory(
        self,
        first_operator: str,
        first_value,
        second_operator: str,
        second_value,
    ) -> bool:

        if not self._values_are_comparable(
            first_value,
            second_value,
        ):
            return False

        if first_operator == ">" and second_operator == "<":
            return True

        if first_operator == "<" and second_operator == ">":
            return True

        if first_operator == ">=" and second_operator == "<":
            return True

        if first_operator == "<" and second_operator == ">=":
            return True

        return False

    @staticmethod
    def _values_are_comparable(
        first_value,
        second_value,
    ) -> bool:

        return (
            isinstance(first_value, (int, float))
            and isinstance(second_value, (int, float))
        )