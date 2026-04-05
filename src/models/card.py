"""Directive (card) definitions — tactical orders issued to mechs.

Directives are the player's primary interaction in combat.  Each directive
has a type (combat, movement, repair, utility), an overload cost, and
one or more effects (damage, healing, movement range).  Patterns define
how the directive targets tiles on the grid.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto


class DirectiveType(Enum):
    """Broad category of a directive's effect."""

    COMBAT = auto()  #: Deals damage to hostiles
    MOVEMENT = auto()  #: Repositions the mech
    REPAIR = auto()  #: Restores HP or removes debuffs
    UTILITY = auto()  #: Buffs, debuffs, or tactical effects


class TargetPattern(Enum):
    """Shape of the targeting area on the combat grid."""

    NONE = auto()  #: No target needed (self-buff)
    SINGLE = auto()  #: Single tile
    LINE = auto()  #: Straight line from origin
    CONE = auto()  #: 3-tile cone / fan
    AREA = auto()  #: 3x3 area centred on target
    SELF = auto()  #: Always targets the owning mech
    ALL_HOSTILES = auto()  #: Affects every hostile on the grid


@dataclass(frozen=True)
class Directive:
    """A single tactical order that can be played from the hand.

    Invariants:
    - ``damage`` and ``heal`` are non-negative.
    - ``overload_cost`` is non-negative (zero means free).
    - ``range_`` is positive for targeted directives.
    - ``keywords`` is a set of string tags for rules interactions.
    """

    id: str
    """Unique directive identifier (e.g. ``"autocannon_burst"``)."""

    name: str
    """Display name (e.g. ``"Autocannon Burst"``)."""

    directive_type: DirectiveType
    """Broad category of effect."""

    damage: int = 0
    """Base damage dealt to each valid target."""

    heal: int = 0
    """Base HP restored to the target."""

    overload_cost: int = 0
    """Overload points consumed when this directive is played."""

    range_: int = 0
    """Maximum targeting range in grid cells (0 = melee / self)."""

    move_range: int = 0
    """Movement range in cells (for movement directives)."""

    pattern: TargetPattern = TargetPattern.NONE
    """How targets are resolved on the grid."""

    keywords: frozenset[str] = field(default_factory=frozenset)
    """Tags for rules interactions (e.g. ``"kinetic"``, ``"suppress"``)."""

    description: str = ""
    """Short tactical description shown in the briefing."""

    def validate(self) -> None:
        """Raise ``ValueError`` if any field is out of range.

        Raises:
            ValueError: If ``id`` or ``name`` is empty, numeric values are
                negative, or ``range_`` is negative.
        """
        if not self.id:
            raise ValueError("Directive id must be non-empty")
        if not self.name:
            raise ValueError("Directive name must be non-empty")
        if self.damage < 0:
            raise ValueError(f"damage {self.damage} must be >= 0")
        if self.heal < 0:
            raise ValueError(f"heal {self.heal} must be >= 0")
        if self.overload_cost < 0:
            raise ValueError(f"overload_cost {self.overload_cost} must be >= 0")
        if self.range_ < 0:
            raise ValueError(f"range_ {self.range_} must be >= 0")
        if self.move_range < 0:
            raise ValueError(f"move_range {self.move_range} must be >= 0")

    def effective_damage(self, weapon_bonus: int = 0) -> int:
        """Return damage after applying equipment and pilot bonuses.

        Args:
            weapon_bonus: Flat damage bonus from equipped weapon and pilot.
        """
        return max(0, self.damage + weapon_bonus)

    def effective_ol_cost(self, discount: int = 0) -> int:
        """Return overload cost after applying equipment discounts.

        Args:
            discount: Overload reduction from equipped modules.
        """
        return max(0, self.overload_cost - discount)
