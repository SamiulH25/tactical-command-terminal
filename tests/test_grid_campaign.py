"""Tests for grid, encounter, campaign, and data loader modules."""

import pytest

from src.models.campaign import Campaign
from src.models.encounter import (
    Encounter,
    EncounterType,
    EnemySpawn,
    Floor,
    outpost_name_for_floor,
)
from src.models.grid import CombatGrid, GridCell, TerrainType

# ---------------------------------------------------------------------------
# GridCell
# ---------------------------------------------------------------------------


class TestGridCell:
    """Verify grid cell properties."""

    def test_open_cell(self) -> None:
        c = GridCell(col=0, row=0, terrain=TerrainType.OPEN)
        assert c.is_passable is True
        assert c.movement_cost == 1
        assert c.cover_bonus == 0
        assert c.symbol == " "
        c.validate()

    def test_cover_cell(self) -> None:
        c = GridCell(col=0, row=0, terrain=TerrainType.COVER)
        assert c.is_passable is True
        assert c.movement_cost == 1
        assert c.cover_bonus == 10
        assert c.symbol == "\u2591"  # ░

    def test_wall_cell(self) -> None:
        c = GridCell(col=0, row=0, terrain=TerrainType.WALL)
        assert c.is_passable is False
        assert c.movement_cost == -1
        assert c.symbol == "\u2588"  # █

    def test_high_ground(self) -> None:
        c = GridCell(col=0, row=0, terrain=TerrainType.HIGH_GROUND)
        assert c.is_passable is True
        assert c.movement_cost == 2
        assert c.symbol == "\u25b2"  # ▲

    def test_water(self) -> None:
        c = GridCell(col=0, row=0, terrain=TerrainType.WATER)
        assert c.is_passable is True
        assert c.movement_cost == 3
        assert c.symbol == "~"

    def test_negative_col_raises(self) -> None:
        with pytest.raises(ValueError, match="col"):
            GridCell(col=-1, row=0).validate()

    def test_negative_row_raises(self) -> None:
        with pytest.raises(ValueError, match="row"):
            GridCell(col=0, row=-1).validate()


# ---------------------------------------------------------------------------
# CombatGrid
# ---------------------------------------------------------------------------


class TestCombatGrid:
    """Verify combat grid construction and access."""

    def _make_grid(self, w: int = 10, h: int = 10) -> CombatGrid:
        cells = [[GridCell(col=c, row=r) for c in range(w)] for r in range(h)]
        return CombatGrid(width=w, height=h, cells=cells)

    def test_valid_grid(self) -> None:
        g = self._make_grid()
        g.validate()  # no raise
        assert g.width == 10
        assert g.height == 10

    def test_get_cell(self) -> None:
        g = self._make_grid()
        cell = g.get_cell(3, 5)
        assert cell.col == 3
        assert cell.row == 5

    def test_get_cell_out_of_bounds_col(self) -> None:
        g = self._make_grid()
        with pytest.raises(IndexError, match="col"):
            g.get_cell(10, 5)

    def test_get_cell_out_of_bounds_row(self) -> None:
        g = self._make_grid()
        with pytest.raises(IndexError, match="row"):
            g.get_cell(5, 10)

    def test_is_valid(self) -> None:
        g = self._make_grid()
        assert g.is_valid(0, 0) is True
        assert g.is_valid(9, 9) is True
        assert g.is_valid(10, 0) is False
        assert g.is_valid(0, 10) is False
        assert g.is_valid(-1, 0) is False

    def test_zero_width_raises(self) -> None:
        with pytest.raises(ValueError, match="width"):
            CombatGrid(width=0, height=1, cells=[])

    def test_zero_height_raises(self) -> None:
        with pytest.raises(ValueError, match="height"):
            CombatGrid(width=1, height=0, cells=[])

    def test_row_length_mismatch_raises(self) -> None:
        cells = [[GridCell(col=0, row=0)]]
        with pytest.raises(ValueError, match="cols"):
            CombatGrid(width=2, height=1, cells=cells)

    def test_coord_mismatch_raises(self) -> None:
        cells = [[GridCell(col=99, row=99)]]
        with pytest.raises(ValueError, match="mismatched"):
            CombatGrid(width=1, height=1, cells=cells)

    def test_terrain_variety(self) -> None:
        cells = [
            [
                GridCell(col=c, row=r, terrain=TerrainType.WALL if c == 5 else TerrainType.OPEN)
                for c in range(10)
            ]
            for r in range(10)
        ]
        g = CombatGrid(width=10, height=10, cells=cells)
        assert g.get_cell(5, 5).terrain == TerrainType.WALL
        assert g.get_cell(5, 5).is_passable is False
        assert g.get_cell(0, 0).is_passable is True


# ---------------------------------------------------------------------------
# EnemySpawn
# ---------------------------------------------------------------------------


