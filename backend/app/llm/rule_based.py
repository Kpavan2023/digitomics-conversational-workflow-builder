"""
Rule-based LLM provider.

This provider performs deterministic information extraction without
calling an external LLM API.

Its primary purpose is to provide a safe baseline implementation for
the conversation engine:

    user message
        ↓
    deterministic extraction
        ↓
    ExtractionResult
        ↓
    normalization
        ↓
    canonical WorkflowState

The provider must never invent missing workflow information.
"""

from __future__ import annotations

import re
from typing import Any

from app.llm.base import LLMProvider
from app.schemas.extraction import (
    ExtractedAction,
    ExtractedCondition,
    ExtractedIntent,
    ExtractedTrigger,
    ExtractionResult,
)
from app.schemas.workflow import WorkflowState


# ================================================================
# Number parsing
# ================================================================

_NUMBER_WORDS: dict[str, float] = {
    "zero": 0,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "thirteen": 13,
    "fourteen": 14,
    "fifteen": 15,
    "sixteen": 16,
    "seventeen": 17,
    "eighteen": 18,
    "nineteen": 19,
    "twenty": 20,
    "thirty": 30,
    "forty": 40,
    "fifty": 50,
    "sixty": 60,
    "seventy": 70,
    "eighty": 80,
    "ninety": 90,
    "hundred": 100,
    "thousand": 1000,
    "lakh": 100000,
    "million": 1000000,
}


# ================================================================
# Currency detection
# ================================================================

_CURRENCY_MAP: dict[str, str] = {
    "₹": "INR",
    "rs": "INR",
    "rupees": "INR",
    "inr": "INR",
    "$": "USD",
    "usd": "USD",
    "€": "EUR",
    "eur": "EUR",
    "£": "GBP",
    "gbp": "GBP",
}


# ================================================================
# Provider detection
# ================================================================

_PROVIDER_PATTERNS: list[tuple[str, str, str]] = [
    (
        "gmail",
        "Gmail",
        r"\bgmail\b",
    ),
    (
        "outlook",
        "Outlook",
        r"\b(outlook|microsoft\s+mail|ms\s+mail)\b",
    ),
]


# ================================================================
# Notification platform detection
# ================================================================

_PLATFORM_PATTERNS: list[tuple[str, str, str]] = [
    (
        "slack",
        "Slack",
        r"\bslack\b",
    ),
    (
        "teams",
        "Microsoft Teams",
        r"\b(teams|microsoft\s+teams|ms\s+teams)\b",
    ),
    (
        "email",
        "Email",
        r"\bemail\s+notification\b",
    ),
]


# ================================================================
# Utility functions
# ================================================================

def _escape_regex(value: str) -> str:
    return re.escape(value)


def _parse_amount(raw: str) -> float | None:
    """
    Parse a numeric or simple number-word amount.

    Examples:
        "10000"         -> 10000
        "10,000"        -> 10000
        "10k"           -> 10000
        "ten thousand"  -> 10000
        "100 thousand"  -> 100000
    """

    cleaned = (
        raw
        .replace(",", "")
        .strip()
        .lower()
    )

    if not cleaned:
        return None

    try:
        return float(cleaned)
    except ValueError:
        pass

    shorthand_match = re.fullmatch(
        r"(\d+(?:\.\d+)?)\s*(k|thousand|lakh|million)",
        cleaned,
    )

    if shorthand_match:
        number = float(shorthand_match.group(1))
        multiplier = shorthand_match.group(2)

        multipliers = {
            "k": 1000,
            "thousand": 1000,
            "lakh": 100000,
            "million": 1000000,
        }

        return number * multipliers[multiplier]

    words = cleaned.split()

    if not words:
        return None

    if not all(word in _NUMBER_WORDS for word in words):
        return None

    total = 0.0
    current = 0.0

    for word in words:
        value = _NUMBER_WORDS[word]

        if word == "hundred":
            if current == 0:
                current = 1

            current *= 100

        elif word in {
            "thousand",
            "lakh",
            "million",
        }:
            if current == 0:
                current = 1

            total += current * value
            current = 0

        else:
            current += value

    total += current

    return total


# ================================================================
# Condition decision extraction
# ================================================================

