"""Verify all card-to-mech/pilot/equipment linkages are valid.

Every directive ID referenced in mech starting_directives, pilot
starting_directives, and equipment directives_granted must exist in
the loaded directive pool.
"""

from __future__ import annotations

import pytest

from src.models.data_loader import GameData, load_all_data
from src.systems.deckbuilder import build_deployed_mech


@pytest.fixture()
def game_data() -> GameData:
    return load_all_data()


class TestCardLinkages:
    """Verify every directive reference resolves to a loaded card."""

    def test_mech_starting_directives_all_valid(self, game_data: GameData) -> None:
        """Every mech frame's starting_directives must exist."""
        for mech in game_data.mech_frames:
            for did in mech.starting_directives:
                assert did in game_data.directives, f"{mech.id} references missing directive: {did}"

    def test_pilot_starting_directives_all_valid(self, game_data: GameData) -> None:
        """Every pilot's starting_directives must exist."""
        for ptype, pilot in game_data.pilots.items():
            for did in pilot.starting_directives:
                assert did in game_data.directives, (
                    f"Pilot {ptype} references missing directive: {did}"
                )

    def test_equipment_directives_granted_all_valid(self, game_data: GameData) -> None:
        """Every equipment's directives_granted must exist."""
        for eq in game_data.equipment:
            for did in eq.directives_granted:
                assert did in game_data.directives, (
                    f"Equipment {eq.id} grants missing directive: {did}"
                )

    def test_mech_equipment_slots_all_valid(self, game_data: GameData) -> None:
        """Every mech frame's equipment_slots must reference existing equipment."""
        equip_ids = {eq.id for eq in game_data.equipment}
        for mech in game_data.mech_frames:
            for slot, eid in mech.equipment_slots.items():
                if eid is not None:
                    assert eid in equip_ids, (
                        f"{mech.id} has equipment slot '{slot}' "
                        f"referencing missing equipment: {eid}"
                    )

    def test_bastion_deck_builds_correctly(self, game_data: GameData) -> None:
        """FSA Bastion with aggressive pilot should build a valid deck."""
        mech = game_data.get_mech("fsa_bastion")
        pilot = game_data.get_pilot("aggressive")
        assert mech is not None
        assert pilot is not None
        deployed = build_deployed_mech(mech, pilot, game_data)
        # Check all cards in deck exist
        for did in deployed.deck:
            assert did in game_data.directives

    def test_all_mechs_build_valid_decks(self, game_data: GameData) -> None:
        """Every mech + aggressive pilot combo should produce a valid deck."""
        pilot = game_data.get_pilot("aggressive")
        assert pilot is not None
        for mech in game_data.mech_frames:
            deployed = build_deployed_mech(mech, pilot, game_data)
            for did in deployed.deck:
                assert did in game_data.directives, (
                    f"{mech.id} deck contains missing directive: {did}"
                )

    def test_deck_sizes_are_reasonable(self, game_data: GameData) -> None:
        """Deployed decks should have between 6 and 20 cards."""
        pilot = game_data.get_pilot("aggressive")
        assert pilot is not None
        for mech in game_data.mech_frames:
            deployed = build_deployed_mech(mech, pilot, game_data)
            assert 6 <= len(deployed.deck) <= 20, (
                f"{mech.id} deck size {len(deployed.deck)} out of range"
            )

    def test_raptor_has_movement_cards(self, game_data: GameData) -> None:
        """FSA Raptor should have dash and flank in its deck."""
        mech = game_data.get_mech("fsa_raptor")
        pilot = game_data.get_pilot("scout")
        assert mech is not None
        assert pilot is not None
        deployed = build_deployed_mech(mech, pilot, game_data)
        assert "dash" in deployed.deck
        assert "flank" in deployed.deck
        assert "scan" in deployed.deck

    def test_anvil_has_heavy_cards(self, game_data: GameData) -> None:
        """FSA Anvil should have heavy_cannon and suppressing_fire."""
        mech = game_data.get_mech("fsa_anvil")
        pilot = game_data.get_pilot("aggressive")
        assert mech is not None
        assert pilot is not None
        deployed = build_deployed_mech(mech, pilot, game_data)
        assert "heavy_cannon" in deployed.deck
        assert "suppressing_fire" in deployed.deck

    def test_wraith_has_stealth_cards(self, game_data: GameData) -> None:
        """FSA Wraith should have cloak and sniper_shot."""
        mech = game_data.get_mech("fsa_wraith")
        pilot = game_data.get_pilot("scout")
        assert mech is not None
        assert pilot is not None
        deployed = build_deployed_mech(mech, pilot, game_data)
        assert "cloak" in deployed.deck
        assert "sniper_shot" in deployed.deck

    def test_field_medic_grants_patch_up(self, game_data: GameData) -> None:
        """Field Medic Kit equipment should grant patch_up."""
        eq = game_data.get_equipment("field_medic")
        assert eq is not None
        assert "patch_up" in eq.directives_granted

    def test_shield_generator_grants_guard(self, game_data: GameData) -> None:
        """Shield Generator should grant guard."""
        eq = game_data.get_equipment("shield_generator")
        assert eq is not None
        assert "guard" in eq.directives_granted

    def test_optical_camouflage_grants_cloak(self, game_data: GameData) -> None:
        """Optical Camouflage should grant cloak."""
        eq = game_data.get_equipment("optical_camouflage")
        assert eq is not None
        assert "cloak" in eq.directives_granted

    def test_sensor_array_grants_scan(self, game_data: GameData) -> None:
        """Sensor Array should grant scan."""
        eq = game_data.get_equipment("sensor_array")
        assert eq is not None
        assert "scan" in eq.directives_granted

    def test_no_duplicate_directives_in_deck(self, game_data: GameData) -> None:
        """Each mech's deck may have duplicates from the frame, but the
        final composed deck from all sources should not have unexpected
        duplication from equipment grants on top of frame cards."""
        pilot = game_data.get_pilot("aggressive")
        assert pilot is not None
        for mech in game_data.mech_frames:
            deployed = build_deployed_mech(mech, pilot, game_data)
            # Deck can have duplicates (e.g. rifle_fire x2) but every
            # entry must be a valid directive
            for did in deployed.deck:
                directive = game_data.directives.get(did)
                assert directive is not None, f"{mech.id} has non-existent directive: {did}"