class TestEnemySpawn:
    """Verify enemy spawn validation."""

    def test_valid_spawn(self) -> None:
        s = EnemySpawn(mech_id="cc_bastion", grid_col=3, grid_row=5)
        s.validate()

    def test_empty_mech_id_raises(self) -> None:
        with pytest.raises(ValueError, match="mech_id"):
            EnemySpawn(mech_id="").validate()

    def test_negative_col_raises(self) -> None:
        with pytest.raises(ValueError, match="grid_col"):
            EnemySpawn(mech_id="x", grid_col=-1).validate()

    def test_negative_row_raises(self) -> None:
        with pytest.raises(ValueError, match="grid_row"):
            EnemySpawn(mech_id="x", grid_row=-1).validate()


# ---------------------------------------------------------------------------
# Encounter
# ---------------------------------------------------------------------------


class TestEncounter:
    """Verify encounter validation."""

    def test_combat_encounter(self) -> None:
        enc = Encounter(
            id="floor1_combat",
            encounter_type=EncounterType.COMBAT,
            enemies=[EnemySpawn(mech_id="cc_bastion")],
        )
        enc.validate()

    def test_event_encounter(self) -> None:
        enc = Encounter(
            id="floor1_event",
            encounter_type=EncounterType.EVENT,
            choices=[
                {"text": "Help them", "outcome_id": "help_outcome"},
                {"text": "Ignore them", "outcome_id": "ignore_outcome"},
            ],
        )
        enc.validate()

    def test_merchant_encounter(self) -> None:
        enc = Encounter(
            id="floor1_merchant",
            encounter_type=EncounterType.MERCHANT,
        )
        enc.validate()  # no enemies or choices required

    def test_rest_encounter(self) -> None:
        enc = Encounter(
            id="floor1_rest",
            encounter_type=EncounterType.REST,
        )
        enc.validate()

    def test_empty_id_raises(self) -> None:
        with pytest.raises(ValueError, match="id"):
            Encounter(id="", encounter_type=EncounterType.COMBAT).validate()

    def test_combat_no_enemies_raises(self) -> None:
        with pytest.raises(ValueError, match="enemy"):
            Encounter(
                id="bad_combat",
                encounter_type=EncounterType.COMBAT,
            ).validate()

    def test_event_no_choices_raises(self) -> None:
        with pytest.raises(ValueError, match="choice"):
            Encounter(
                id="bad_event",
                encounter_type=EncounterType.EVENT,
            ).validate()


# ---------------------------------------------------------------------------
# Floor
# ---------------------------------------------------------------------------


class TestFloor:
    """Verify floor validation and outpost naming."""

    def _make_floor(self, num: int = 1) -> Floor:
        enc = Encounter(
            id="test_enc",
            encounter_type=EncounterType.COMBAT,
            enemies=[EnemySpawn(mech_id="cc_bastion")],
        )
        return Floor(number=num, encounters=[enc])

    def test_valid_floor(self) -> None:
        f = self._make_floor()
        f.validate()
        assert f.outpost_name == "Outpost Alpha"

    def test_outpost_names(self) -> None:
        """Each sector should map to the correct outpost name."""
        expected = {
            1: "Outpost Alpha",
            5: "Outpost Alpha",
            6: "Outpost Bravo",
            10: "Outpost Bravo",
            11: "Outpost Charlie",
            15: "Outpost Charlie",
            16: "Outpost Delta",
            20: "Outpost Delta",
            21: "Command Fortress",
            25: "Command Fortress",
        }
        for num, name in expected.items():
            f = self._make_floor(num)
            assert f.outpost_name == name

    def test_floor_number_range(self) -> None:
        with pytest.raises(ValueError, match="out of range"):
            Floor(
                number=0,
                encounters=[
                    Encounter(
                        id="x",
                        encounter_type=EncounterType.COMBAT,
                        enemies=[EnemySpawn(mech_id="x")],
                    )
                ],
            ).validate()

    def test_floor_no_encounters_raises(self) -> None:
        with pytest.raises(ValueError, match="encounter"):
            Floor(number=1, encounters=[]).validate()


def test_outpost_name_for_floor_valid() -> None:
    """All floor numbers 1-25 should return a name."""
    for i in range(1, 26):
        name = outpost_name_for_floor(i)
        assert isinstance(name, str)
        assert len(name) > 0


def test_outpost_name_for_floor_invalid() -> None:
    with pytest.raises(ValueError, match="out of range"):
        outpost_name_for_floor(0)


# ---------------------------------------------------------------------------
# Campaign
# ---------------------------------------------------------------------------