def _extract_condition_decision(
    text: str,
    current_state: WorkflowState,
) -> bool | None:

    normalized = text.strip().lower()

    negative_patterns = [
        r"\bno\s+condition\b",
        r"\bno\s+conditions?\b",
        r"\bwithout\s+(?:any\s+)?condition\b",
        r"\bno\s+need\s+for\s+(?:a\s+)?condition\b",
        r"\bdon['’]?t\s+need\s+(?:a\s+)?condition\b",
        r"\bdo\s+not\s+need\s+(?:a\s+)?condition\b",
        r"\bnotify\s+(?:me\s+)?for\s+every\s+invoice\b",
        r"\bnotify\s+(?:me\s+)?for\s+all\s+invoices\b",
        r"\bfor\s+every\s+invoice\b",
        r"\bfor\s+all\s+invoices\b",
        r"\bevery\s+invoice\b",
    ]

    if any(
        re.search(pattern, normalized)
        for pattern in negative_patterns
    ):
        return False

    positive_patterns = [
        r"\buse\s+(?:a\s+)?condition\b",
        r"\bwith\s+(?:a\s+)?condition\b",
        r"\bapply\s+(?:a\s+)?condition\b",
        r"\bcondition\s+should\s+be\b",
        r"\bonly\s+when\b",
        r"\bonly\s+if\b",
        r"\bwhen\s+the\s+amount\b",
        r"\bif\s+the\s+amount\b",
        r"\bprovided\s+that\b",
    ]

    if any(
        re.search(pattern, normalized)
        for pattern in positive_patterns
    ):
        return True

    if current_state.active_requirement_id == "condition":

        if re.fullmatch(
            r"(?:yes|yeah|yep|sure|correct|right|true)",
            normalized,
        ):
            return True

        if re.fullmatch(
            r"(?:no|nope|nah|false)",
            normalized,
        ):
            return False

    comparison_present = bool(
        re.search(
            r"(?:above|over|more\s+than|greater\s+than|"
            r"below|under|less\s+than|at\s+least|at\s+most|"
            r"equal\s+to|exactly|>=|<=|>|<|=)",
            normalized,
        )
    )

    if comparison_present:
        return True

    return None


# ================================================================
# Condition extraction
# ================================================================

def _extract_condition(text: str) -> dict[str, Any]:

    result: dict[str, Any] = {}

    for symbol, currency in _CURRENCY_MAP.items():
        if re.search(
            _escape_regex(symbol),
            text,
            re.IGNORECASE,
        ):
            result["currency"] = currency
            break

    patterns: list[tuple[str, str]] = [
        (
            ">=",
            r"(?:at least|greater than or equal to|no less than|minimum of|>=)\s+"
            r"([₹$€£]?\s*[\w,.]+(?:\s+(?:thousand|lakh|million))?)",
        ),
        (
            "<=",
            r"(?:at most|less than or equal to|no more than|maximum of|<=)\s+"
            r"([₹$€£]?\s*[\w,.]+(?:\s+(?:thousand|lakh|million))?)",
        ),
        (
            ">",
            r"(?:above|over|more than|greater than|exceeding|>)\s+"
            r"([₹$€£]?\s*[\w,.]+(?:\s+(?:thousand|lakh|million))?)",
        ),
        (
            "<",
            r"(?:below|under|less than|<)\s+"
            r"([₹$€£]?\s*[\w,.]+(?:\s+(?:thousand|lakh|million))?)",
        ),
        (
            "=",
            r"(?:exactly|equal to|=)\s+"
            r"([₹$€£]?\s*[\w,.]+(?:\s+(?:thousand|lakh|million))?)",
        ),
    ]

    for operator, pattern in patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE,
        )

        if not match:
            continue

        raw_value = match.group(1).strip()

        if "currency" not in result:
            for symbol, currency in _CURRENCY_MAP.items():
                if re.search(
                    _escape_regex(symbol),
                    raw_value,
                    re.IGNORECASE,
                ):
                    result["currency"] = currency
                    break

        cleaned_value = raw_value

        cleaned_value = re.sub(
            r"[₹$€£]",
            "",
            cleaned_value,
        )

        cleaned_value = re.sub(
            r"\b(?:rupees|inr|usd|dollars|eur|euros|gbp|pounds)\b",
            "",
            cleaned_value,
            flags=re.IGNORECASE,
        )

        cleaned_value = cleaned_value.strip()

        amount = _parse_amount(cleaned_value)

        if amount is not None:
            result["field"] = "invoice.amount"
            result["operator"] = operator
            result["value"] = amount

            return result

    ambiguous_match = re.search(
        r"\b(high[\s-]?value|important|large|big|significant|heavy)\b",
        text,
        re.IGNORECASE,
    )

    if ambiguous_match:
        result["ambiguous"] = ambiguous_match.group(1)

    return result


