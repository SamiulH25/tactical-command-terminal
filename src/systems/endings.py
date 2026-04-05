"""Ending calculator — determines the campaign outcome from the decision log.

The game supports multiple endings based on accumulated decisions
throughout the 25-floor campaign.  The ending is determined by:

1. **Overall moral alignment** — net reputation across all factions.
2. **Key decisions** — specific critical choices (spared enemies,
   rescued allies, betrayed factions).
3. **Faction reputation thresholds** — whether any faction is friendly
   or hostile enough to trigger special ending branches.

Lore-accurate endings:
- **Liberator**: Helped many, spared enemies, high reputation.
- **Conqueror**: Ruthless path, killed many, feared by all.
- **Exile**: Balanced path, no faction trusts you fully.
- **Redeemed**: Reconciled with FSA, proved your worth.
- **Betrayed**: Allies turned against you due to broken promises.
"""

from __future__ import annotations

from dataclasses import dataclass

from src.models.campaign import Campaign

# ---------------------------------------------------------------------------
# Ending definitions
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Ending:
    """A possible campaign ending.

    Invariants:
    - ``title`` is non-empty and uppercase-ready.
    - ``narrative_text`` is 1-3 sentences.
    """

    ending_id: str
    """Unique ending identifier."""

    title: str
    """Ending title for the victory screen, e.g. ``"LIBERATOR"``."""

    narrative_text: str
    """Closing narrative shown on the victory screen."""

    honour_colour: tuple[int, int, int] = (38, 217, 64)
    """Display colour for the ending title (green = good, red = bad)."""


# ---------------------------------------------------------------------------
# Ending registry
# ---------------------------------------------------------------------------

_ENDINGS: dict[str, Ending] = {
    "liberator": Ending(
        ending_id="liberator",
        title="LIBERATOR",
        narrative_text=(
            "The planet is free.  The Crimson Compact has surrendered, "
            "and the people you saved stand beside you as allies.  Command "
            "can't ignore you now — you've proven that dissent and "
            "competence are not mutually exclusive."
        ),
        honour_colour=(51, 204, 153),  # Cyan — friendly
    ),
    "conqueror": Ending(
        ending_id="conqueror",
        title="CONQUEROR",
        narrative_text=(
            "The planet is yours by force.  The Compact is shattered, the "
            "Rebels scattered.  Command is pleased with the result but wary "
            "of the methods.  You got what you wanted — but at what cost?"
        ),
        honour_colour=(230, 51, 51),  # Red — feared
    ),
    "exile": Ending(
        ending_id="exile",
        title="EXILE",
        narrative_text=(
            "The campaign is over, but no faction claims you as their own. "
            "Command reassigns you to the outer systems.  The Rebels "
            "remember your name but won't speak it.  You survive.  For now."
        ),
        honour_colour=(102, 102, 102),  # Grey — neutral
    ),
    "redeemed": Ending(
        ending_id="redeemed",
        title="REDEEMED",
        narrative_text=(
            "You proved your loyalty through action.  Command officially "
            "clears your record.  The dissident label is retired.  You are "
            "now a full Tactical Coordinator in the FSA fleet.  The irony "
            "is not lost on you."
        ),
        honour_colour=(51, 255, 87),  # Bright green — restored
    ),
    "betrayed": Ending(
        ending_id="betrayed",
        title="BETRAYED",
        narrative_text=(
            "The allies you failed to protect have turned against you. "
            "What was supposed to be a victory celebration becomes a "
            "tribunal.  Command watches silently as the people you "
            "abandoned deliver their verdict."
        ),
        honour_colour=(217, 140, 26),  # Amber — warning
    ),
}


# ---------------------------------------------------------------------------
# Calculator
# ---------------------------------------------------------------------------


class EndingCalculator:
    """Determines which ending the player receives.

    Usage::

        calc = EndingCalculator(campaign)
        ending = calc.calculate()
    """

    def __init__(self, campaign: Campaign) -> None:
        """Create an EndingCalculator.

        Args:
            campaign: The completed campaign state.
        """
        self.campaign = campaign

    def calculate(self) -> Ending:
        """Determine the ending based campaign state.

        Evaluation order (first match wins):
        1. **Betrayed**: Any rescued ally was later betrayed (decision log
           contains a ``"betray:"`` tag).
        2. **Redeemed**: FSA reputation >= 50 and campaign completed.
        3. **Liberator**: Rebel and CC reputations both >= 20.
        4. **Conqueror**: Both Rebel and CC reputations <= -40.
        5. **Exile**: Default — no other criteria met.

        Returns:
            The determined Ending.
        """
        # 1. Betrayed check
        for decision in self.campaign.decision_log:
            if decision.startswith("betray:"):
                return _ENDINGS["betrayed"]

        # 2. Redeemed check
        fsa_rep = self.campaign.reputation.get("fsa", 0)
        if fsa_rep >= 50:
            return _ENDINGS["redeemed"]

        # 3. Liberator check
        rebel_rep = self.campaign.reputation.get("rebel", 0)
        cc_rep = self.campaign.reputation.get("crimson_compact", 0)
        if rebel_rep >= 20 and cc_rep >= 20:
            return _ENDINGS["liberator"]

        # 4. Conqueror check
        if rebel_rep <= -40 and cc_rep <= -40:
            return _ENDINGS["conqueror"]

        # 5. Default: Exile
        return _ENDINGS["exile"]

    def get_all_possible_endings(self) -> list[Ending]:
        """Return all possible endings for reference.

        Returns:
            List of all Ending objects.
        """
        return list(_ENDINGS.values())
