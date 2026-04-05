"""Tests for the combat state and AI systems."""

from src.models.card import Directive, DirectiveType, TargetPattern
from src.models.data_loader import GameData, load_all_data
from src.models.faction import Faction
from src.models.grid import CombatGrid, GridCell
from src.models.mech import DeployedMech, MechFrame
from src.systems.ai import EnemyAI
from src.systems.combat import (
    CombatPhase,
    CombatState,
    MechOnGrid,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_grid(w: int = 10, h: int = 10) -> CombatGrid:
    cells = [[GridCell(col=c, row=r) for c in range(w)] for r in range(h)]
    return CombatGrid(width=w, height=h, cells=cells)


def _make_frame() -> MechFrame:
    return MechFrame(
        id="test_frame",
        name="Test",
        faction=Faction.FSA,
        hp=20,
        overload=10,
        starting_directives=[
            "rifle_fire",
            "rifle_fire",
            "rifle_fire",
            "advance",
            "patch_up",
        ],
    )


def _make_deployed() -> DeployedMech:
    frame = _make_frame()
    return DeployedMech(
        frame=frame,
        pilot_callsign="Alpha-1",
        pilot_type="aggressive",
        max_hp=frame.hp,
        max_ol=frame.overload,
        current_hp=frame.hp,
        current_ol=0,
        deck=list(frame.starting_directives),
    )


def _make_data() -> GameData:
    """Load real data and add test directives if missing."""
    data = load_all_data()
    # Ensure rifle_fire exists (it should from JSON)
    if "rifle_fire" not in data.directives:
        data.directives["rifle_fire"] = Directive(
            id="rifle_fire",
            name="Rifle Fire",
            directive_type=DirectiveType.COMBAT,
            damage=4,
            overload_cost=1,
            range_=3,
            pattern=TargetPattern.SINGLE,
        )
    if "patch_up" not in data.directives:
        data.directives["patch_up"] = Directive(
            id="patch_up",
            name="Patch Up",
            directive_type=DirectiveType.REPAIR,
            heal=5,
            overload_cost=2,
            pattern=TargetPattern.SELF,
        )
    if "advance" not in data.directives:
        data.directives["advance"] = Directive(
            id="advance",
            name="Advance",
            directive_type=DirectiveType.MOVEMENT,
            move_range=3,
            overload_cost=1,
            pattern=TargetPattern.NONE,
        )
    return data


# ---------------------------------------------------------------------------
# CombatState
# ---------------------------------------------------------------------------


class TestCombatState:
    """Verify combat state management."""

    def _make_state(self) -> CombatState:
        grid = _make_grid()
        friendly = MechOnGrid(
            mech=_make_deployed(),
            col=2,
            row=5,
            friendly=True,
        )
        hostile_frame = MechFrame(
            id="enemy",
            name="Enemy",
            faction=Faction.CRIMSON_COMPACT,
            hp=15,
            overload=8,
            starting_directives=["rifle_fire", "rifle_fire"],
        )
        hostile = DeployedMech(
            frame=hostile_frame,
            pilot_callsign="HOSTILE-A",
            pilot_type="aggressive",
            max_hp=hostile_frame.hp,
            max_ol=hostile_frame.overload,
            current_hp=hostile_frame.hp,
            current_ol=0,
            deck=list(hostile_frame.starting_directives),
        )
        enemy = MechOnGrid(mech=hostile, col=7, row=5, friendly=False)
        return CombatState(grid=grid, mechs=[friendly, enemy])

    def test_begin_combat_sets_phase(self) -> None:
        state = self._make_state()
        state.begin_combat()
        assert state.phase == CombatPhase.PLAYER_DIRECTIVE_SELECT

    def test_begin_combat_draws_hand(self) -> None:
        state = self._make_state()
        state.begin_combat()
        assert len(state.hand) == 5

    def test_begin_combat_populates_pile(self) -> None:
        state = self._make_state()
        state.begin_combat()
        # Deck has 5 directives, hand draws 5, so draw pile may be empty
        assert len(state.hand) + len(state.draw_pile) == 5

    def test_friendlies_property(self) -> None:
        state = self._make_state()
        assert len(state.friendlies) == 1
        assert state.friendlies[0].friendly is True

    def test_hostiles_property(self) -> None:
        state = self._make_state()
        assert len(state.hostiles) == 1
        assert state.hostiles[0].friendly is False

    def test_all_hostiles_dead(self) -> None:
        state = self._make_state()
        state.hostiles[0].mech.take_damage(999)
        assert state.all_hostiles_dead is True

    def test_all_friendlies_dead(self) -> None:
        state = self._make_state()
        state.friendlies[0].mech.take_damage(999)
        assert state.all_friendlies_dead is True

    def test_get_mech_at(self) -> None:
        state = self._make_state()
        mg = state.get_mech_at(2, 5)
        assert mg is not None
        assert mg.friendly is True

    def test_get_mech_at_empty(self) -> None:
        state = self._make_state()
        assert state.get_mech_at(0, 0) is None

    def test_end_player_turn_discards_hand(self) -> None:
        state = self._make_state()
        state.begin_combat()
        state.end_player_turn()
        # Hand was discarded then reshuffled into new draw pile,
        # so discard is empty and hand has new cards
        assert len(state.discard_pile) == 0  # reshuffled into draw
        assert len(state.hand) == 5
        assert state.phase == CombatPhase.ENEMY_TURN

    def test_play_directive_moves_to_discard(self) -> None:
        state = self._make_state()
        state.begin_combat()
        initial_hand = len(state.hand)
        result = state.play_directive(0)
        assert result is True
        assert len(state.hand) == initial_hand - 1
        assert len(state.discard_pile) == 1
        assert state.cards_played_count == 1

    def test_play_directive_invalid_index(self) -> None:
        state = self._make_state()
        state.begin_combat()
        result = state.play_directive(999)
        assert result is False

    def test_play_directive_wrong_phase(self) -> None:
        state = self._make_state()
        state.begin_combat()
        state.phase = CombatPhase.ENEMY_TURN
        result = state.play_directive(0)
        assert result is False

    def test_check_completion_victory(self) -> None:
        state = self._make_state()
        state.hostiles[0].mech.take_damage(999)
        result = state.check_completion()
        assert result is not None
        assert result.victory is True
        assert result.defeat is False

    def test_check_completion_defeat(self) -> None:
        state = self._make_state()
        state.friendlies[0].mech.take_damage(999)
        result = state.check_completion()
        assert result is not None
        assert result.victory is False
        assert result.defeat is True

    def test_check_completion_no_result(self) -> None:
        state = self._make_state()
        result = state.check_completion()
        assert result is None

    def test_record_enemy_defeat(self) -> None:
        state = self._make_state()
        state.record_enemy_defeat()
        assert state.enemies_defeated_count == 1


# ---------------------------------------------------------------------------
# EnemyAI
# ---------------------------------------------------------------------------


class TestEnemyAI:
    """Verify enemy AI decision-making."""

    def _make_ai(self) -> tuple[CombatState, EnemyAI]:
        grid = _make_grid()
        # Friendly at (4, 5)
        friendly_mech = _make_deployed()
        friendly = MechOnGrid(mech=friendly_mech, col=4, row=5, friendly=True)

        # Enemy at (6, 5) with attack directives
        hostile_frame = MechFrame(
            id="enemy",
            name="Enemy",
            faction=Faction.CRIMSON_COMPACT,
            hp=15,
            overload=8,
            starting_directives=["rifle_fire", "rifle_fire", "rifle_fire"],
        )
        hostile = DeployedMech(
            frame=hostile_frame,
            pilot_callsign="HOSTILE-A",
            pilot_type="aggressive",
            max_hp=hostile_frame.hp,
            max_ol=hostile_frame.overload,
            current_hp=hostile_frame.hp,
            current_ol=0,
            deck=["rifle_fire", "rifle_fire", "rifle_fire"],
            weapon_bonus=1,
        )
        enemy = MechOnGrid(mech=hostile, col=6, row=5, friendly=False)

        state = CombatState(grid=grid, mechs=[friendly, enemy])
        data = _make_data()
        ai = EnemyAI(state, data.directives)
        return state, ai

    def test_ai_visible_targets(self) -> None:
        """AI should see the friendly mech (no walls)."""
        state, ai = self._make_ai()
        mg = state.hostiles[0]
        visible = ai._get_visible_targets(mg)
        assert len(visible) >= 1

    def test_ai_picks_lowest_hp_target(self) -> None:
        """When multiple targets, AI should pick the one with lowest HP."""
        state, ai = self._make_ai()
        # Add a second friendly with lower HP
        low_hp = _make_deployed()
        low_hp.current_hp = 3
        low = MechOnGrid(mech=low_hp, col=3, row=5, friendly=True)
        state.mechs.append(low)
        mg = state.hostiles[0]
        targets = ai._get_visible_targets(mg)
        target = ai._pick_target(targets)
        assert target is not None
        assert target.mech.current_hp == 3

    def test_ai_pick_directive_in_range(self) -> None:
        """AI should select a directive that can reach the target."""
        state, ai = self._make_ai()
        mech_on_grid = state.hostiles[0]
        target = state.friendlies[0]
        directive = ai._pick_directive(mech_on_grid, target)
        # rifle_fire has range 3, distance is 2 — should be selectable
        assert directive is not None

    def test_ai_move_toward_nearest(self) -> None:
        """If no attack possible, AI should move toward nearest friendly."""
        state, ai = self._make_ai()
        mg = state.hostiles[0]
        old_col, old_row = mg.col, mg.row
        ai._move_toward_nearest(mg)
        # Should have moved at least one cell closer
        assert mg.col != old_col or mg.row != old_row

    def test_ai_execute_enemy_turn_completes(self) -> None:
        """execute_enemy_turn should transition back to player phase."""
        state, ai = self._make_ai()
        state.begin_combat()
        ai.execute_enemy_turn()
        # After enemy turn, should be back to player phase
        assert state.phase == CombatPhase.PLAYER_DIRECTIVE_SELECT