# ================================================================
# Destination extraction
# ================================================================

def _extract_destination(text: str) -> str | None:

    channel = re.search(
        r"#([a-z0-9][a-z0-9_-]*)",
        text,
        re.IGNORECASE,
    )

    if channel:
        return f"#{channel.group(1)}"

    email = re.search(
        r"\b[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}\b",
        text,
        re.IGNORECASE,
    )

    if email:
        return email.group(0)

    quoted = re.search(
        r'(?:channel|team)\s+(?:called\s+)?["\']([^"\']+)["\']',
        text,
        re.IGNORECASE,
    )

    if quoted:
        return quoted.group(1)

    return None


# ================================================================
# Provider extraction
# ================================================================

def _extract_provider(
    text: str,
) -> tuple[str | None, str | None]:

    for provider, label, pattern in _PROVIDER_PATTERNS:
        if re.search(
            pattern,
            text,
            re.IGNORECASE,
        ):
            return provider, label

    return None, None


# ================================================================
# Notification platform extraction
# ================================================================

def _extract_notification_platform(
    text: str,
) -> tuple[str | None, str | None]:

    for platform, label, pattern in _PLATFORM_PATTERNS:
        if re.search(
            pattern,
            text,
            re.IGNORECASE,
        ):
            return platform, label

    return None, None


# ================================================================
# Gmail monitor location
# ================================================================

def _extract_monitor_location(
    text: str,
    current_state: WorkflowState,
) -> str | None:
    """
    Extract the Gmail label/folder that should be monitored.

    The extractor is intentionally contextual.

    A short answer such as:

        Invoices

    is interpreted as a monitor location only when the active
    requirement is:

        trigger.location

    This prevents ordinary words from accidentally becoming a
    Gmail location elsewhere in the conversation.
    """

    normalized = text.strip()

    if not normalized:
        return None

    # ------------------------------------------------------------
    # This extractor is only active when the backend has explicitly
    # asked for the Gmail monitor location.
    # ------------------------------------------------------------

    if current_state.active_requirement_id != "trigger.location":
        return None

    # ------------------------------------------------------------
    # Do not interpret yes/no as a Gmail location.
    # ------------------------------------------------------------

    if re.fullmatch(
        r"(?:yes|yeah|yep|sure|no|nope|nah|true|false)",
        normalized,
        re.IGNORECASE,
    ):
        return None

    # ------------------------------------------------------------
    # Explicit label/folder phrasing.
    #
    # Examples:
    #   Gmail label Invoices
    #   label Invoices
    #   folder Invoices
    #   Gmail folder "Vendor Invoices"
    # ------------------------------------------------------------

    explicit_match = re.search(
        r"(?:gmail\s+)?(?:label|folder)"
        r"(?:\s+called|\s+named|\s+is|\s*[:\-])?"
        r"\s*[\"']?([^\"']+?)[\"']?\s*$",
        normalized,
        re.IGNORECASE,
    )

    if explicit_match:
        location = explicit_match.group(1).strip()

        if location:
            return location

    # ------------------------------------------------------------
    # Quoted answer.
    #
    # Example:
    #   "Invoices"
    # ------------------------------------------------------------

    quoted_match = re.fullmatch(
        r'["\']([^"\']+)["\']',
        normalized,
    )

    if quoted_match:
        location = quoted_match.group(1).strip()

        if location:
            return location

    # ------------------------------------------------------------
    # Contextual short answer.
    #
    # Since the active requirement explicitly asks for the Gmail
    # label/folder, the user's answer itself is the value.
    #
    # Examples:
    #   Invoices
    #   Vendor Invoices
    #   Receipts
    # ------------------------------------------------------------

    location = re.sub(
        r"^(?:the\s+)",
        "",
        normalized,
        flags=re.IGNORECASE,
    ).strip()

    if not location:
        return None

    # Avoid accepting obviously unrelated provider/platform answers.
    if re.fullmatch(
        r"(?:gmail|outlook|slack|teams|email)",
        location,
        re.IGNORECASE,
    ):
        return None

    return location


