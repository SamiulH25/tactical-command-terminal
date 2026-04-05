"""Enemy AI — target selection and directive play for hostile mechs.

The AI follows a deterministic priority system:

1. **Target priority:** Lowest-HP friendly mech first (finish-off logic).
   Ties broken by closest distance.
2. **Directive selection:** Pick the highest-damage directive the enemy
   can afford (within OL budget) and that is in range of a visible target.
3. **Movement:** If no attack is possible, advance toward the nearest
   friendly.

Lore framing:  Enemy commanders are tactically competent but not
omniscient.  They only target friendlies within LOS and make decisions
based on the telemetry they can observe.
"""

from __future__ import annotations

from src.models.card import Directive
from src.systems.combat import CombatState, MechOnGrid
from src.systems.los import grid_distance, has_los


class EnemyAI:
    """Deterministic enemy turn controller.

    Usage::

        ai = EnemyAI(combat_state, directive_pool)
        ai.execute_enemy_turn()
    """

    def __init__(
        self,
        state: CombatState,
        directives: dict[str, Directive],
    ) -> None:
        """Create an EnemyAI.

        Args:
            state: The current combat state (mutable).
            directives: Full directive pool for looking up card data.
        """
        self.state = state
        self.directives = directives

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    def execute_enemy_turn(self) -> None:
        """Process all hostile mech actions for the enemy phase."""
        self.state.start_enemy_turn()

        for mg in list(self.state.hostiles):
            if not mg.mech.is_alive:
                continue
            self._execute_single(mg)
            # Check if combat ended mid-turn
            if self.state.check_completion() is not None:
                return

        self.state.end_enemy_turn()

    # ------------------------------------------------------------------
    # Single enemy mech action
    # ------------------------------------------------------------------

    def _execute_single(self, mg: MechOnGrid) -> None:
        """Decide and execute one hostile mech's action.

        Priority:
        1. Attack best visible target (if directive available and in range)
        2. Move toward nearest friendly
        """
        # Find visible friendlies
        visible = self._get_visible_targets(mg)
        if not visible:
            # No LOS to any friendly — move toward nearest
            self._move_toward_nearest(mg)
            return

        # Pick best target
        target = self._pick_target(visible)
        if target is None:
            return

        # Pick best directive for this target
        directive = self._pick_directive(mg, target)
        if directive is not None:
            self._attack(mg, target, directive)
        else:
            self._move_toward_nearest(mg)

    # ------------------------------------------------------------------
    # Visibility
    # ------------------------------------------------------------------

    def _get_visible_targets(self, attacker: MechOnGrid) -> list[MechOnGrid]:
        """Return friendly mechs visible to *attacker*."""
        visible: list[MechOnGrid] = []
        for f in self.state.friendlies:
            if has_los(
                self.state.grid,
                attacker.col,
                attacker.row,
                f.col,
                f.row,
            ):
                visible.append(f)
        return visible

    # ------------------------------------------------------------------
    # Target priority — lowest HP first, then closest
    # ------------------------------------------------------------------

    def _pick_target(self, candidates: list[MechOnGrid]) -> MechOnGrid | None:
        """Select the highest-priority target from *candidates*.

        Priority: lowest current HP first, then closest distance.
        """
        if not candidates:
            return None
        return min(
            candidates,
            key=lambda f: (
                f.mech.current_hp,
                grid_distance(self.state.mechs[0].col, self.state.mechs[0].row, f.col, f.row),
            ),
        )

    # ------------------------------------------------------------------
    # Directive selection — highest damage affordable and in range
    # ------------------------------------------------------------------

    def _pick_directive(self, mg: MechOnGrid, target: MechOnGrid) -> Directive | None:
        """Choose the best attack directive for *mg* against *target*.

        Criteria:
        - Must be a COMBAT type directive
        - Must be within mech's OL budget (current_ol + cost <= max_ol)
        - Must be within range of the target
        - Prefers highest damage; ties broken by lowest OL cost
        """
        mech = mg.mech
        dist = grid_distance(mg.col, mg.row, target.col, target.row)

        best: Directive | None = None
        for did in mech.deck:
            d = self.directives.get(did)
            if d is None:
                continue
            if d.directive_type.name != "COMBAT":
                continue
            # Check OL budget
            if mech.current_ol + d.overload_cost > mech.max_ol:
                continue
            # Check range
            if d.range_ > 0 and dist > d.range_:
                continue
            # Compare with current best
            eff_dmg = d.effective_damage(mech.weapon_bonus)
            if best is None:
                best = d
            else:
                best_dmg = best.effective_damage(mech.weapon_bonus)
                if eff_dmg > best_dmg or (
                    eff_dmg == best_dmg and d.overload_cost < best.overload_cost
                ):
                    best = d
        return best

    # ------------------------------------------------------------------
    # Attack execution
    # ------------------------------------------------------------------

    def _attack(
        self,
        attacker: MechOnGrid,
        target: MechOnGrid,
        directive: Directive,
    ) -> None:
        """Resolve an attack from *attacker* against *target*.

        Applies damage, OL cost, and records kills.
        """
        dmg = directive.effective_damage(attacker.mech.weapon_bonus)
        # Apply evasion (simplified: flat percentage miss chance)
        import random

        if random.randint(1, 100) <= target.mech.evasion:
            return  # Attack missed

        target.mech.take_damage(dmg)
        attacker.mech.current_ol += directive.overload_cost

        if not target.mech.is_alive:
            self.state.record_enemy_defeat()

    # ------------------------------------------------------------------
    # Movement — advance toward nearest friendly
    # ------------------------------------------------------------------

    def _move_toward_nearest(self, mg: MechOnGrid) -> None:
        """Move *mg* one cell closer to the nearest friendly mech."""
        if not self.state.friendlies:
            return
        nearest = min(
            self.state.friendlies,
            key=lambda f: grid_distance(mg.col, mg.row, f.col, f.row),
        )
        dc = 1 if nearest.col > mg.col else (-1 if nearest.col < mg.col else 0)
        dr = 1 if nearest.row > mg.row else (-1 if nearest.row < mg.row else 0)
        nc, nr = mg.col + dc, mg.row + dr
        if self.state.grid.is_valid(nc, nr):
            cell = self.state.grid.get_cell(nc, nr)
            if cell.is_passable and self.state.get_mech_at(nc, nr) is None:
                mg.col = nc
                mg.row = nr
