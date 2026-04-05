"""Mech frame definitions — the core unit of combat.

A mech is a combination of a base frame (HP, OL, IFF shape), an
assigned pilot, and three equipment slots (weapon, armour, utility).
All base stats come from JSON data; runtime state (current HP, current OL)
is tracked separately in the combat system.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from src.models.faction import Faction, IFFShape


@dataclass(frozen=True)
class MechFrame:
    """A mech frame definition — base stats and visual identity.

    This is the **template** loaded from JSON.  A deployed mech
    combines a ``MechFrame`` with a :class:`~src.models.pilot.Pilot`
    and :class:`~src.models.equipment.Equipment` items.

    Invariants:
    - ``hp`` and ``overload`` are positive.
    - ``iff_shape`` is set.
    - ``faction`` determines display colour and AI behaviour.
    - ``starting_directives`` contains directive IDs for the base deck.
    """

    id: str
    """Unique frame identifier (e.g. ``"fsa_bastion"``)."""

    name: str
    """Frame name (e.g. ``"Bastion"``)."""

    faction: Faction
    """Owning faction for IFF colour and AI."""

    hp: int
    """Base maximum hit points."""

    overload: int
    """Base maximum overload capacity."""

    evasion: int = 0
    """Base evasion percentage."""

    iff_shape: IFFShape = IFFShape.SQUARE
    """Geometric IFF transponder shape."""

    starting_directives: list[str] = field(default_factory=list)
    """Directive IDs in the mech's base deck."""

    equipment_slots: dict[str, str | None] = field(default_factory=dict)
    """Default equipment per slot: ``{"weapon": ..., "armor": ..., "utility": ...}``."""

    trait: str = ""
    """Passive ability description (e.g. ``"Heavy Plating: -25% damage"``)."""

    role: str = ""
    """Tactical role: ``"tank"``, ``"scout"``, ``"heavy"``, ``"defender"``,
    ``"stealth"``."""

    def validate(self) -> None:
        """Raise ``ValueError`` if any field is invalid.

        Raises:
            ValueError: If ``id`` or ``name`` is empty, ``hp`` or
                ``overload`` is non-positive, or slots contain invalid
                keys.
        """
        if not self.id:
            raise ValueError("Mech frame id must be non-empty")
        if not self.name:
            raise ValueError("Mech frame name must be non-empty")
        if self.hp <= 0:
            raise ValueError(f"hp {self.hp} must be > 0")
        if self.overload <= 0:
            raise ValueError(f"overload {self.overload} must be > 0")
        valid_slots = {"weapon", "armor", "utility"}
        for slot_key in self.equipment_slots:
            if slot_key not in valid_slots:
                raise ValueError(f"Equipment slot '{slot_key}' not in {valid_slots}")


@dataclass
class DeployedMech:
    """A mech frame with pilot and equipment applied — combat-ready.

    The combat **deck** is derived from three sources:
    1. ``MechFrame.starting_directives`` — base deck from the frame
    2. ``Pilot.starting_directives`` — extra cards from the pilot archetype
    3. ``Equipment.directives_granted`` — cards granted by each equipped item

    Unlike ``MechFrame`` (frozen template), this is mutable because it
    tracks current HP and OL during combat.

    Invariants:
    - ``current_hp`` is clamped to ``[0, max_hp]``.
    - ``current_ol`` is clamped to ``[0, max_ol]``.
    - ``deck`` is the concatenation of all parts' directive lists.
    """

    frame: MechFrame
    """The base frame template."""

    pilot_callsign: str
    """The pilot's callsign."""

    pilot_type: str
    """The pilot's operator type."""

    max_hp: int
    """Effective maximum HP (frame + pilot + equipment bonuses)."""

    max_ol: int
    """Effective maximum overload (frame + pilot bonuses)."""

    current_hp: int
    """Current hit points."""

    current_ol: int
    """Current overload points consumed."""

    weapon_bonus: int = 0
    """Flat damage bonus from weapon equipment and pilot."""

    evasion: int = 0
    """Effective evasion percentage."""

    ol_discount: int = 0
    """Overload cost reduction from equipment."""

    deck: list[str] = field(default_factory=list)
    """List of directive IDs in the combat deck."""

    def validate(self) -> None:
        """Ensure current values are within bounds.

        Raises:
            ValueError: If HP or OL are outside valid range.
        """
        if not (0 <= self.current_hp <= self.max_hp):
            raise ValueError(f"current_hp {self.current_hp} out of range [0, {self.max_hp}]")
        if not (0 <= self.current_ol <= self.max_ol):
            raise ValueError(f"current_ol {self.current_ol} out of range [0, {self.max_ol}]")

    def take_damage(self, amount: int) -> int:
        """Apply damage and return the actual amount dealt.

        Args:
            amount: Raw incoming damage.

        Returns:
            The actual damage applied (may be less if capped by current HP).
        """
        if amount < 0:
            raise ValueError(f"damage amount {amount} must be >= 0")
        actual = min(amount, self.current_hp)
        self.current_hp -= actual
        return actual

    def heal(self, amount: int) -> int:
        """Restore HP and return the actual amount healed.

        Args:
            amount: Raw healing value.

        Returns:
            Actual HP restored (capped at max_hp).
        """
        if amount < 0:
            raise ValueError(f"heal amount {amount} must be >= 0")
        actual = min(amount, self.max_hp - self.current_hp)
        self.current_hp += actual
        return actual

    def spend_ol(self, amount: int) -> bool:
        """Consume overload points.

        Args:
            amount: OL cost.

        Returns:
            ``True`` if the cost was paid, ``False`` if insufficient OL.
        """
        if amount < 0:
            raise ValueError(f"OL cost {amount} must be >= 0")
        if self.current_ol + amount > self.max_ol:
            return False
        self.current_ol += amount
        return True

    def reset_ol(self) -> None:
        """Reset overload to zero at the start of the mech's turn."""
        self.current_ol = 0

    @property
    def is_alive(self) -> bool:
        """Whether the mech still has HP remaining."""
        return self.current_hp > 0

    @property
    def is_engaged(self) -> bool:
        """Whether the mech has taken any action this turn."""
        return self.current_ol > 0