# ================================================================
# Duplicate handling
# ================================================================

def _extract_duplicate_handling(
    text: str,
    current_state: WorkflowState,
) -> bool | None:

    normalized = text.strip().lower()

    ignore_patterns = [
        r"\bignore\s+(?:the\s+)?duplicates?\b",
        r"\bskip\s+(?:the\s+)?duplicates?\b",
        r"\bignore\s+(?:any\s+)?duplicate\s+invoices?\b",
        r"\bskip\s+(?:any\s+)?duplicate\s+invoices?\b",
        r"\bdon['’]?t\s+notify\s+(?:me\s+)?(?:about\s+)?duplicates?\b",
        r"\bdo\s+not\s+notify\s+(?:me\s+)?(?:about\s+)?duplicates?\b",
        r"\bdo\s+not\s+process\s+(?:the\s+)?duplicates?\b",
        r"\bdon['’]?t\s+process\s+(?:the\s+)?duplicates?\b",
    ]

    if any(
        re.search(pattern, normalized)
        for pattern in ignore_patterns
    ):
        return True

    allow_patterns = [
        r"\ballow\s+(?:the\s+)?duplicates?\b",
        r"\bprocess\s+(?:the\s+)?duplicates?\b",
        r"\binclude\s+(?:the\s+)?duplicates?\b",
        r"\bnotify\s+(?:me\s+)?(?:about\s+)?duplicates?\b",
        r"\bdon['’]?t\s+ignore\s+(?:the\s+)?duplicates?\b",
        r"\bdo\s+not\s+ignore\s+(?:the\s+)?duplicates?\b",
        r"\bdo\s+not\s+skip\s+(?:the\s+)?duplicates?\b",
    ]

    if any(
        re.search(pattern, normalized)
        for pattern in allow_patterns
    ):
        return False

    if re.search(
        r"\b(?:every|all)\s+(?:new\s+)?invoices?\b",
        normalized,
    ):
        return False

    if current_state.active_requirement_id == "duplicate_handling":

        if re.fullmatch(
            r"(?:yes|yeah|yep|sure|correct|right|true)",
            normalized,
        ):
            return True

        if re.fullmatch(
            r"(?:no|nope|nah|false)",
            normalized,
        ):
            return False

    return None


# ================================================================
# Rule-based provider
# ================================================================

