"""Campaign state — tracks progress, decisions, and faction reputation.

The Campaign object persists across the entire playthrough.  It holds
the current floor, the decision log (array of choice IDs), reputation
scores per faction, and statistics for the operational report.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# Reputation thresholds for narrative branching.
_REP_HOSTILE = -30
_REP_NEUTRAL = -10
_REP_FRIENDLY = 10


@dataclass
class Campaign:
    """The persistent state of a playthrough.

    This object is serialised to JSON for save files and updated after
    every floor and encounter.

    Invariants:
    - ``current_floor`` is in ``[0, 25]`` (0 = not yet started).
    - ``reputation`` values are in ``[-100, 100]``.
    - ``decision_log`` contains only non-empty strings.
    """

    current_floor: int = 0
    """The floor the player is currently on (0 = not deployed)."""

    decision_log: list[str] = field(default_factory=list)
    """Ordered list of choice IDs made during the campaign."""

    reputation: dict[str, int] = field(
        default_factory=lambda: {
            "fsa": 0,
            "crimson_compact": 0,
            "rebel": 0,
        }
    )
    """Faction reputation scores.  Positive = friendly, negative = hostile."""

    # --- Operational report statistics ---
    enemies_defeated: int = 0
    cards_played: int = 0
    credits_earned: int = 0
    casualties: int = 0
    floors_cleared: int = 0
    current_credits: int = 150
    """Starting credits for the player (per lore: CR:0150)."""

    # --- Meta state ---
    unlocked_equipment: list[str] = field(default_factory=list)
    """Equipment IDs unlocked through salvage or events."""

    unlocked_mechs: list[str] = field(default_factory=list)
    """Mech frame IDs available for deployment (expands over time)."""

    allies_rescued: list[str] = field(default_factory=list)
    """Callsigns of allied NPCs that may appear as reinforcements."""

    # ------------------------------------------------------------------
    # Reputation helpers
    # ------------------------------------------------------------------

    def adjust_reputation(self, faction: str, delta: int) -> None:
        """Modify faction reputation by *delta*, clamped to [-100, 100].

        Args:
            faction: One of ``"fsa"``, ``"crimson_compact"``, ``"rebel"``.
            delta: Positive for friendlier, negative for more hostile.

        Raises:
            ValueError: If *faction* is not a known key.
        """
        if faction not in self.reputation:
            raise ValueError(f"Unknown faction '{faction}'. Known: {list(self.reputation.keys())}")
        self.reputation[faction] = max(-100, min(100, self.reputation[faction] + delta))

    def get_reputation_level(self, faction: str) -> str:
        """Return a qualitative level for the given faction.

        Returns:
            One of ``"hostile"``, ``"neutral"``, ``"friendly"``.
        """
        score = self.reputation.get(faction, 0)
        if score <= _REP_HOSTILE:
            return "hostile"
        if score >= _REP_FRIENDLY:
            return "friendly"
        return "neutral"

    # ------------------------------------------------------------------
    # Decision log helpers
    # ------------------------------------------------------------------

    def record_decision(self, choice_id: str) -> None:
        """Append a decision to the log.

        Args:
            choice_id: Unique identifier for the choice made.

        Raises:
            ValueError: If *choice_id* is empty.
        """
        if not choice_id:
            raise ValueError("choice_id must be non-empty")
        self.decision_log.append(choice_id)

    def has_decision(self, choice_id: str) -> bool:
        """Check whether a specific decision was made.

        Args:
            choice_id: The decision ID to look for.
        """
        return choice_id in self.decision_log

    def decisions_of_type(self, prefix: str) -> list[str]:
        """Return all decisions whose IDs start with *prefix*.

        Args:
            prefix: The prefix to match (e.g. ``"event:"``,
                ``"combat:"``).
        """
        return [d for d in self.decision_log if d.startswith(prefix)]

    # ------------------------------------------------------------------
    # Progression helpers
    # ------------------------------------------------------------------

    def advance_floor(self) -> int:
        """Move to the next floor.

        Returns:
            The new floor number.

        Raises:
            ValueError: If already at floor 25.
        """
        if self.current_floor >= 25:
            raise ValueError("Already at final floor (25)")
        self.current_floor += 1
        self.floors_cleared = self.current_floor - 1
        return self.current_floor

    @property
    def outpost_name(self) -> str:
        """Human-readable outpost name for the current floor."""
        # Import here to avoid circular dependency at module level.
        from src.models.encounter import outpost_name_for_floor

        if self.current_floor <= 0:
            return "Pre-Deployment"
        return outpost_name_for_floor(self.current_floor)

    def validate(self) -> None:
        """Raise ``ValueError`` if campaign state is inconsistent.

        Raises:
            ValueError: If ``current_floor`` is out of range or any
                reputation value is out of bounds.
        """
        if not (0 <= self.current_floor <= 25):
            raise ValueError(f"current_floor {self.current_floor} out of range [0, 25]")
        for faction_key, score in self.reputation.items():
            if not (-100 <= score <= 100):
                raise ValueError(f"reputation['{faction_key}'] = {score} out of range [-100, 100]")
        for decision in self.decision_log:
            if not decision:
                raise ValueError("decision_log contains an empty string")
