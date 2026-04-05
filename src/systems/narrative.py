"""Narrative engine — processes decisions and applies consequences.

The NarrativeEngine connects the player's choices to the game world:
- Records decisions in the campaign decision log.
- Adjusts faction reputation based on choice outcomes.
- Modifies future encounters based on accumulated reputation.
- Tracks rescued allies who may appear as reinforcements.

Lore framing:  The Coordinator's dissident status and accumulated
reputation precede them.  CC forces may surrender if treated mercifully,
Rebels may provide intel if helped, and FSA command may interfere if
the Coordinator appears too competent.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from src.models.campaign import Campaign

# ---------------------------------------------------------------------------
# Outcome definitions — each possible choice result maps to consequences.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Outcome:
    """The consequence of a narrative choice.

    Invariants:
    - At least one of the fields should be non-default.
    - ``credits_delta`` may be negative (paying a bribe).
    """

    outcome_id: str
    """Unique identifier for this outcome."""

    narrative_text: str = ""
    """Terminal text shown after the choice is made."""

    reputation_changes: dict[str, int] = field(default_factory=dict)
    """Faction reputation deltas, e.g. ``{"rebel": 15}``."""

    credits_delta: int = 0
    """Credits gained or lost."""

    ally_rescued: str | None = None
    """Callsign of an ally rescued by this choice, if any."""

    decision_tag: str = ""
    """Tag appended to the decision log, e.g. ``"event:help_rebel"``."""

    def validate(self) -> None:
        """Raise ``ValueError`` if the outcome is malformed.

        Raises:
            ValueError: If ``outcome_id`` is empty.
        """
        if not self.outcome_id:
            raise ValueError("Outcome outcome_id must be non-empty")


@dataclass(frozen=True)
class EventChoice:
    """A single player choice within a narrative event.

    Each choice has display text and an associated outcome ID that
    determines the consequences.
    """

    text: str
    """The button label shown to the player."""

    outcome_id: str
    """References an Outcome in the event's outcome map."""

    requires_decision: str | None = None
    """If set, this choice only appears if the player has made this decision."""

    forbidden_decision: str | None = None
    """If set, this choice is hidden if the player has made this decision."""

    def validate(self) -> None:
        """Raise ``ValueError`` if the choice is malformed.

        Raises:
            ValueError: If ``text`` or ``outcome_id`` is empty.
        """
        if not self.text:
            raise ValueError("EventChoice text must be non-empty")
        if not self.outcome_id:
            raise ValueError("EventChoice outcome_id must be non-empty")


@dataclass(frozen=True)
class NarrativeEvent:
    """A branching narrative encounter.

    The event presents 2-3 choices to the player.  Each choice leads
    to a different outcome that affects reputation, credits, and
    potentially unlocks allies.

    Invariants:
    - At least 2 choices.
    - All ``outcome_id`` references in choices must exist in outcomes.
    """

    id: str
    """Unique event identifier."""

    title: str
    """Event title shown in the header, e.g. ``"INTERCEPTED SIGNAL"``."""

    narrative_text: str
    """The situation description shown before choices."""

    choices: list[EventChoice]
    """Available player choices."""

    outcomes: dict[str, Outcome]
    """Maps outcome_id → Outcome for all possible results."""

    min_floor: int = 1
    """Minimum floor this event can appear on."""

    max_floor: int = 25
    """Maximum floor this event can appear on."""

    def validate(self) -> None:
        """Raise ``ValueError`` if the event is malformed.

        Raises:
            ValueError: If ``id`` is empty, fewer than 2 choices, or any
                choice references a missing outcome.
        """
        if not self.id:
            raise ValueError("NarrativeEvent id must be non-empty")
        if not self.title:
            raise ValueError("NarrativeEvent title must be non-empty")
        if not self.narrative_text:
            raise ValueError("NarrativeEvent narrative_text must be non-empty")
        if len(self.choices) < 2:
            raise ValueError(
                f"NarrativeEvent '{self.id}' must have at least 2 choices, got {len(self.choices)}"
            )
        for choice in self.choices:
            choice.validate()
            if choice.outcome_id not in self.outcomes:
                raise ValueError(
                    f"Choice outcome '{choice.outcome_id}' not found in "
                    f"outcomes for event '{self.id}'"
                )
        for outcome in self.outcomes.values():
            outcome.validate()

    def get_available_choices(self, campaign: Campaign) -> list[EventChoice]:
        """Return choices that are currently available based on decisions.

        Filters out choices that require or forbid decisions the player
        has (not) made.

        Args:
            campaign: The current campaign state.

        Returns:
            List of choices available to the player.
        """
        available: list[EventChoice] = []
        for choice in self.choices:
            if choice.requires_decision and not campaign.has_decision(choice.requires_decision):
                continue
            if choice.forbidden_decision and campaign.has_decision(choice.forbidden_decision):
                continue
            available.append(choice)
        # Ensure at least one choice is always available
        if not available:
            return [self.choices[0]]
        return available


# ---------------------------------------------------------------------------
# Narrative Engine
# ---------------------------------------------------------------------------


class NarrativeEngine:
    """Processes narrative choices and applies their consequences.

    Usage::

        engine = NarrativeEngine(campaign)
        outcome = engine.resolve_choice(event, chosen_choice)
    """

    def __init__(self, campaign: Campaign) -> None:
        """Create a NarrativeEngine.

        Args:
            campaign: The campaign to modify based on choices.
        """
        self.campaign = campaign

    def resolve_choice(self, event: NarrativeEvent, choice: EventChoice) -> Outcome:
        """Apply the consequences of a chosen outcome.

        This method:
        1. Looks up the outcome by ID.
        2. Adjusts faction reputation.
        3. Updates credits.
        4. Records rescued allies.
        5. Appends the decision to the campaign log.

        Args:
            event: The narrative event containing the choice.
            choice: The player's chosen option.

        Returns:
            The resolved Outcome.

        Raises:
            ValueError: If the outcome ID is not found.
        """
        outcome = event.outcomes.get(choice.outcome_id)
        if outcome is None:
            raise ValueError(f"Outcome '{choice.outcome_id}' not found in event '{event.id}'")

        # Apply reputation changes
        for faction, delta in outcome.reputation_changes.items():
            self.campaign.adjust_reputation(faction, delta)

        # Apply credits
        self.campaign.current_credits += outcome.credits_delta
        self.campaign.current_credits = max(0, self.campaign.current_credits)

        # Record rescued ally
        if outcome.ally_rescued and outcome.ally_rescued not in self.campaign.allies_rescued:
            self.campaign.allies_rescued.append(outcome.ally_rescued)

        # Record decision
        decision_tag = outcome.decision_tag or f"{event.id}:{choice.outcome_id}"
        self.campaign.record_decision(decision_tag)

        return outcome
