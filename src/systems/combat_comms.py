"""Combat comms — flavour text transmitted to the Coordinator during combat.

Messages appear as intercepted transmissions or tactical readouts on the
terminal.  They are purely cosmetic — no gameplay effect — but reinforce
the narrative of a Coordinator sitting at a command terminal during an
active engagement.

Messages are selected based on:
- Current combat situation (player HP, enemy HP, turn phase)
- Campaign floor number
- Faction reputation levels
- Random variation to avoid repetition
"""

from __future__ import annotations

import random

from src.models.campaign import Campaign
from src.systems.combat import CombatState
from src.ui.text import pad

# ---------------------------------------------------------------------------
# Message pools — each dict maps a situation key to a list of messages.
# ---------------------------------------------------------------------------

# Generic combat observations — shown at the start of any engagement
ENGAGEMENT_START: list[str] = [
    "> TACTICAL FEED ACTIVE.  Enemy contacts detected on grid.",
    "> ENGAGEMENT PROTOCOL INITIATED.  Good hunting, Coordinator.",
    "> COMBAT FEED ESTABLISHED.  Sensors show hostiles in sector.",
    "> LINK CONFIRMED.  Enemy transponders active on grid.",
    "> TACTICAL DISPLAY ONLINE.  Hostile units identified.",
    "> ENGAGEMENT START.  All units report status green.",
    "> FEED ACQUIRED.  Enemy positions mapped to grid.",
    "> COMBAT PROTOCOL ACTIVE.  Direct your pilots, Coordinator.",
]

# Player mech takes damage
DAMAGE_TAKEN_LOW: list[str] = [
    "> Minor hull impact reported.  Within acceptable parameters.",
    "> Armor plating held.  Minimal structural damage.",
    "> Glancing blow detected.  Systems nominal.",
    "> Shallow impact on forward armor.  No critical systems affected.",
]

DAMAGE_TAKEN_MED: list[str] = [
    "> Significant impact detected.  Recommend repositioning.",
    "> Hull integrity compromised in sector 4.  Patching available.",
    "> Heavy hit absorbed.  Recommend field repairs.",
    "> Structural stress increasing.  Armor integrity at {hp}%.",
]

DAMAGE_TAKEN_HIGH: list[str] = [
    "> CRITICAL DAMAGE.  Hull breach imminent.",
    "> CRITICAL: Multiple systems offline.  Hull integrity failing.",
    "> SEVERE structural damage.  Recommend immediate withdrawal.",
    "> ALARM: Armor integrity below 25%.  Survival unlikely.",
]

# Enemy damaged or destroyed
ENEMY_HIT: list[str] = [
    "> Direct impact confirmed.  Enemy transponder flickering.",
    "> Hostile unit taking damage.  Recommend follow-up fire.",
    "> Hit confirmed.  Enemy mobility impaired.",
    "> Good effect on target.  Enemy unit damaged.",
]

ENEMY_DESTROYED: list[str] = [
    "> HOSTILE UNIT OFFLINE.  Transponder signal lost.",
    "> Enemy mech destroyed.  Signal eliminated from grid.",
    "> Target neutralized.  Debris field confirmed.",
    "> Hostile eliminated.  Grid position cleared.",
]

ENEMY_LOW_HP: list[str] = [
    "> Enemy transponder weakening.  Recommend finishing fire.",
    "> Hostile unit critically damaged.  One more hit should eliminate.",
    "> Enemy IFF signal degrading.  Unit near destruction.",
]

# Player mech low HP
PLAYER_LOW_HP: list[str] = [
    "> ALERT: Hull integrity critical.  Recommend immediate repair.",
    "> WARNING: Structural failure imminent.  Repair recommended.",
    "> CRITICAL: Armor integrity below 25%.  Field repairs advised.",
    "> ALERT: Multiple system failures detected.  Retreat advised.",
]

# Overload warning
OL_WARNING: list[str] = [
    "> Overload capacity reaching threshold.  Conserve directives.",
    "> Power systems strained.  Recommend lower-cost directives.",
    "> OL budget depleting.  Manage remaining capacity carefully.",
]

# Enemy turn
ENEMY_TURN: list[str] = [
    "> Enemy units active.  Brace for incoming fire.",
    "> Hostile transponders moving.  Enemy phase initiated.",
    "> Enemy turn — brace positions and monitor grid.",
]

