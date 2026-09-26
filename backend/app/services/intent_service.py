"""Intent service — extracts and normalizes the user's automation goal."""

from __future__ import annotations

from app.schemas.workflow import Intent


class IntentService:
    """Service for working with the workflow intent."""

    def normalize(self, intent: Intent | None) -> Intent:
        """
        Normalize an extracted intent without inventing information.

        The service preserves the goal exactly when it is available and
        keeps missing information as None.
        """
        if intent is None:
            return Intent()

        goal = intent.goal.strip() if intent.goal else None

        return Intent(
            goal=goal,
            confidence=intent.confidence,
        )