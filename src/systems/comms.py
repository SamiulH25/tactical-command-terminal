"""Intercepted comms — faction-specific transmission text.

The Coordinator's terminal periodically picks up enemy or ally
communications.  The content of these transmissions changes based on
the player's reputation with each faction and the current floor range.

Lore framing:  Radio comms are subject to interference.  CC forces
sound desperate if losing, defiant if holding.  Rebels are cynical and
pragmatic.  FSA command is professional but may reference the
Coordinator's dissident status.
"""

from __future__ import annotations

from src.models.campaign import Campaign

# ---------------------------------------------------------------------------
# Comm text pools — keyed by (faction, reputation_level, floor_range).
# ---------------------------------------------------------------------------

_CC_COMMS: dict[str, list[str]] = {
    "hostile": [
        "CC Command: All units, fall back to Fortress.  They're too strong.",
        "CC Patrol: We can't hold them.  Request reinforcements at Grid 14.",
        "CC Officer: The dissident coordinator is pushing through our lines.",
    ],
    "neutral": [
        "CC Command: Maintain perimeter defences.  Do not engage recklessly.",
        "CC Patrol: Unknown contacts at Outpost perimeter.  Stay alert.",
        "CC Officer: Reinforce the relay station.  Intel suggests movement.",
    ],
    "friendly": [
        "CC Soldier: Maybe we can negotiate.  They're not mindless killers.",
        "CC Officer: If we stand down, will they let us keep our homes?",
        "CC Command: Cease fire on the dissident's forces.  Evaluate options.",
    ],
}

_REBEL_COMMS: dict[str, list[str]] = {
    "hostile": [
        "Rebel: That coordinator screwed us.  Hit them where it hurts.",
        "Rebel Scout: They took our supplies.  Next time we take heads.",
    ],
    "neutral": [
        "Rebel: Everyone's just trying to survive.  Keep your head down.",
        "Rebel Trader: Got salvage if you got credits.  Fair trade only.",
    ],
    "friendly": [
        "Rebel: The dissident came through for us.  We owe them one.",
        "Rebel Leader: Send word — help the coordinator if they ask.",
    ],
}

_FSA_COMMS: dict[str, list[str]] = {
    "hostile": [
        "FSA Command: Keep the dissident on a short leash.  Monitor closely.",
        "FSA Officer: That coordinator is a liability.  Report all movements.",
    ],
    "neutral": [
        "FSA Command: Outpost status report requested.  Transmit on schedule.",
        "FSA Officer: Maintain radio discipline.  Command is watching.",
    ],
    "friendly": [
        "FSA Command: The dissident is proving their worth.  Recognise their efforts.",
        "FSA Officer: Word from high command — the coordinator may be rehabilitated.",
    ],
}


def get_intercepted_comm(
    campaign: Campaign,
    faction: str = "auto",
) -> str:
    """Return a random intercepted comm appropriate for the campaign state.

    Args:
        campaign: Current campaign state (for reputation and floor).
        faction: ``"cc"``, ``"rebel"``, ``"fsa"``, or ``"auto"`` to pick
            based on floor range.

    Returns:
        A comm text string.
    """
    if faction == "auto":
        floor = campaign.current_floor
        if floor <= 10:
            faction = "fsa"
        elif floor <= 18:
            faction = "rebel"
        else:
            faction = "cc"

    comm_pools: dict[str, dict[str, list[str]]] = {
        "cc": _CC_COMMS,
        "rebel": _REBEL_COMMS,
        "fsa": _FSA_COMMS,
    }
    pool = comm_pools.get(faction)
    if pool is None:
        return "> NO SIGNAL // TELEMETRY INTERFERENCE DETECTED"

    rep_level = campaign.get_reputation_level(faction)
    texts = pool.get(rep_level, pool["neutral"])

    import random

    return random.choice(texts)
