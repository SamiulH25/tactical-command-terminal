"""Tests for faction, mech, equipment, pilot, and directive models."""

import pytest

from src.models.card import Directive, DirectiveType, TargetPattern
from src.models.equipment import Equipment
from src.models.faction import FACTION_COLOUR, Faction, IFFShape
from src.models.mech import DeployedMech, MechFrame
from src.models.pilot import Pilot

# ---------------------------------------------------------------------------
# Faction
# ---------------------------------------------------------------------------


class TestFaction:
    """Verify faction enum and colour mappings."""

    def test_all_factions_have_colour(self) -> None:
        """Every faction must have an RGB colour defined."""
        for faction in Faction:
            assert faction in FACTION_COLOUR
            colour = FACTION_COLOUR[faction]
            assert len(colour) == 3
            for channel in colour:
                assert 0 <= channel <= 255

    def test_iff_shape_values(self) -> None:
        """All expected IFF shapes must exist."""
        expected = {
            "SQUARE",
            "DIAMOND",
            "HEXAGON",
            "CIRCLE_CROSS",
            "CHEVRON",
            "TRIANGLE",
            "RECTANGLE",
            "CIRCLE",
            "CROSS",
        }
        actual = {s.name for s in IFFShape}
        assert expected == actual


# ---------------------------------------------------------------------------
# Equipment
# ---------------------------------------------------------------------------


class TestEquipment:
    """Verify equipment validation."""

    def _valid(self) -> Equipment:
        return Equipment(
            id="test_gun",
            name="Test Gun",
            slot="weapon",
            damage_bonus=3,
        )

    def test_valid_equipment(self) -> None:
        """Valid equipment should not raise on validate()."""
        self._valid().validate()

    def test_empty_id_raises(self) -> None:
        with pytest.raises(ValueError, match="id must be non-empty"):
            Equipment(id="", name="X", slot="weapon").validate()

    def test_empty_name_raises(self) -> None:
        with pytest.raises(ValueError, match="name must be non-empty"):
            Equipment(id="x", name="", slot="weapon").validate()

    def test_invalid_slot_raises(self) -> None:
        with pytest.raises(ValueError, match="slot"):
            Equipment(id="x", name="X", slot="helm").validate()

    def test_damage_bonus_range(self) -> None:
        with pytest.raises(ValueError, match="damage_bonus"):
            Equipment(id="x", name="X", slot="weapon", damage_bonus=200).validate()

    def test_hp_bonus_range(self) -> None:
        with pytest.raises(ValueError, match="hp_bonus"):
            Equipment(id="x", name="X", slot="weapon", hp_bonus=2000).validate()

    def test_evasion_bonus_range(self) -> None:
        with pytest.raises(ValueError, match="evasion_bonus"):
            Equipment(id="x", name="X", slot="weapon", evasion_bonus=100).validate()

    def test_ol_discount_range(self) -> None:
        with pytest.raises(ValueError, match="ol_discount"):
            Equipment(id="x", name="X", slot="weapon", ol_discount=20).validate()


# ---------------------------------------------------------------------------
# Pilot
# ---------------------------------------------------------------------------


class TestPilot:
    """Verify pilot validation."""

    def _valid(self) -> Pilot:
        return Pilot(callsign="Alpha-1", operator_type="aggressive")

    def test_valid_pilot(self) -> None:
        """Valid pilot should not raise."""
        self._valid().validate()

    def test_empty_callsign_raises(self) -> None:
        with pytest.raises(ValueError, match="callsign"):
            Pilot(callsign="", operator_type="aggressive").validate()

    def test_empty_operator_raises(self) -> None:
        with pytest.raises(ValueError, match="operator_type"):
            Pilot(callsign="A", operator_type="").validate()

    def test_invalid_operator_type(self) -> None:
        with pytest.raises(ValueError, match="operator_type"):
            Pilot(callsign="A", operator_type="wizard").validate()

    def test_valid_operator_types(self) -> None:
        """All five operator types should be accepted."""
        for op in ("aggressive", "defensive", "tactical", "scout", "engineer"):
            Pilot(callsign="A", operator_type=op).validate()

    def test_damage_bonus_range(self) -> None:
        with pytest.raises(ValueError, match="damage_bonus"):
            Pilot(callsign="A", operator_type="aggressive", damage_bonus=100).validate()


# ---------------------------------------------------------------------------
# Directive
# ---------------------------------------------------------------------------


class TestDirective:
    """Verify directive validation and computed properties."""

    def _valid(self) -> Directive:
        return Directive(
            id="test_attack",
            name="Test Attack",
            directive_type=DirectiveType.COMBAT,
            damage=6,
            overload_cost=2,
            range_=4,
            pattern=TargetPattern.SINGLE,
            keywords=frozenset({"kinetic"}),
        )

    def test_valid_directive(self) -> None:
        self._valid().validate()

    def test_empty_id_raises(self) -> None:
        with pytest.raises(ValueError, match="id"):
            Directive(id="", name="X", directive_type=DirectiveType.COMBAT).validate()

    def test_empty_name_raises(self) -> None:
        with pytest.raises(ValueError, match="name"):
            Directive(id="x", name="", directive_type=DirectiveType.COMBAT).validate()

    def test_negative_damage_raises(self) -> None:
        with pytest.raises(ValueError, match="damage"):
            self._valid().validate()  # damage=6 ok
            Directive(
                id="x",
                name="X",
                directive_type=DirectiveType.COMBAT,
                damage=-1,
            ).validate()

    def test_negative_ol_raises(self) -> None:
        with pytest.raises(ValueError, match="overload_cost"):
            Directive(
                id="x",
                name="X",
                directive_type=DirectiveType.COMBAT,
                overload_cost=-1,
            ).validate()

    def test_effective_damage_with_bonus(self) -> None:
        d = self._valid()
        assert d.effective_damage(weapon_bonus=3) == 9
        assert d.effective_damage(weapon_bonus=-2) == 4
        assert d.effective_damage(weapon_bonus=-10) == 0  # floored

    def test_effective_ol_with_discount(self) -> None:
        d = self._valid()
        assert d.effective_ol_cost(discount=1) == 1
        assert d.effective_ol_cost(discount=5) == 0  # floored

    def test_self_pattern(self) -> None:
        d = Directive(
            id="self_heal",
            name="Self Heal",
            directive_type=DirectiveType.REPAIR,
            heal=5,
            pattern=TargetPattern.SELF,
        )
        d.validate()
        assert d.pattern == TargetPattern.SELF