# Floor-specific messages (narrative context during combat)
FLOOR_COMMS: dict[tuple[int, int], list[str]] = {
    (1, 5): [
        "> FSA Command: First contact with CC forces.  Maintain discipline.",
        "> Intercepted: 'They're hitting us hard.  Fall back to perimeter.'",
        "> CC Command: 'Intruders at Outpost Alpha.  Engage and destroy.'",
    ],
    (6, 10): [
        "> FSA Command: Bravo sector intensifying.  CC reinforcing positions.",
        "> Intercepted: 'Hold the line.  They won't break through.'",
        "> CC Command: 'Double the perimeter guard.  They're pushing deep.'",
    ],
    (11, 15): [
        "> FSA Command: Deep in enemy territory.  No backup available.",
        "> Intercepted: 'They're inside the perimeter.  All units converge.'",
        "> CC Command: 'Command Fortress is the last line.  Do not yield.'",
    ],
    (16, 20): [
        "> FSA Command: Final approach.  Everything the CC has is here.",
        "> Intercepted: 'They're at the Fortress gates.  Last stand orders.'",
        "> CC Command: 'This is it.  No retreat.  No surrender.'",
    ],
    (21, 25): [
        "> FSA Command: Final assault.  The enemy commander awaits.",
        "> Intercepted: 'They've reached the Fortress core.  ALL UNITS.'",
        "> CC Command: 'Protect the Commander at all costs.  This ends now.'",
    ],
}

# Random ambient comms — shown periodically during combat
AMBIENT_COMMS: list[str] = [
    "> FSA Command: All coordinators report status on primary channel.",
    "> Intercepted: '...static... reinforcement request... static...'",
    "> FSA Logistics: Supply drop delayed.  Ration remaining munitions.",
    "> Intercepted: 'Hold position.  Artillery support incoming.'",
    "> FSA Command: Enemy jamming detected.  Switching to backup feed.",
    "> Intercepted: '...they've breached the eastern wall...'",
    "> FSA Medical: Casualty reports incoming.  Prepare triage.",
    "> Intercepted: 'Request immediate evac.  Repeat, immediate—'",
    "> FSA Command: Satellite feed shows enemy reinforcements inbound.",
    "> Intercepted: '...fall back to secondary position... now!'",
    "> FSA Logistics: Ammo reserves at 60%.  Conserve heavy ordnance.",
    "> Intercepted: '...I can see their IFF tags.  There's dozens of—'",
    "> FSA Command: All units, maintain radio discipline.",
    "> Intercepted: '...commander's down.  Who's in charge here?!'",
    "> FSA Medical: Medical supplies en route to your sector.",
    "> Intercepted: '...the grid is full of them.  We need—'",
    "> FSA Command: Weather systems deteriorating.  Expect signal loss.",
    "> Intercepted: '...hold the ridge.  Don't let them flank—'",
    "> FSA Logistics: New munitions batch received.  Quality uncertain.",
    "> Intercepted: '...they're using our own IFF codes.  How are—'",
]

# Faction-specific comms based on reputation
REBEL_FRIENDLY: list[str] = [
    "> Rebel channel open: 'We owe you one, Coordinator.  Watch your six.'",
    "> Intercepted (Rebel): 'The Coordinator's our friend.  Don't engage.'",
    "> Rebel transmission: 'Got your back.  Watch the flanks.'",
]

CC_HOSTILE: list[str] = [
    "> Intercepted (CC): 'The dissident coordinator is our priority target.'",
    "> CC Command: 'Focus fire on the coordinator's mech.  Eliminate command.'",
    "> Intercepted (CC): 'They're led by a political dissident.  They'll break.'",
]

CC_FRIENDLY: list[str] = [
    "> Intercepted (CC): 'Maybe we can negotiate.  Hold fire until ordered.'",
    "> CC Command: 'Unusual orders from high command.  Stand down partially.'",
]

FSA_HOSTILE: list[str] = [
    "> FSA Command: Coordinator, you're being monitored.  Perform adequately.",
    "> Intercepted (FSA Internal): 'That dissident better not fail again.'",
]


# ---------------------------------------------------------------------------
# Timestamp formatting
# ---------------------------------------------------------------------------


def _format_timestamp(hours: int, minutes: int, seconds: int) -> str:
    """Generate a realistic tactical timestamp prefix.

    Format: ``HH:MM:SS // `` with zero-padded values.

    Args:
        hours: Hour (00-23).
        minutes: Minute (00-59).
        seconds: Second (00-59).

    Returns:
        Formatted timestamp string like ``04:12:33 // ``.
    """
    return f"{pad(hours, 2)}:{pad(minutes, 2)}:{pad(seconds, 2)} // "


