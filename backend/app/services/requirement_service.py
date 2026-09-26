from app.schemas.requirement import Requirement, RequirementStatus
from app.schemas.workflow import WorkflowState


class RequirementService:
    """
    Determines the complete set of information required to
    describe the workflow.

    This service operates only on the canonical WorkflowState.
    It does not inspect raw user messages.

    The service always returns the complete requirement model.

    Requirement status indicates whether each piece of information
    is currently:
        - satisfied
        - missing
        - ambiguous
        - conflicting

    Requirement dependencies describe the logical order in which
    information can be collected.
    """

    def evaluate(
        self,
        state: WorkflowState,
    ) -> list[Requirement]:
        """
        Evaluate the current workflow state and return the complete
        requirement model.
        """

        requirements: list[Requirement] = []

        requirements.extend(
            self._intent_requirements(state)
        )

        requirements.extend(
            self._trigger_requirements(state)
        )

        requirements.extend(
            self._condition_requirements(state)
        )

        requirements.extend(
            self._action_requirements(state)
        )

        requirements.extend(
            self._duplicate_handling_requirements(state)
        )

        return requirements

    # =============================================================
    # Intent
    # =============================================================

    def _intent_requirements(
        self,
        state: WorkflowState,
    ) -> list[Requirement]:
        """
        Determine whether the overall automation goal is known.
        """

        status = (
            RequirementStatus.SATISFIED
            if state.intent.goal
            else RequirementStatus.MISSING
        )

        return [
            Requirement(
                id="workflow.intent",
                description="Purpose of the automation",
                status=status,
                required=True,
                question=(
                    "What would you like this workflow "
                    "to automate?"
                ),
                priority=10,
            )
        ]

    # =============================================================
    # Trigger
    # =============================================================

    def _trigger_requirements(
        self,
        state: WorkflowState,
    ) -> list[Requirement]:
        """
        Determine the information required to start the workflow.

        Trigger type is mandatory.

        Trigger provider is required when the trigger depends
        on an external platform or service.

        For Gmail invoice workflows, the Gmail label/folder to
        monitor is also mandatory.
        """

        requirements: list[Requirement] = []

        # ---------------------------------------------------------
        # Trigger type
        # ---------------------------------------------------------

        trigger_status = (
            RequirementStatus.SATISFIED
            if state.trigger.type
            else RequirementStatus.MISSING
        )

        requirements.append(
            Requirement(
                id="trigger.type",
                description="Event that starts the workflow",
                status=trigger_status,
                required=True,
                question=(
                    "What event should trigger "
                    "this workflow?"
                ),
                priority=20,
            )
        )

        # ---------------------------------------------------------
        # Trigger provider
        # ---------------------------------------------------------

        if self._trigger_provider_required(state):

            provider_status = (
                RequirementStatus.SATISFIED
                if state.trigger.provider
                else RequirementStatus.MISSING
            )

            requirements.append(
                Requirement(
                    id="trigger.provider",
                    description=(
                        "Platform or service that provides "
                        "the trigger"
                    ),
                    status=provider_status,
                    required=True,
                    depends_on=["trigger.type"],
                    question=self._trigger_provider_question(
                        state
                    ),
                    priority=30,
                )
            )

        # ---------------------------------------------------------
        # Gmail monitor location
        # ---------------------------------------------------------

        if self._gmail_monitor_location_required(state):

            location = state.trigger.configuration.get(
                "location"
            )

            location_status = (
                RequirementStatus.SATISFIED
                if location
                else RequirementStatus.MISSING
            )

            requirements.append(
                Requirement(
                    id="trigger.location",
                    description=(
                        "Gmail label or folder to monitor "
                        "for incoming invoices"
                    ),
                    status=location_status,
                    required=True,
                    depends_on=["trigger.provider"],
                    question=(
                        "Which Gmail label or folder "
                        "should I monitor?"
                    ),
                    priority=35,
                )
            )

        return requirements

    # =============================================================
    # Conditions
    # =============================================================

    def _condition_requirements(
        self,
        state: WorkflowState,
    ) -> list[Requirement]:
        """
        Determine whether the workflow should use a condition.

        The condition decision is required only when the system
        does not yet know whether a condition should be used.

        The three possible states are:

            None
                The user has not decided yet.

            True
                The workflow uses a condition.

            False
                The workflow does not use a condition.

        If a concrete condition already exists, that itself proves
        that the condition decision has been made. In that case,
        the generic "condition" requirement is not returned.
        """

        requirements: list[Requirement] = []

        condition_enabled = state.condition_enabled

        if condition_enabled is None and state.conditions:
            condition_enabled = True

        if condition_enabled is None:

            requirements.append(
                Requirement(
                    id="condition",
                    description=(
                        "Whether the workflow should apply "
                        "a condition before running the action"
                    ),
                    status=RequirementStatus.MISSING,
                    required=True,
                    question=(
                        "Should there be a condition that "
                        "determines when the action runs?"
                    ),
                    priority=40,
                )
            )

            return requirements

        if condition_enabled is False:

            requirements.append(
                Requirement(
                    id="condition",
                    description=(
                        "Whether the workflow should apply "
                        "a condition before running the action"
                    ),
                    status=RequirementStatus.SATISFIED,
                    required=True,
                    question=(
                        "Should there be a condition that "
                        "determines when the action runs?"
                    ),
                    priority=40,
                )
            )

            return requirements

        if not state.conditions:

            requirements.append(
                Requirement(
                    id="condition.details",
                    description=(
                        "Details of the condition that "
                        "controls when the action runs"
                    ),
                    status=RequirementStatus.MISSING,
                    required=True,
                    depends_on=["condition"],
                    question=(
                        "What should the workflow check "
                        "before running the action?"
                    ),
                    priority=41,
                )
            )

            return requirements

        for index, condition in enumerate(
            state.conditions
        ):

            condition_id = f"condition.{index}"

            field_status = (
                RequirementStatus.SATISFIED
                if condition.field
                else RequirementStatus.MISSING
            )

            requirements.append(
                Requirement(
                    id=f"{condition_id}.field",
                    description="Field used by the condition",
                    status=field_status,
                    required=True,
                    question=(
                        "Which field should the condition "
                        "check?"
                    ),
                    priority=42 + (index * 3),
                )
            )

            operator_status = (
                RequirementStatus.SATISFIED
                if condition.operator
                else RequirementStatus.MISSING
            )

            requirements.append(
                Requirement(
                    id=f"{condition_id}.operator",
                    description="Condition comparison operator",
                    status=operator_status,
                    required=True,
                    depends_on=[
                        f"{condition_id}.field"
                    ],
                    question=(
                        "How should the condition compare "
                        "the value?"
                    ),
                    priority=43 + (index * 3),
                )
            )

            value_status = (
                RequirementStatus.SATISFIED
                if condition.value is not None
                else RequirementStatus.MISSING
            )

            requirements.append(
                Requirement(
                    id=f"{condition_id}.value",
                    description="Value used by the condition",
                    status=value_status,
                    required=True,
                    depends_on=[
                        f"{condition_id}.operator"
                    ],
                    question=(
                        "What value should the condition "
                        "use?"
                    ),
                    priority=44 + (index * 3),
                )
            )

        return requirements

    # =============================================================
    # Actions
    # =============================================================

    def _action_requirements(
        self,
        state: WorkflowState,
    ) -> list[Requirement]:
        """
        Determine whether an action exists and whether its
        required configuration is complete.
        """

        requirements: list[Requirement] = []

        action_status = (
            RequirementStatus.SATISFIED
            if state.actions
            else RequirementStatus.MISSING
        )

        requirements.append(
            Requirement(
                id="action",
                description="Action performed by the workflow",
                status=action_status,
                required=True,
                question=(
                    "What should the workflow do when "
                    "the trigger occurs?"
                ),
                priority=60,
            )
        )

        for index, action in enumerate(
            state.actions
        ):

            action_id = f"action.{index}"

            provider_status = (
                RequirementStatus.SATISFIED
                if action.provider
                else RequirementStatus.MISSING
            )

            requirements.append(
                Requirement(
                    id=f"{action_id}.provider",
                    description=(
                        f"Platform used for the "
                        f"'{action.type}' action"
                    ),
                    status=provider_status,
                    required=True,
                    depends_on=["action"],
                    question=self._action_provider_question(
                        action.type
                    ),
                    priority=70 + index,
                )
            )

            destination = action.configuration.get(
                "destination"
            )

            destination_required = (
                action.type == "notification"
                and action.provider in {
                    "slack",
                    "teams",
                    "email",
                }
            )

            if destination_required:

                destination_status = (
                    RequirementStatus.SATISFIED
                    if destination
                    else RequirementStatus.MISSING
                )

                requirements.append(
                    Requirement(
                        id=f"{action_id}.destination",
                        description=(
                            "Destination for the notification"
                        ),
                        status=destination_status,
                        required=True,
                        depends_on=[
                            f"{action_id}.provider"
                        ],
                        question=(
                            self._destination_question(
                                action.provider
                            )
                        ),
                        priority=80 + index,
                    )
                )

        return requirements

    # =============================================================
    # Duplicate handling
    # =============================================================

    def _duplicate_handling_requirements(
        self,
        state: WorkflowState,
    ) -> list[Requirement]:
        """
        Determine whether the duplicate-invoice handling
        preference has been explicitly provided.

        None means the user has not answered yet.

        True means duplicate invoices should be ignored.

        False means duplicate invoices should not be ignored.

        The requirement is intentionally mandatory because the
        workflow should not be generated until this preference
        has been explicitly collected.
        """

        status = (
            RequirementStatus.SATISFIED
            if state.duplicate_handling is not None
            else RequirementStatus.MISSING
        )

        return [
            Requirement(
                id="duplicate_handling",
                description=(
                    "How duplicate invoices should be handled"
                ),
                status=status,
                required=True,
                question=(
                    "Should duplicate invoices be ignored?"
                ),
                priority=90,
            )
        ]

    # =============================================================
    # Trigger helpers
    # =============================================================

    @staticmethod
    def _trigger_provider_required(
        state: WorkflowState,
    ) -> bool:
        """
        Determine whether the trigger requires a provider.

        Invoice-created workflows need to know where the
        invoice arrives.

        Email triggers also require an email platform.
        """

        return state.trigger.type in {
            "invoice.created",
            "email",
        }

    @staticmethod
    def _gmail_monitor_location_required(
        state: WorkflowState,
    ) -> bool:
        """
        Determine whether a Gmail monitor location is required.

        The assignment's invoice workflow explicitly asks for
        the Gmail label/folder after Gmail has been selected.

        This requirement is therefore limited to:
            trigger.type == invoice.created
            trigger.provider == gmail
        """

        return (
            state.trigger.type == "invoice.created"
            and state.trigger.provider == "gmail"
        )

    @staticmethod
    def _trigger_provider_question(
        state: WorkflowState,
    ) -> str:
        """
        Generate a natural question for the trigger provider.
        """

        if state.trigger.type == "invoice.created":
            return (
                "Where do the invoices arrive — "
                "Gmail, Outlook, or somewhere else?"
            )

        if state.trigger.type == "email":
            return (
                "Which email platform should receive "
                "the trigger — Gmail or Outlook?"
            )

        return (
            "Which platform or service should provide "
            "the trigger?"
        )

    # =============================================================
    # Action helpers
    # =============================================================

    @staticmethod
    def _action_provider_question(
        action_type: str,
    ) -> str:
        """
        Generate a natural clarification question for
        an action provider.
        """

        if action_type == "notification":
            return (
                "Which notification platform would you "
                "like to use — Slack, Microsoft Teams, "
                "or email?"
            )

        return (
            f"Which platform should be used for the "
            f"{action_type} action?"
        )

    @staticmethod
    def _destination_question(
        provider: str | None,
    ) -> str:
        """
        Generate a destination question based on the
        selected notification provider.
        """

        if provider == "slack":
            return (
                "Which Slack channel should receive "
                "the notification?"
            )

        if provider == "teams":
            return (
                "Which Microsoft Teams channel should "
                "receive the notification?"
            )

        if provider == "email":
            return (
                "Which email address should receive "
                "the notification?"
            )

        return (
            "Where should the notification be sent?"
        )