class TestCampaign:
    """Verify campaign state management."""

    def _make(self) -> Campaign:
        return Campaign(current_floor=0)

    def test_initial_state(self) -> None:
        c = self._make()
        assert c.current_floor == 0
        assert c.floors_cleared == 0
        assert c.current_credits == 150
        assert c.decision_log == []
        c.validate()

    def test_advance_floor(self) -> None:
        c = self._make()
        assert c.advance_floor() == 1
        assert c.current_floor == 1
        assert c.floors_cleared == 0  # floor 1 not yet cleared

    def test_advance_to_25(self) -> None:
        c = self._make()
        for _ in range(25):
            c.advance_floor()
        assert c.current_floor == 25
        assert c.floors_cleared == 24

    def test_advance_beyond_25_raises(self) -> None:
        c = self._make()
        for _ in range(25):
            c.advance_floor()
        with pytest.raises(ValueError, match="final floor"):
            c.advance_floor()

    def test_reputation_adjust(self) -> None:
        c = self._make()
        c.adjust_reputation("rebel", 20)
        assert c.reputation["rebel"] == 20
        assert c.get_reputation_level("rebel") == "friendly"

    def test_reputation_clamped(self) -> None:
        c = self._make()
        c.adjust_reputation("fsa", -200)
        assert c.reputation["fsa"] == -100
        c.adjust_reputation("fsa", 300)
        assert c.reputation["fsa"] == 100

    def test_reputation_invalid_faction(self) -> None:
        c = self._make()
        with pytest.raises(ValueError, match="Unknown faction"):
            c.adjust_reputation("aliens", 10)

    def test_reputation_levels(self) -> None:
        c = self._make()
        assert c.get_reputation_level("fsa") == "neutral"
        c.adjust_reputation("fsa", -40)
        assert c.get_reputation_level("fsa") == "hostile"
        c.adjust_reputation("fsa", 50)
        assert c.get_reputation_level("fsa") == "friendly"

    def test_decision_log(self) -> None:
        c = self._make()
        c.record_decision("event:help_rebel")
        c.record_decision("combat:spare_enemy")
        assert c.has_decision("event:help_rebel") is True
        assert c.has_decision("event:ignore_rebel") is False
        assert len(c.decisions_of_type("event:")) == 1

    def test_empty_decision_id_raises(self) -> None:
        c = self._make()
        with pytest.raises(ValueError, match="non-empty"):
            c.record_decision("")

    def test_outpost_name(self) -> None:
        c = self._make()
        assert c.outpost_name == "Pre-Deployment"
        c.advance_floor()
        assert c.outpost_name == "Outpost Alpha"
        for _ in range(10):
            c.advance_floor()
        assert c.outpost_name == "Outpost Charlie"

    def test_validation_negative_floor(self) -> None:
        c = self._make()
        c.current_floor = -1
        with pytest.raises(ValueError, match="current_floor"):
            c.validate()

    def test_validation_reputation_out_of_range(self) -> None:
        c = self._make()
        c.reputation["fsa"] = 200
        with pytest.raises(ValueError, match="reputation"):
            c.validate()

    def test_validation_empty_decision(self) -> None:
        c = self._make()
        c.decision_log.append("")
        with pytest.raises(ValueError, match="empty string"):
            c.validate()


# ---------------------------------------------------------------------------
# Data Loader
# ---------------------------------------------------------------------------


class TestGameData:
    """Verify the master data loader."""

    def test_load_all_data(self) -> None:
        """All JSON data should load without errors."""
        from src.models.data_loader import load_all_data

        data = load_all_data()
        assert len(data.mech_frames) >= 12  # 5 FSA + 4 CC + 3 Rebel
        assert len(data.equipment) >= 10
        assert len(data.pilots) == 5  # aggressive, defensive, tactical, scout, engineer
        assert len(data.directives) >= 15

    def test_get_mech(self) -> None:
        from src.models.data_loader import load_all_data

        data = load_all_data()
        mech = data.get_mech("fsa_bastion")
        assert mech is not None
        assert mech.name == "Bastion"
        assert data.get_mech("nonexistent") is None

    def test_get_directive(self) -> None:
        from src.models.data_loader import load_all_data

        data = load_all_data()
        d = data.get_directive("autocannon_burst")
        assert d is not None
        assert d.damage == 6
        assert data.get_directive("nonexistent") is None

    def test_get_equipment(self) -> None:
        from src.models.data_loader import load_all_data

        data = load_all_data()
        eq = data.get_equipment("autocannon_mk1")
        assert eq is not None
        assert eq.damage_bonus == 3

    def test_get_pilot(self) -> None:
        from src.models.data_loader import load_all_data

        data = load_all_data()
        p = data.get_pilot("aggressive")
        assert p is not None
        assert p.damage_bonus == 2

    def test_missing_file_raises(self) -> None:
        from src.models import data_loader

        with pytest.raises(FileNotFoundError):
            data_loader._load_json(data_loader._DATA_ROOT / "nonexistent.json")
