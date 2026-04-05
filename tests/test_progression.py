"""Tests for the floor progression and campaign flow systems."""

import pytest

from src.models.campaign import Campaign
from src.models.encounter import EncounterType
from src.systems.progression import FloorProgression, _default_floor

# ---------------------------------------------------------------------------
# FloorTemplate / default floor
# ---------------------------------------------------------------------------


class TestDefaultFloor:
    """Verify default floor generation."""

    def test_floor_1_has_combat(self) -> None:
        """Floor 1 should have a combat encounter."""
        ft = _default_floor(1)
        assert ft.floor_number == 1
        assert ft.combat.encounter_type == EncounterType.COMBAT

    def test_floor_has_rest(self) -> None:
        """Every floor should have a rest encounter."""
        ft = _default_floor(10)
        assert ft.optional_b.encounter_type == EncounterType.REST

    def test_floor_3_has_merchant(self) -> None:
        """Floor divisible by 3 should have a merchant encounter."""
        ft = _default_floor(3)
        assert ft.optional_a.encounter_type == EncounterType.MERCHANT

    def test_floor_6_has_merchant(self) -> None:
        """Floor 6 should also have merchant."""
        ft = _default_floor(6)
        assert ft.optional_a.encounter_type == EncounterType.MERCHANT

    def test_floor_4_has_event(self) -> None:
        """Floor not divisible by 3 should have an event."""
        ft = _default_floor(4)
        assert ft.optional_a.encounter_type == EncounterType.EVENT

    def test_narrative_for_known_floor(self) -> None:
        """Floor 1 should have specific narrative text."""
        ft = _default_floor(1)
        assert "INSERTION" in ft.narrative_intro

    def test_narrative_for_unknown_floor(self) -> None:
        """Floor 3 should have specific narrative text."""
        ft = _default_floor(3)
        assert "Sector sweep" in ft.narrative_intro
        assert "Enemy adapting" in ft.narrative_outro


# ---------------------------------------------------------------------------
# FloorProgression
# ---------------------------------------------------------------------------


class TestFloorProgression:
    """Verify floor progression manager."""

    def _make(self) -> FloorProgression:
        return FloorProgression(Campaign())

    def test_get_floor_pre_deployment(self) -> None:
        """Floor 0 should return None."""
        prog = self._make()
        assert prog.get_floor_template() is None

    def test_get_floor_after_advance(self) -> None:
        """After advancing, should return the floor template."""
        prog = self._make()
        prog.campaign.current_floor = 1
        template = prog.get_floor_template()
        assert template is not None
        assert template.floor_number == 1

    def test_get_encounters_returns_3(self) -> None:
        """Each floor should have 3 encounters."""
        prog = self._make()
        prog.campaign.current_floor = 5
        encounters = prog.get_encounters()
        assert encounters is not None
        assert len(encounters) == 3

    def test_advance_floor(self) -> None:
        """Advancing should increment floor number."""
        prog = self._make()
        prog.campaign.current_floor = 1
        new_floor = prog.advance()
        assert new_floor == 2
        assert prog.campaign.current_floor == 2

    def test_advance_to_25_then_error(self) -> None:
        """Advancing beyond floor 25 should raise ValueError."""
        prog = self._make()
        for _ in range(25):
            prog.campaign.current_floor = max(0, prog.campaign.current_floor)
            try:
                prog.advance()
            except ValueError:
                break
        prog.campaign.current_floor = 25
        with pytest.raises(ValueError, match="final floor"):
            prog.advance()

    def test_get_transition_text_format(self) -> None:
        """Transition text should include standard lines."""
        prog = self._make()
        text = prog.get_transition_text(1, 2)
        assert "UPLOADING SECTOR DATA" in text
        assert "SECTOR 02 LOADED" in text
        assert "SIGNAL RE-ACQUIRED" in text

    def test_transition_text_includes_intro(self) -> None:
        """Floor 1 transition should include intro narrative."""
        prog = self._make()
        text = prog.get_transition_text(0, 1)
        assert "INSERTION" in text

    def test_get_outpost_name(self) -> None:
        """Outpost name should match campaign."""
        prog = self._make()
        prog.campaign.current_floor = 1
        assert prog.get_outpost_name() == "Outpost Alpha"

    def test_floors_cleared_updated(self) -> None:
        """floors_cleared should update after advancing."""
        prog = self._make()
        prog.campaign.current_floor = 1
        prog.advance()
        assert prog.campaign.floors_cleared == 1

    def test_all_25_templates_exist(self) -> None:
        """All 25 floor templates should be generated."""
        prog = self._make()
        for i in range(1, 26):
            prog.campaign.current_floor = i
            template = prog.get_floor_template()
            assert template is not None
            assert template.floor_number == i