# ---------------------------------------------------------------------------
# MechFrame
# ---------------------------------------------------------------------------


class TestMechFrame:
    """Verify mech frame validation."""

    def _valid(self) -> MechFrame:
        return MechFrame(
            id="test_mech",
            name="Test Mech",
            faction=Faction.FSA,
            hp=20,
            overload=10,
        )

    def test_valid_frame(self) -> None:
        self._valid().validate()

    def test_empty_id_raises(self) -> None:
        with pytest.raises(ValueError, match="id"):
            MechFrame(
                id="",
                name="X",
                faction=Faction.FSA,
                hp=10,
                overload=10,
            ).validate()

    def test_empty_name_raises(self) -> None:
        with pytest.raises(ValueError, match="name"):
            MechFrame(
                id="x",
                name="",
                faction=Faction.FSA,
                hp=10,
                overload=10,
            ).validate()

    def test_zero_hp_raises(self) -> None:
        with pytest.raises(ValueError, match="hp"):
            MechFrame(
                id="x",
                name="X",
                faction=Faction.FSA,
                hp=0,
                overload=10,
            ).validate()

    def test_zero_ol_raises(self) -> None:
        with pytest.raises(ValueError, match="overload"):
            MechFrame(
                id="x",
                name="X",
                faction=Faction.FSA,
                hp=10,
                overload=0,
            ).validate()

    def test_invalid_equipment_slot(self) -> None:
        with pytest.raises(ValueError, match="Equipment slot"):
            MechFrame(
                id="x",
                name="X",
                faction=Faction.FSA,
                hp=10,
                overload=10,
                equipment_slots={"jetpack": "test"},
            ).validate()

    def test_all_fsa_frames_valid(self) -> None:
        """Sanity: FSA mech frames from data should be valid."""
        from src.models.data_loader import load_mech_frames

        frames = load_mech_frames()
        fsa = [f for f in frames if f.faction == Faction.FSA]
        assert len(fsa) >= 5  # Bastion, Raptor, Anvil, Warden, Wraith
        for f in fsa:
            f.validate()  # no raise


# ---------------------------------------------------------------------------
# DeployedMech
# ---------------------------------------------------------------------------


class TestDeployedMech:
    """Verify deployed mech state management."""

    def _make(self) -> DeployedMech:
        frame = MechFrame(
            id="t",
            name="T",
            faction=Faction.FSA,
            hp=20,
            overload=10,
        )
        return DeployedMech(
            frame=frame,
            pilot_callsign="Alpha-1",
            pilot_type="aggressive",
            max_hp=20,
            max_ol=10,
            current_hp=20,
            current_ol=0,
        )

    def test_initial_state(self) -> None:
        m = self._make()
        assert m.is_alive is True
        assert m.is_engaged is False
        m.validate()  # no raise

    def test_take_damage(self) -> None:
        m = self._make()
        dealt = m.take_damage(8)
        assert dealt == 8
        assert m.current_hp == 12
        assert m.is_alive is True

    def test_take_damage_capped(self) -> None:
        m = self._make()
        dealt = m.take_damage(999)
        assert dealt == 20
        assert m.current_hp == 0
        assert m.is_alive is False

    def test_take_negative_damage_raises(self) -> None:
        m = self._make()
        with pytest.raises(ValueError, match="damage amount"):
            m.take_damage(-1)

    def test_heal(self) -> None:
        m = self._make()
        m.take_damage(10)
        healed = m.heal(7)
        assert healed == 7
        assert m.current_hp == 17

    def test_heal_capped(self) -> None:
        m = self._make()
        m.take_damage(5)
        healed = m.heal(100)
        assert healed == 5  # only 5 needed to reach max
        assert m.current_hp == 20

    def test_negative_heal_raises(self) -> None:
        m = self._make()
        with pytest.raises(ValueError, match="heal amount"):
            m.heal(-1)

    def test_spend_ol_success(self) -> None:
        m = self._make()
        assert m.spend_ol(5) is True
        assert m.current_ol == 5
        assert m.is_engaged is True

    def test_spend_ol_failure(self) -> None:
        m = self._make()
        assert m.spend_ol(11) is False  # max_ol is 10
        assert m.current_ol == 0

    def test_negative_ol_raises(self) -> None:
        m = self._make()
        with pytest.raises(ValueError, match="OL cost"):
            m.spend_ol(-1)

    def test_reset_ol(self) -> None:
        m = self._make()
        m.spend_ol(3)
        m.reset_ol()
        assert m.current_ol == 0
        assert m.is_engaged is False

    def test_validation_out_of_range(self) -> None:
        m = self._make()
        m.current_hp = 999
        with pytest.raises(ValueError, match="current_hp"):
            m.validate()
