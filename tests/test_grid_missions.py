"""Tests for grid layouts and mission system overhaul.

Tests cover:
- All 12 grid layouts load and build valid CombatGrids
- Layout selection by floor range works correctly
- Boss and elite layout pools are distinct
- Mission types generate valid encounters
- Enemy compositions scale with floor
- Encounter narrative text is present and varied
- Boss encounters on milestone floors
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.models.encounter import EncounterType
from src.models.grid import TerrainType
from src.models.grid_layouts import (
    _BOSS_LAYOUTS,
    _ELITE_LAYOUTS,
    ALL_LAYOUTS,
    GridLayout,
    get_layouts_for_floor,
    get_random_layout,
)
from src.models.missions import (
    _BOSS_ENEMIES,
    _ELITE_ENEMIES,
    _ENEMY_POOLS,
    _FLOOR_MISSIONS,
    _MISSION_SPECS,
    MissionType,
    generate_combat_encounter,
    generate_event_encounter,
    generate_merchant_encounter,
    generate_rest_encounter,
    get_mission_types_for_floor,
    is_boss_floor,
)
from src.systems.progression import (
    FLOOR_NARRATIVES,
    FloorProgression,
    _default_floor,
)

if TYPE_CHECKING:
    from src.models.campaign import Campaign


# ---------------------------------------------------------------------------
# Grid Layout Tests
# ---------------------------------------------------------------------------


class TestGridLayouts:
    """Verify all grid layouts are valid and build correctly."""

    def test_all_layouts_count(self) -> None:
        """Should have at least 10 distinct layouts."""
        assert len(ALL_LAYOUTS) >= 10

    def test_all_layouts_valid_names(self) -> None:
        """Layout names should be non-empty strings."""
        for name in ALL_LAYOUTS:
            assert isinstance(name, str)
            assert len(name) > 0

    def test_open_plains_builds(self) -> None:
        """Open plains layout should build a valid grid."""
        layout = ALL_LAYOUTS["open_plains"]
        grid = layout.build_grid()
        assert grid.width == 12
        assert grid.height == 10
        assert grid.is_valid(0, 0)
        assert grid.is_valid(11, 9)

    def test_urban_ruins_has_walls(self) -> None:
        """Urban ruins should have WALL terrain."""
        layout = ALL_LAYOUTS["urban_ruins"]
        grid = layout.build_grid()
        has_wall = False
        for r in range(grid.height):
            for c in range(grid.width):
                cell = grid.get_cell(c, r)
                if cell.terrain == TerrainType.WALL:
                    has_wall = True
        assert has_wall

    def test_command_bunker_has_walls(self) -> None:
        """Command bunker should have extensive walls forming corridors."""
        layout = ALL_LAYOUTS["command_bunker"]
        grid = layout.build_grid()
        wall_count = 0
        for r in range(grid.height):
            for c in range(grid.width):
                cell = grid.get_cell(c, r)
                if cell.terrain == TerrainType.WALL:
                    wall_count += 1
        assert wall_count >= 20  # Should have substantial walls

    def test_final_stand_is_arena(self) -> None:
        """Final stand should be an arena with some cover."""
        layout = ALL_LAYOUTS["final_stand"]
        grid = layout.build_grid()
        # Should have cover
        has_cover = False
        for r in range(grid.height):
            for c in range(grid.width):
                cell = grid.get_cell(c, r)
                if cell.terrain == TerrainType.COVER:
                    has_cover = True
        assert has_cover

    def test_flooded_basin_has_water(self) -> None:
        """Flooded basin should have WATER terrain."""
        layout = ALL_LAYOUTS["flooded_basin"]
        grid = layout.build_grid()
        has_water = False
        for r in range(grid.height):
            for c in range(grid.width):
                cell = grid.get_cell(c, r)
                if cell.terrain == TerrainType.WATER:
                    has_water = True
        assert has_water

    def test_ridge_line_has_high_ground(self) -> None:
        """Ridge line should have HIGH_GROUND terrain."""
        layout = ALL_LAYOUTS["ridge_line"]
        grid = layout.build_grid()
        has_high = False
        for r in range(grid.height):
            for c in range(grid.width):
                cell = grid.get_cell(c, r)
                if cell.terrain == TerrainType.HIGH_GROUND:
                    has_high = True
        assert has_high

    def test_bridge_crossing_water(self) -> None:
        """Bridge crossing should be mostly water with a dry path."""
        layout = ALL_LAYOUTS["bridge_crossing"]
        grid = layout.build_grid()
        water_count = 0
        open_count = 0
        for r in range(grid.height):
            for c in range(grid.width):
                cell = grid.get_cell(c, r)
                if cell.terrain == TerrainType.WATER:
                    water_count += 1
                elif cell.terrain == TerrainType.OPEN:
                    open_count += 1
        assert water_count > open_count  # Mostly water

    def test_trench_network_cover(self) -> None:
        """Trench network should have lots of COVER."""
        layout = ALL_LAYOUTS["trench_network"]
        grid = layout.build_grid()
        cover_count = 0
        for r in range(grid.height):
            for c in range(grid.width):
                cell = grid.get_cell(c, r)
                if cell.terrain == TerrainType.COVER:
                    cover_count += 1
        assert cover_count >= 20

    def test_all_layouts_build_without_error(self) -> None:
        """Every registered layout should build a grid without raising."""
        for _name, layout in ALL_LAYOUTS.items():
            grid = layout.build_grid()
            assert grid.width == 12
            assert grid.height == 10


# ---------------------------------------------------------------------------
# Layout Selection Tests
# ---------------------------------------------------------------------------


class TestLayoutSelection:
    """Verify floor-based layout selection logic."""

    def test_floor_1_returns_early_layouts(self) -> None:
        layouts = get_layouts_for_floor(1)
        assert "open_plains" in layouts
        assert "urban_ruins" in layouts

    def test_floor_5_returns_early_layouts(self) -> None:
        layouts = get_layouts_for_floor(5)
        assert "canyon_pass" in layouts

    def test_floor_10_returns_mid_layouts(self) -> None:
        layouts = get_layouts_for_floor(10)
        assert "flooded_basin" in layouts
        assert "ridge_line" in layouts

    def test_floor_20_returns_late_layouts(self) -> None:
        layouts = get_layouts_for_floor(20)
        assert "urban_ruins" in layouts
        assert "ridge_line" in layouts

    def test_floor_25_returns_final_layouts(self) -> None:
        layouts = get_layouts_for_floor(25)
        assert "command_bunker" in layouts
        assert "final_stand" in layouts

    def test_boss_returns_boss_layouts(self) -> None:
        layouts = get_layouts_for_floor(1, is_boss=True)
        assert all(layout_id in _BOSS_LAYOUTS for layout_id in layouts)

    def test_elite_returns_elite_layouts(self) -> None:
        layouts = get_layouts_for_floor(1, is_elite=True)
        assert all(layout_id in _ELITE_LAYOUTS for layout_id in layouts)

    def test_boss_layouts_distinct_from_early(self) -> None:
        """Boss layouts should not all be available on floor 1."""
        early = set(get_layouts_for_floor(1))
        boss = set(_BOSS_LAYOUTS)
        assert not boss.issubset(early) or len(boss - early) > 0

    def test_get_random_layout_returns_layout(self) -> None:
        layout = get_random_layout(1)
        assert isinstance(layout, GridLayout)
        grid = layout.build_grid()
        assert grid.width == 12

    def test_floor_layout_ranges_cover_1_to_25(self) -> None:
        """Every floor 1-25 should have at least one layout."""
        for floor in range(1, 26):
            layouts = get_layouts_for_floor(floor)
            assert len(layouts) > 0, f"No layouts for floor {floor}"


# ---------------------------------------------------------------------------
# Mission Type Tests
# ---------------------------------------------------------------------------


class TestMissionTypes:
    """Verify mission type definitions and scheduling."""

    def test_all_mission_types_have_specs(self) -> None:
        for mtype in MissionType:
            assert mtype in _MISSION_SPECS

    def test_patrol_is_easy(self) -> None:
        spec = _MISSION_SPECS[MissionType.PATROL]
        assert spec.enemy_count == 2
        assert spec.credit_base == 40

    def test_boss_is_hard(self) -> None:
        spec = _MISSION_SPECS[MissionType.BOSS]
        assert spec.enemy_count >= 3
        assert spec.credit_base >= 100

    def test_elite_has_good_rewards(self) -> None:
        spec = _MISSION_SPECS[MissionType.ELITE]
        assert spec.credit_base >= 70
        assert spec.card_pick >= 2

    def test_floor_1_only_patrol(self) -> None:
        types = get_mission_types_for_floor(1)
        assert types == [MissionType.PATROL]

    def test_floor_10_has_multiple_types(self) -> None:
        types = get_mission_types_for_floor(10)
        assert len(types) >= 3

    def test_floor_25_has_boss(self) -> None:
        types = get_mission_types_for_floor(25)
        assert MissionType.BOSS in types

    def test_mission_types_increase_with_floor(self) -> None:
        """Higher floors should have access to at least as many types."""
        early = get_mission_types_for_floor(5)
        late = get_mission_types_for_floor(15)
        assert len(late) >= len(early)


# ---------------------------------------------------------------------------
# Enemy Pool Tests
# ---------------------------------------------------------------------------


class TestEnemyPools:
    """Verify enemy availability by floor."""

    def test_enemy_pools_cover_all_floors(self) -> None:
        for floor in range(1, 26):
            found = False
            for (lo, hi), pool in _ENEMY_POOLS.items():
                if lo <= floor <= hi:
                    assert len(pool) > 0
                    found = True
            assert found, f"No enemy pool for floor {floor}"

    def test_boss_enemies_defined(self) -> None:
        assert len(_BOSS_ENEMIES) == 5  # floors 5, 10, 15, 20, 25

    def test_boss_floors_correct(self) -> None:
        for floor in (5, 10, 15, 20, 25):
            assert is_boss_floor(floor)

    def test_non_boss_floors(self) -> None:
        for floor in (1, 2, 3, 4, 6, 7, 11, 12, 21, 24):
            assert not is_boss_floor(floor)

    def test_elite_enemies_defined(self) -> None:
        assert len(_ELITE_ENEMIES) >= 1

    def test_boss_enemy_ids_exist(self) -> None:
        for _floor, enemy_id in _BOSS_ENEMIES.items():
            assert enemy_id in ("cc_bastion", "cc_siege", "cc_warden", "cc_sentinel")


# ---------------------------------------------------------------------------
# Encounter Generation Tests
# ---------------------------------------------------------------------------


class TestEncounterGeneration:
    """Verify encounter generation produces valid encounters."""

    def test_combat_encounter_floor_1(self) -> None:
        enc = generate_combat_encounter(1)
        assert enc.encounter_type == EncounterType.COMBAT
        assert len(enc.enemies) >= 1
        assert enc.rewards.get("credits", 0) > 0

    def test_combat_encounter_floor_10(self) -> None:
        enc = generate_combat_encounter(10)
        assert enc.encounter_type == EncounterType.COMBAT
        assert len(enc.enemies) >= 1

    def test_combat_encounter_floor_25(self) -> None:
        enc = generate_combat_encounter(25)
        assert enc.encounter_type == EncounterType.COMBAT
        assert len(enc.enemies) >= 2

    def test_boss_encounter_floor_5(self) -> None:
        enc = generate_combat_encounter(5, force_boss=True)
        assert enc.encounter_type == EncounterType.COMBAT
        # Boss should have multiple enemies
        assert len(enc.enemies) >= 2

    def test_boss_has_correct_enemy(self) -> None:
        for floor in (5, 10, 15, 20, 25):
            enc = generate_combat_encounter(floor, force_boss=True)
            boss_id = _BOSS_ENEMIES[floor]
            enemy_ids = [e.mech_id for e in enc.enemies]
            assert boss_id in enemy_ids

    def test_enemy_positions_valid(self) -> None:
        enc = generate_combat_encounter(5)
        for enemy in enc.enemies:
            assert enemy.grid_col >= 0
            assert enemy.grid_row >= 0

    def test_event_encounter_has_choices(self) -> None:
        enc = generate_event_encounter(1)
        assert enc.encounter_type == EncounterType.EVENT
        assert len(enc.choices) >= 2

    def test_event_encounter_varied_text(self) -> None:
        """Multiple event encounters should have different text."""
        texts = set()
        for _ in range(10):
            enc = generate_event_encounter(1)
            texts.add(enc.narrative_text[:20])
        assert len(texts) >= 2  # At least some variation

    def test_merchant_encounter(self) -> None:
        enc = generate_merchant_encounter(1)
        assert enc.encounter_type == EncounterType.MERCHANT

    def test_rest_encounter(self) -> None:
        enc = generate_rest_encounter(1)
        assert enc.encounter_type == EncounterType.REST

    def test_combat_rewards_scale_with_floor(self) -> None:
        enc_1 = generate_combat_encounter(1)
        enc_20 = generate_combat_encounter(20)
        assert enc_20.rewards["credits"] > enc_1.rewards["credits"]

    def test_combat_narrative_present(self) -> None:
        enc = generate_combat_encounter(5)
        assert len(enc.narrative_text) > 10

    def test_encounter_id_unique_across_floors(self) -> None:
        ids = set()
        for floor in range(1, 26):
            enc = generate_combat_encounter(floor)
            assert enc.id not in ids, f"Duplicate encounter id: {enc.id}"
            ids.add(enc.id)


# ---------------------------------------------------------------------------
# Floor Progression Integration Tests
# ---------------------------------------------------------------------------


class TestFloorProgressionIntegration:
    """Verify the full progression system with new missions."""

    def test_default_floor_combat(self) -> None:
        ft = _default_floor(1)
        assert ft.combat.encounter_type == EncounterType.COMBAT
        assert len(ft.combat.enemies) >= 1

    def test_default_floor_optional_encounters(self) -> None:
        ft = _default_floor(3)
        # optional_a should be event (3 % 3 == 0 -> merchant)
        assert ft.optional_a.encounter_type == EncounterType.MERCHANT

    def test_default_floor_rest(self) -> None:
        ft = _default_floor(1)
        assert ft.optional_b.encounter_type == EncounterType.REST

    def test_default_floor_narrative_present(self) -> None:
        ft = _default_floor(1)
        assert "INSERTION" in ft.narrative_intro

    def test_boss_floor_5_has_boss_encounter(self) -> None:
        ft = _default_floor(5)
        enc = ft.combat
        assert len(enc.enemies) >= 2  # Boss + escorts

    def test_progression_templates_generated(self) -> None:
        prog = FloorProgression(_make_campaign())
        assert len(prog._templates) == 25

    def test_progression_get_encounters(self) -> None:
        prog = FloorProgression(_make_campaign())
        prog.campaign.current_floor = 1
        encounters = prog.get_encounters()
        assert encounters is not None
        assert len(encounters) == 3

    def test_progression_transition_text(self) -> None:
        prog = FloorProgression(_make_campaign())
        text = prog.get_transition_text(1, 2)
        assert "SECTOR 02" in text
        assert "SIGNAL RE-ACQUIRED" in text

    def test_floor_mission_scheduling(self) -> None:
        for (_lo, _hi), types in _FLOOR_MISSIONS.items():
            assert len(types) > 0
            for t in types:
                assert t in _MISSION_SPECS


# ---------------------------------------------------------------------------
# Floor Narratives
# ---------------------------------------------------------------------------


class TestFloorNarratives:
    """Verify narrative text coverage."""

    def test_narratives_for_boss_floors(self) -> None:
        for floor in (5, 10, 15, 20, 25):
            assert floor in FLOOR_NARRATIVES

    def test_narratives_have_intro_and_outro(self) -> None:
        for _floor, (intro, outro) in FLOOR_NARRATIVES.items():
            assert len(intro) > 10
            assert len(outro) > 10

    def test_narrative_count(self) -> None:
        assert len(FLOOR_NARRATIVES) >= 9


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_campaign() -> Campaign:
    from src.models.campaign import Campaign

    return Campaign()
