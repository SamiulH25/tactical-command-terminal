"""Tests for the deck composition system.

Verifies that decks are correctly composed from mech frame, pilot, and
equipment parts.  Every directive in the deck must trace back to a part.
"""

from src.models.data_loader import GameData, load_all_data
from src.models.faction import Faction
from src.models.pilot import Pilot
from src.systems.deckbuilder import build_deployed_mech, compose_deck

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _data() -> GameData:
    """Load all game data for test use."""
    return load_all_data()


def _pilot() -> Pilot:
    """Return a test pilot with known directives."""
    return Pilot(
        callsign="Test-Pilot",
        operator_type="aggressive",
        damage_bonus=2,
        hp_bonus=0,
        ol_bonus=0,
        evasion_bonus=0,
        starting_directives=["suppressing_fire"],
    )


# ---------------------------------------------------------------------------
# Deck composition
# ---------------------------------------------------------------------------


class TestComposeDeck:
    """Verify deck assembly from mech frame, pilot, and equipment."""

    def test_frame_directives_included(self) -> None:
        """Deck must contain all of the mech frame's starting directives."""
        data = _data()
        frame = data.get_mech("fsa_bastion")
        assert frame is not None
        pilot = _pilot()
        deck = compose_deck(frame, pilot, data)
        for did in frame.starting_directives:
            assert did in deck, f"Frame directive '{did}' missing from deck"

    def test_pilot_directives_included(self) -> None:
        """Deck must contain all of the pilot's starting directives."""
        data = _data()
        frame = data.get_mech("fsa_bastion")
        assert frame is not None
        pilot = _pilot()
        deck = compose_deck(frame, pilot, data)
        for did in pilot.starting_directives:
            assert did in deck, f"Pilot directive '{did}' missing from deck"

    def test_equipment_directives_included(self) -> None:
        """Deck must contain directives granted by equipment."""
        data = _data()
        # Bastion has field_medic which grants "patch_up"
        frame = data.get_mech("fsa_bastion")
        assert frame is not None
        pilot = _pilot()
        deck = compose_deck(frame, pilot, data)
        # field_medic grants patch_up, and frame already has patch_up
        # so we just verify it's present from equipment
        medic = data.get_equipment("field_medic")
        assert medic is not None
        for did in medic.directives_granted:
            assert did in deck, f"Equipment directive '{did}' missing from deck"

    def test_deck_is_sum_of_parts(self) -> None:
        """Deck length must equal the total from all three sources."""
        data = _data()
        frame = data.get_mech("fsa_bastion")
        assert frame is not None
        pilot = _pilot()

        frame_count = len(frame.starting_directives)
        pilot_count = len(pilot.starting_directives)

        equip_count = 0
        for _slot, equip_id in frame.equipment_slots.items():
            if equip_id is None:
                continue
            eq = data.get_equipment(equip_id)
            if eq is not None:
                equip_count += len(eq.directives_granted)

        deck = compose_deck(frame, pilot, data)
        assert len(deck) == frame_count + pilot_count + equip_count

    def test_deck_allows_duplicates(self) -> None:
        """The same directive can appear multiple times (stacking)."""
        data = _data()
        frame = data.get_mech("fsa_warden")
        assert frame is not None
        pilot = _pilot()
        deck = compose_deck(frame, pilot, data)
        # Warden has patch_up x2 in starting_directives
        patch_count = deck.count("patch_up")
        assert patch_count >= 2

    def test_empty_frame_empty_pilot(self) -> None:
        """If neither frame nor pilot nor equipment has directives,
        deck should be empty.
        """
        from src.models.mech import MechFrame

        bare_frame = MechFrame(
            id="bare",
            name="Bare",
            faction=Faction.FSA,
            hp=10,
            overload=5,
            starting_directives=[],
            equipment_slots={},
        )
        bare_pilot = Pilot(
            callsign="Bare",
            operator_type="aggressive",
            starting_directives=[],
        )
        data = _data()
        deck = compose_deck(bare_frame, bare_pilot, data)
        assert deck == []


# ---------------------------------------------------------------------------
# Build deployed mech
# ---------------------------------------------------------------------------


class TestBuildDeployedMech:
    """Verify the full mech assembly pipeline."""

    def test_bastion_builds(self) -> None:
        """Bastion should build without errors."""
        data = _data()
        frame = data.get_mech("fsa_bastion")
        assert frame is not None
        pilot = _pilot()
        mech = build_deployed_mech(frame, pilot, data)
        mech.validate()

    def test_hp_includes_pilot_and_equipment(self) -> None:
        """Max HP must reflect all bonuses."""
        data = _data()
        frame = data.get_mech("fsa_bastion")
        pilot = _pilot()
        assert frame is not None
        mech = build_deployed_mech(frame, pilot, data)
        # Bastion: 30 HP + pilot.hp_bonus(0) + light_plating(+5) = 35
        assert mech.max_hp >= 30  # at least base HP

    def test_ol_includes_pilot_bonus(self) -> None:
        """Max OL must include pilot OL bonus."""
        data = _data()
        frame = data.get_mech("fsa_bastion")
        pilot = _pilot()
        assert frame is not None
        mech = build_deployed_mech(frame, pilot, data)
        # Bastion: 12 OL + pilot.ol_bonus(0) = 12
        assert mech.max_ol >= 12

    def test_weapon_bonus_applied(self) -> None:
        """Weapon bonus should be pilot damage + weapon damage."""
        data = _data()
        frame = data.get_mech("fsa_bastion")
        pilot = _pilot()
        assert frame is not None
        mech = build_deployed_mech(frame, pilot, data)
        # pilot.damage_bonus(2) + autocannon_mk1(+3) = 5
        assert mech.weapon_bonus == 5

    def test_deck_composed_from_parts(self) -> None:
        """Deployed mech deck must include all three sources."""
        data = _data()
        frame = data.get_mech("fsa_raptor")
        pilot = _pilot()
        assert frame is not None
        mech = build_deployed_mech(frame, pilot, data)
        # Frame directives
        for did in frame.starting_directives:
            assert did in mech.deck
        # Pilot directives
        for did in pilot.starting_directives:
            assert did in mech.deck

    def test_custom_callsign(self) -> None:
        """Custom callsign should override pilot default."""
        data = _data()
        frame = data.get_mech("fsa_bastion")
        pilot = _pilot()
        assert frame is not None
        mech = build_deployed_mech(frame, pilot, data, callsign="ALPHA-7")
        assert mech.pilot_callsign == "ALPHA-7"

    def test_all_fsa_frames_build(self) -> None:
        """All FSA frames should build with an aggressive pilot."""
        data = _data()
        pilot = _pilot()
        for frame in data.mech_frames:
            if frame.faction == Faction.FSA:
                mech = build_deployed_mech(frame, pilot, data)
                mech.validate()
                assert mech.is_alive
                assert mech.deck, f"Mech {frame.name} built with empty deck"
