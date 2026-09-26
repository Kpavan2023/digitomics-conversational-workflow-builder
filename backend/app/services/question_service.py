from app.schemas.requirement import Requirement, RequirementStatus
from app.schemas.workflow import WorkflowState


class QuestionService:
    """
    Selects the next clarification requirement based on the
    current workflow state and its unresolved requirements.

    This service does not modify the workflow state.
    """

    def get_next_requirement(
        self,
        state: WorkflowState,
        requirements: list[Requirement],
    ) -> Requirement | None:
        """
        Return the highest-priority unresolved requirement whose
        dependencies have already been satisfied.

        Returns None when there is no unresolved required
        information that needs clarification.
        """

        unresolved = [
            requirement
            for requirement in requirements
            if requirement.required
            and requirement.status
            in {
                RequirementStatus.MISSING,
                RequirementStatus.AMBIGUOUS,
                RequirementStatus.CONFLICTING,
            }
        ]

        if not unresolved:
            return None

        # ---------------------------------------------------------
        # Only consider requirements whose dependencies are ready.
        # ---------------------------------------------------------

        eligible: list[Requirement] = []

        for requirement in unresolved:
            dependencies_satisfied = all(
                self._is_requirement_satisfied(
                    dependency_id=dependency_id,
                    requirements=requirements,
                )
                for dependency_id in requirement.depends_on
            )

            if dependencies_satisfied:
                eligible.append(requirement)

        if not eligible:
            return None

        # ---------------------------------------------------------
        # Select the highest-priority eligible requirement.
        # ---------------------------------------------------------

        eligible.sort(
            key=lambda requirement: requirement.priority
        )

        return eligible[0]

    def get_next_question(
        self,
        state: WorkflowState,
        requirements: list[Requirement],
    ) -> str | None:
        """
        Return the question belonging to the next eligible
        requirement.

        This method is retained as a compatibility wrapper for
        existing callers and tests.
        """

        requirement = self.get_next_requirement(
            state=state,
            requirements=requirements,
        )

        if requirement is None:
            return None

        return (
            requirement.question
            or requirement.description
        )

    @staticmethod
    def _is_requirement_satisfied(
        dependency_id: str,
        requirements: list[Requirement],
    ) -> bool:
        """
        Return True when the specified dependency exists and
        has been satisfied.
        """

        dependency = next(
            (
                requirement
                for requirement in requirements
                if requirement.id == dependency_id
            ),
            None,
        )

        if dependency is None:
            return False

        return dependency.status == RequirementStatus.SATISFIED