class CombatComms:
    """Generates flavour text messages during combat.

    Usage::

        comms = CombatComms(campaign)
        # At start of combat:
        comms.start_combat(combat_state, floor_number)
        # Each turn or event:
        msg = comms.get_message("damage_taken", hp_ratio=0.3)
    """

    def __init__(self, campaign: Campaign) -> None:
        self._campaign = campaign
        self._floor: int = 0
        self._seen_messages: set[str] = set()
        self._ambient_counter: int = 0
        self._mission_clock_seconds: int = 0

    def start_combat(self, combat_state: CombatState, floor: int) -> None:
        """Initialize comms for a new combat encounter.

        Args:
            combat_state: The current combat state.
            floor: The current campaign floor number.
        """
        self._floor = floor
        self._seen_messages.clear()
        self._mission_clock_seconds = 0

    def _tick_clock(self) -> tuple[int, int, int]:
        """Advance the simulated mission clock and return (h, m, s)."""
        self._mission_clock_seconds += 3
        h = (self._mission_clock_seconds // 3600) % 24
        m = (self._mission_clock_seconds % 3600) // 60
        s = self._mission_clock_seconds % 60
        return h, m, s

    def get_message(self, event: str, **kwargs: float) -> str | None:
        """Get a flavour text message for the given event.

        Args:
            event: The event type (see keys below).
            **kwargs: Context values (hp_ratio, etc.).

        Returns:
            A message string with timestamp prefix, or ``None`` if no message
            is appropriate.
        """
        msg = self._select_message(event, **kwargs)
        if msg is None:
            return None
        # Avoid repeating the same message
        if msg in self._seen_messages:
            return None
        self._seen_messages.add(msg)
        # Cap seen messages to prevent memory growth
        if len(self._seen_messages) > 50:
            self._seen_messages.clear()
        h, m, s = self._tick_clock()
        return _format_timestamp(h, m, s) + msg

    def _select_message(self, event: str, **kwargs: float) -> str | None:
        """Internal message selection logic."""
        hp_ratio = float(kwargs.get("hp_ratio", 1.0))

        if event == "engagement_start":
            return self._msg_engagement_start()
        if event == "damage_taken":
            return self._msg_damage_taken(hp_ratio)
        if event == "enemy_hit":
            return self._msg_enemy_hit()
        if event == "enemy_destroyed":
            return self._msg_enemy_destroyed()
        if event == "enemy_low_hp":
            return self._msg_enemy_low_hp()
        if event == "player_low_hp":
            return self._msg_player_low_hp()
        if event == "ol_warning":
            return self._msg_ol_warning()
        if event == "enemy_turn":
            return self._msg_enemy_turn()
        if event == "ambient":
            return self._msg_ambient()
        return None

    # ------------------------------------------------------------------
    # Message generators
    # ------------------------------------------------------------------

    def _msg_engagement_start(self) -> str:
        return random.choice(ENGAGEMENT_START)

    def _msg_damage_taken(self, hp_ratio: float) -> str:
        if hp_ratio < 0.25:
            return random.choice(DAMAGE_TAKEN_HIGH)
        if hp_ratio < 0.5:
            msg = random.choice(DAMAGE_TAKEN_MED)
            return msg.replace("{hp}", str(int(hp_ratio * 100)))
        return random.choice(DAMAGE_TAKEN_LOW)

    def _msg_enemy_hit(self) -> str:
        return random.choice(ENEMY_HIT)

    def _msg_enemy_destroyed(self) -> str:
        return random.choice(ENEMY_DESTROYED)

    def _msg_enemy_low_hp(self) -> str:
        return random.choice(ENEMY_LOW_HP)

    def _msg_player_low_hp(self) -> str:
        return random.choice(PLAYER_LOW_HP)

    def _msg_ol_warning(self) -> str:
        return random.choice(OL_WARNING)

    def _msg_enemy_turn(self) -> str:
        return random.choice(ENEMY_TURN)

    def _msg_ambient(self) -> str | None:
        """Ambient comms — occasionally include faction-specific messages."""
        self._ambient_counter += 1
        # Every 5th ambient message, try faction-specific
        if self._ambient_counter % 5 == 0:
            rep = self._campaign.get_reputation_level("rebel")
            cc_rep = self._campaign.get_reputation_level("crimson_compact")
            fsa_rep = self._campaign.get_reputation_level("fsa")

            if rep == "friendly" and REBEL_FRIENDLY:
                return random.choice(REBEL_FRIENDLY)
            if cc_rep == "hostile" and CC_HOSTILE:
                return random.choice(CC_HOSTILE)
            if cc_rep == "friendly" and CC_FRIENDLY:
                return random.choice(CC_FRIENDLY)
            if fsa_rep == "hostile" and FSA_HOSTILE:
                return random.choice(FSA_HOSTILE)

        # Floor-specific messages
        for (start, end), msgs in FLOOR_COMMS.items():
            if start <= self._floor <= end:
                return random.choice(msgs)

        # Generic ambient
        return random.choice(AMBIENT_COMMS)
