"""Combat state — the authoritative state of an ongoing combat encounter.

The CombatState tracks every mech (friendly and hostile), their grid
positions, the current turn phase, the active mech, and the directive
queue.  It is the single source of truth for the combat system and is
read by the CombatHUD for rendering.

Lore framing:  The Coordinator's terminal displays combat as a series of
telemetry snapshots.  Each turn represents a discrete update cycle of the
tactical feed.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from enum import Enum, auto

from src.models.card import Directive
from src.models.data_loader import GameData
from src.models.grid import CombatGrid
from src.models.mech import DeployedMech


class CombatPhase(Enum):
    """Current phase of the combat loop."""

    PLAYER_DIRECTIVE_SELECT = auto()
    PLAYER_TARGETING = auto()
    PLAYER_ANIMATING = auto()
    ENEMY_TURN = auto()
    COMBAT_COMPLETE = auto()


@dataclass
class MechOnGrid:
    """A deployed mech placed on the combat grid."""

    mech: DeployedMech
    col: int
    row: int
    friendly: bool = True


@dataclass
class CombatResult:
    """The outcome of a completed combat encounter."""

    victory: bool
    defeat: bool
    enemies_defeated: int = 0
    cards_played: int = 0
    current_credits_earned: int = 0


@dataclass
class CombatState:
    """The complete mutable state of a combat encounter."""

    grid: CombatGrid
    mechs: list[MechOnGrid] = field(default_factory=list)
    phase: CombatPhase | None = None
    active_mech_index: int = -1
    result: CombatResult | None = None

    # Directive queue state for the active mech
    hand: list[str] = field(default_factory=list)
    draw_pile: list[str] = field(default_factory=list)
    discard_pile: list[str] = field(default_factory=list)
    energy: int = 3
    max_energy: int = 3

    # Statistics
    enemies_defeated_count: int = 0
    cards_played_count: int = 0

    # ------------------------------------------------------------------
    # Initialisation
    # ------------------------------------------------------------------

    def begin_combat(self) -> None:
        """Transition to the player's first turn."""
        self.phase = CombatPhase.PLAYER_DIRECTIVE_SELECT
        self._build_initial_piles()
        self._draw_hand(5)

    def _build_initial_piles(self) -> None:
        """Populate draw pile from all friendly mech decks."""
        self.draw_pile = []
        for mg in self.mechs:
            if mg.friendly and mg.mech.is_alive:
                self.draw_pile.extend(mg.mech.deck)
        self._shuffle_pile()

    def _shuffle_pile(self) -> None:
        """Shuffle the draw pile."""
        random.shuffle(self.draw_pile)

    def _draw_hand(self, count: int) -> None:
        """Draw *count* cards into hand, reshuffling discard if needed."""
        for _ in range(count):
            if not self.draw_pile and self.discard_pile:
                self.draw_pile = list(self.discard_pile)
                self.discard_pile.clear()
                self._shuffle_pile()
            if self.draw_pile:
                self.hand.append(self.draw_pile.pop())

    # ------------------------------------------------------------------
    # Mech queries
    # ------------------------------------------------------------------

    @property
    def friendlies(self) -> list[MechOnGrid]:
        """All living friendly mechs."""
        return [m for m in self.mechs if m.friendly and m.mech.is_alive]

    @property
    def hostiles(self) -> list[MechOnGrid]:
        """All living hostile mechs."""
        return [m for m in self.mechs if not m.friendly and m.mech.is_alive]

    @property
    def all_friendlies_dead(self) -> bool:
        """Whether the player has lost."""
        return not self.friendlies

    @property
    def all_hostiles_dead(self) -> bool:
        """Whether the player has won."""
        return not self.hostiles

    def get_mech_at(self, col: int, row: int) -> MechOnGrid | None:
        """Return the mech at the given grid position, if any."""
        for mg in self.mechs:
            if mg.mech.is_alive and mg.col == col and mg.row == row:
                return mg
        return None

    # ------------------------------------------------------------------
    # Turn management
    # ------------------------------------------------------------------

    def start_player_turn(self) -> None:
        """Reset energy and OL for the player's turn."""
        self.energy = self.max_energy
        self.phase = CombatPhase.PLAYER_DIRECTIVE_SELECT

    def end_player_turn(self) -> None:
        """Transition to the enemy turn phase."""
        self.phase = CombatPhase.ENEMY_TURN
        self.discard_pile.extend(self.hand)
        self.hand.clear()
        for mg in self.friendlies:
            mg.mech.reset_ol()
        self._draw_hand(5)

    def start_enemy_turn(self) -> None:
        """Begin enemy action processing."""
        self.phase = CombatPhase.ENEMY_TURN

    def end_enemy_turn(self) -> None:
        """End the enemy phase and start the next player turn."""
        self.phase = CombatPhase.PLAYER_DIRECTIVE_SELECT
        self.energy = self.max_energy
        self._draw_hand(5)

    # ------------------------------------------------------------------
    # Directive play
    # ------------------------------------------------------------------

    def play_directive(
        self,
        hand_index: int,
        game_data: GameData | None = None,
        target_col: int | None = None,
        target_row: int | None = None,
    ) -> bool:
        """Attempt to play a directive from hand."""
        if self.phase not in (
            CombatPhase.PLAYER_DIRECTIVE_SELECT,
            CombatPhase.PLAYER_TARGETING,
        ):
            return False
        if not (0 <= hand_index < len(self.hand)):
            return False

        directive_id = self.hand[hand_index]
        directive = None
        if game_data is not None:
            directive = game_data.directives.get(directive_id)

        if directive is None:
            self.hand.pop(hand_index)
            self.discard_pile.append(directive_id)
            self.energy = max(0, self.energy - 1)
            self.cards_played_count += 1
            return True

        if self.energy < directive.overload_cost:
            return False

        self._resolve_directive(directive, target_col, target_row, game_data)
        self.energy -= directive.overload_cost
        self.hand.pop(hand_index)
        self.discard_pile.append(directive_id)
        self.cards_played_count += 1
        return True

    def _resolve_directive(
        self,
        directive: Directive,
        target_col: int | None,
        target_row: int | None,
        game_data: GameData | None,
    ) -> None:
        """Resolve a directive's effects on the combat grid."""
        from src.models.card import DirectiveType

        player_mech = self.friendlies[0] if self.friendlies else None
        if player_mech is None:
            return

        weapon_bonus = player_mech.mech.weapon_bonus

        if directive.directive_type == DirectiveType.COMBAT:
            self._resolve_combat_directive(
                directive, player_mech, target_col, target_row, weapon_bonus
            )
        elif directive.directive_type == DirectiveType.MOVEMENT:
            self._resolve_movement_directive(directive, player_mech, target_col, target_row)
        elif directive.directive_type == DirectiveType.REPAIR:
            self._resolve_repair_directive(directive, player_mech)
        elif directive.directive_type == DirectiveType.UTILITY:
            self._resolve_utility_directive(directive, player_mech, target_col, target_row)

    def _resolve_combat_directive(
        self,
        directive: Directive,
        source: MechOnGrid,
        target_col: int | None,
        target_row: int | None,
        weapon_bonus: int,
    ) -> None:
        """Apply damage from a combat directive."""
        from src.systems.los import has_los

        dmg = directive.effective_damage(weapon_bonus)
        pattern = directive.pattern
        rng = directive.range_

        # Dispatch via pattern value integer to avoid mypy narrowing.
        _key = pattern.value
        if _key == 2:  # SINGLE
            if target_col is not None and target_row is not None:
                target = self.get_mech_at(target_col, target_row)
                if (
                    target is not None
                    and not target.friendly
                    and target.mech.is_alive
                    and has_los(
                        self.grid,
                        source.col,
                        source.row,
                        target_col,
                        target_row,
                    )
                ):
                    dist = _grid_distance(source.col, source.row, target_col, target_row)
                    if dist <= rng:
                        target.mech.take_damage(dmg)
                        self._count_if_dead(target)
        elif _key == 3:  # LINE
            if target_col is not None and target_row is not None:
                self._attack_line(dmg, source, target_col, target_row)
        elif _key == 5:  # AREA
            if target_col is not None and target_row is not None:
                self._attack_area(dmg, target_col, target_row)
        elif _key == 4:  # CONE
            if target_col is not None and target_row is not None:
                self._attack_cone(dmg, source, target_col, target_row)
        elif _key == 7:  # ALL_HOSTILES
            self._attack_all(dmg)

    def _count_if_dead(self, mech: MechOnGrid) -> None:
        """Increment defeat counter if mech was destroyed."""
        if mech.mech.current_hp <= 0:
            self.enemies_defeated_count += 1

    def _attack_line(
        self,
        dmg: int,
        source: MechOnGrid,
        target_col: int,
        target_row: int,
    ) -> None:
        """Damage all enemies along a line from source to target."""
        from src.systems.los import bresenham_cells

        cells = bresenham_cells(source.col, source.row, target_col, target_row)
        for c, r in cells:
            enemy = self.get_mech_at(c, r)
            if enemy is not None and not enemy.friendly and enemy.mech.is_alive:
                enemy.mech.take_damage(dmg)
                self._count_if_dead(enemy)

    def _attack_area(
        self,
        dmg: int,
        target_col: int,
        target_row: int,
    ) -> None:
        """Damage all enemies in a 3x3 area."""
        for dr in range(-1, 2):
            for dc in range(-1, 2):
                tc, tr = target_col + dc, target_row + dr
                enemy = self.get_mech_at(tc, tr)
                if enemy is not None and not enemy.friendly and enemy.mech.is_alive:
                    enemy.mech.take_damage(dmg)
                    self._count_if_dead(enemy)

    def _attack_cone(
        self,
        dmg: int,
        source: MechOnGrid,
        target_col: int,
        target_row: int,
    ) -> None:
        """Damage all enemies in a cone toward target."""
        cone = self._cells_in_cone(source.col, source.row, target_col, target_row, 3)
        for tc, tr in cone:
            enemy = self.get_mech_at(tc, tr)
            if enemy is not None and not enemy.friendly and enemy.mech.is_alive:
                enemy.mech.take_damage(dmg)
                self._count_if_dead(enemy)

    def _attack_all(self, dmg: int) -> None:
        """Damage all hostile mechs."""
        for enemy in list(self.hostiles):
            enemy.mech.take_damage(dmg)
            self._count_if_dead(enemy)

    def _resolve_movement_directive(
        self,
        directive: Directive,
        source: MechOnGrid,
        target_col: int | None,
        target_row: int | None,
    ) -> None:
        """Reposition a mech based on a movement directive."""
        move_range = directive.move_range
        if move_range <= 0:
            return
        if target_col is not None and target_row is not None:
            dist = _grid_distance(source.col, source.row, target_col, target_row)
            if dist <= move_range and self.grid.is_valid(target_col, target_row):
                cell = self.grid.get_cell(target_col, target_row)
                if cell.is_passable:
                    source.col = target_col
                    source.row = target_row

    def _resolve_repair_directive(
        self,
        directive: Directive,
        source: MechOnGrid,
    ) -> None:
        """Apply healing from a repair directive."""
        source.mech.heal(directive.heal)

    def _resolve_utility_directive(
        self,
        directive: Directive,
        source: MechOnGrid,
        target_col: int | None,
        target_row: int | None,
    ) -> None:
        """Apply utility effects (buffs, self-heal, etc.)."""
        from src.models.card import TargetPattern

        pattern = directive.pattern

        if pattern == TargetPattern.SELF:
            if directive.heal > 0:
                source.mech.heal(directive.heal)
        elif (
            pattern == TargetPattern.SINGLE and target_col is not None and target_row is not None
        ) or pattern == TargetPattern.ALL_HOSTILES:
            pass  # Needs status system

    def _cells_in_cone(
        self,
        from_col: int,
        from_row: int,
        to_col: int,
        to_row: int,
        radius: int,
    ) -> list[tuple[int, int]]:
        """Return cells in a cone from source toward target."""
        cells: list[tuple[int, int]] = []
        if from_col == to_col and from_row == to_row:
            return cells
        dx = to_col - from_col
        dy = to_row - from_row
        angle = math.atan2(dy, dx)
        for r in range(1, radius + 1):
            for spread in range(-1, 2):
                a = angle + spread * 0.3
                c = int(from_col + r * math.cos(a))
                row = int(from_row + r * math.sin(a))
                if self.grid.is_valid(c, row):
                    cells.append((c, row))
        return cells

    # ------------------------------------------------------------------
    # Combat completion
    # ------------------------------------------------------------------

    def check_completion(self) -> CombatResult | None:
        """Check whether combat has ended and record the result."""
        if self.result is not None:
            return self.result

        if self.all_hostiles_dead:
            self.result = CombatResult(
                victory=True,
                defeat=False,
                enemies_defeated=self.enemies_defeated_count,
                cards_played=self.cards_played_count,
            )
            self.phase = CombatPhase.COMBAT_COMPLETE
        elif self.all_friendlies_dead:
            self.result = CombatResult(
                victory=False,
                defeat=True,
                enemies_defeated=self.enemies_defeated_count,
                cards_played=self.cards_played_count,
            )
            self.phase = CombatPhase.COMBAT_COMPLETE

        return self.result

    def record_enemy_defeat(self) -> None:
        """Increment the defeated enemy counter."""
        self.enemies_defeated_count += 1


def _grid_distance(c1: int, r1: int, c2: int, r2: int) -> float:
    """Euclidean distance between two grid cells."""
    return math.sqrt((c2 - c1) ** 2 + (r2 - r1) ** 2)