class RuleBasedProvider(LLMProvider):
    """
    Deterministic pattern-based extraction.

    No external API calls are made.
    """

    async def extract_information(
        self,
        user_message: str,
        current_state: WorkflowState,
    ) -> ExtractionResult:

        text = user_message

        result = ExtractionResult()

        # ========================================================
        # Intent
        # ========================================================

        intent_goal: str | None = None

        has_invoice_term = bool(
            re.search(
                r"\b(invoice|bill|receipt)\b",
                text,
                re.IGNORECASE,
            )
        )

        has_notification_term = bool(
            re.search(
                r"\b(notif(?:y|ication)?|alert|send|inform|message|tell)\b",
                text,
                re.IGNORECASE,
            )
        )

        has_workflow_term = bool(
            re.search(
                r"\b(workflow|automation|automate)\b",
                text,
                re.IGNORECASE,
            )
        )

        if has_invoice_term and has_notification_term:
            intent_goal = (
                "Send a notification when an invoice "
                "satisfies the specified conditions."
            )

        elif has_invoice_term:
            intent_goal = "Build an invoice-related workflow."

        elif has_workflow_term:
            intent_goal = "Build an automation workflow."

        if intent_goal:
            result.intent = ExtractedIntent(
                goal=intent_goal,
                confidence=1.0,
            )

        # ========================================================
        # Trigger
        # ========================================================

        trigger_type: str | None = None
        trigger_provider: str | None = None
        trigger_configuration: dict[str, Any] = {}

        # --------------------------------------------------------
        # Resolve answers to the currently active
        # trigger.provider requirement first.
        # --------------------------------------------------------

        if (
            current_state.active_requirement_id
            == "trigger.provider"
        ):
            provider, _ = _extract_provider(text)

            if provider:
                existing_trigger_type = (
                    current_state.trigger.type
                )

                if existing_trigger_type:
                    trigger_type = existing_trigger_type
                    trigger_provider = provider

                    trigger_configuration = dict(
                        current_state.trigger.configuration
                    )

                    if not trigger_configuration.get("event"):
                        if existing_trigger_type == "invoice.created":
                            trigger_configuration["event"] = (
                                "invoice.created"
                            )
                        elif existing_trigger_type == "email":
                            trigger_configuration["event"] = (
                                "email.received"
                            )

        # --------------------------------------------------------
        # Resolve answer to trigger.location.
        #
        # IMPORTANT:
        # Preserve the already-known trigger type/provider and
        # merge only the new location into configuration.
        # --------------------------------------------------------

        if (
            current_state.active_requirement_id
            == "trigger.location"
        ):
            location = _extract_monitor_location(
                text=text,
                current_state=current_state,
            )

            if location:
                trigger_type = current_state.trigger.type
                trigger_provider = current_state.trigger.provider

                trigger_configuration = dict(
                    current_state.trigger.configuration
                )

                trigger_configuration["location"] = location

        # --------------------------------------------------------
        # Invoice created / received
        # --------------------------------------------------------

        if trigger_type is None and re.search(
            r"\b("
            r"when\s+(?:a\s+|an\s+)?new\s+invoice\s+is\s+created|"
            r"when\s+(?:a\s+|an\s+)?invoice\s+is\s+created|"
            r"when\s+(?:a\s+|an\s+)?new\s+invoice\s+arrives?|"
            r"when\s+(?:a\s+|an\s+)?invoice\s+is\s+received"
            r")\b",
            text,
            re.IGNORECASE,
        ):
            trigger_type = "invoice.created"
            trigger_configuration["event"] = "invoice.created"

        # --------------------------------------------------------
        # Email received
        # --------------------------------------------------------

        elif trigger_type is None and re.search(
            r"\b(email|gmail|outlook|inbox|"
            r"receive|received|arrives?|incoming)\b",
            text,
            re.IGNORECASE,
        ):
            trigger_type = "email"

            provider, _ = _extract_provider(text)

            if provider:
                trigger_provider = provider

            trigger_configuration["event"] = "email.received"

        # --------------------------------------------------------
        # Build extracted trigger
        # --------------------------------------------------------

        if trigger_type:
            result.trigger = ExtractedTrigger(
                type=trigger_type,
                provider=trigger_provider,
                configuration=trigger_configuration,
            )

        # ========================================================
        # Condition decision
        # ========================================================

        condition_enabled = _extract_condition_decision(
            text=text,
            current_state=current_state,
        )

        if condition_enabled is not None:
            result.condition_enabled = condition_enabled

        # ========================================================
        # Condition details
        # ========================================================

        condition_data = _extract_condition(text)

        if condition_data.get("operator"):
            result.condition_enabled = True

            result.condition = ExtractedCondition(
                field=condition_data.get(
                    "field",
                    "invoice.amount",
                ),
                operator=condition_data["operator"],
                value=condition_data.get("value"),
                currency=condition_data.get("currency"),
            )

        # ========================================================
        # Action
        # ========================================================

        platform, platform_label = _extract_notification_platform(
            text
        )

        has_notification_action = bool(
            re.search(
                r"\b(notif(?:y|ication)?|alert|send|message|tell)\b",
                text,
                re.IGNORECASE,
            )
        )

        has_pending_notification_provider = any(
            action.type == "notification"
            and action.provider is None
            for action in current_state.actions
        )

        if has_pending_notification_provider and platform:
            has_notification_action = True

        destination = _extract_destination(text)

        if (
            current_state.active_requirement_id
            == "action.0.destination"
            and destination
        ):
            existing_notification_action = next(
                (
                    action
                    for action in current_state.actions
                    if action.type == "notification"
                ),
                None,
            )

            if existing_notification_action is not None:
                result.action = ExtractedAction(
                    type="notification",
                    provider=existing_notification_action.provider,
                    configuration={
                        "destination": destination,
                    },
                )

                has_notification_action = True

        if has_notification_action and result.action is None:
            configuration: dict[str, Any] = {}

            if destination:
                configuration["destination"] = destination

            if platform_label:
                configuration["provider_label"] = platform_label

            result.action = ExtractedAction(
                type="notification",
                provider=platform,
                configuration=configuration,
            )

        # ========================================================
        # Duplicate handling
        # ========================================================

        duplicate_handling = _extract_duplicate_handling(
            text=text,
            current_state=current_state,
        )

        if duplicate_handling is not None:
            result.duplicate_handling = duplicate_handling

        # ========================================================
        # Raw facts
        # ========================================================

        if destination:
            result.raw_facts["destination"] = destination

        if duplicate_handling is not None:
            result.raw_facts["duplicate_handling"] = (
                duplicate_handling
            )

        if condition_data.get("ambiguous"):
            result.raw_facts["ambiguous_condition"] = (
                condition_data["ambiguous"]
            )

        if platform_label:
            result.raw_facts["notification_platform_label"] = (
                platform_label
            )

        # --------------------------------------------------------
        # Monitor location raw fact
        # --------------------------------------------------------

        if result.trigger is not None:
            location = result.trigger.configuration.get(
                "location"
            )

            if location:
                result.raw_facts["trigger_location"] = location

        return result

    async def detect_ambiguity(
        self,
        user_message: str,
        current_state: WorkflowState,
    ) -> list[str]:

        found: list[str] = []

        text = user_message

        vague_condition = re.search(
            r"\b(important|high[\s-]?value|large|big|"
            r"significant|heavy)\b",
            text,
            re.IGNORECASE,
        )

        has_condition = bool(current_state.conditions)

        if vague_condition and not has_condition:
            found.append(
                "The condition is vague. "
                "Ask what threshold or rule should define it."
            )

        has_destination = any(
            action.configuration.get("destination")
            for action in current_state.actions
        )

        if re.search(
            r"\bfinance\s+team\b",
            text,
            re.IGNORECASE,
        ) and not has_destination:
            found.append(
                '"Finance team" is a group, not a specific destination. '
                "Ask which channel or address represents it."
            )

        if re.search(
            r"\bmy\s+team\b",
            text,
            re.IGNORECASE,
        ) and not has_destination:
            found.append(
                '"My team" is a group, not a specific destination. '
                "Ask which channel or address should receive the notification."
            )

        if re.search(
            r"\bnotify\s+me\b",
            text,
            re.IGNORECASE,
        ) and not has_destination:
            found.append(
                '"Notify me" does not specify a destination. '
                "Ask which channel or address should receive the notification."
            )

        return [
            ambiguity
            for ambiguity in found
            if ambiguity not in current_state.ambiguities
        ]

    async def generate_question(
        self,
        missing_field: str,
        context: WorkflowState,
    ) -> str:

        questions: dict[str, str] = {
            "workflow.intent": (
                "What would you like this workflow to automate?"
            ),
            "trigger.type": (
                "What event should trigger this workflow?"
            ),
            "trigger.provider": (
                "Where do the invoices arrive — Gmail, Outlook, "
                "or somewhere else?"
            ),
            "trigger.location": (
                "Which Gmail label or folder should I monitor?"
            ),
            "condition": (
                "Should the workflow run for every invoice, "
                "or only when a condition is met?"
            ),
            "condition.details": (
                "What should the workflow check "
                "before running the action?"
            ),
            "condition.0.field": (
                "Which field should the condition check?"
            ),
            "condition.0.operator": (
                "How should the condition compare the value?"
            ),
            "condition.0.value": (
                "What value should the condition use?"
            ),
            "action": (
                "What should the workflow do when the trigger occurs?"
            ),
            "action.0.provider": (
                "Which notification platform would you like to use "
                "— Slack, Microsoft Teams, or email?"
            ),
            "action.0.destination": (
                "Which channel or address should receive the notification?"
            ),
            "duplicate_handling": (
                "Should duplicate invoices be ignored?"
            ),
        }

        return questions.get(
            missing_field,
            f"Please provide: {missing_field}",
        )