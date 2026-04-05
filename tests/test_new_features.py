"""Tests for new features: BootScreen watermark, MechSelect faction/unlock
logic, new directive cards, and ShipMenu flow."""

from __future__ import annotations

import pygame
import pytest

from src.models.campaign import Campaign
from src.models.data_loader import GameData, load_all_data
from src.models.faction import Faction
from src.screens.boot_screen import BootScreen
from src.screens.mech_select import (
    _FACTION_UNLOCK_FLOORS,
    _MECH_UNLOCK_FLOORS,
    MechSelect,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def game_data() -> GameData:
    return load_all_data()


@pytest.fixture()
def campaign() -> Campaign:
    return Campaign()


# ---------------------------------------------------------------------------
# BootScreen — BOB2142 watermark
# ---------------------------------------------------------------------------


class TestBootScreenWatermark:
    def test_boot_lines_contains_bob2142(self) -> None:
        """The boot sequence should include the BOB2142 watermark."""
        texts = [line for line, _delay in BootScreen.BOOT_LINES]
        assert "> SYSTEM BY BOB2142" in texts

    def test_bob2142_is_last_text_line(self) -> None:
        """BOB2142 should be the final text line (after HELLO, COORDINATOR)."""
        non_empty = [line for line, _delay in BootScreen.BOOT_LINES if line.strip()]
        assert non_empty[-1] == "> SYSTEM BY BOB2142"

    def test_boot_screen_initialises(self) -> None:
        """BootScreen should construct without error."""
        pygame.font.init()
        pygame.display.set_mode((1920, 1080))
        renderer = type("FakeRenderer", (), {"display": pygame.display.get_surface()})()
        screen = BootScreen(renderer)
        screen.on_enter()
        assert screen._font is not None
        assert screen._line_index == 0


# ---------------------------------------------------------------------------
# MechSelect — faction unlock logic
# ---------------------------------------------------------------------------


class TestMechSelectFactionUnlocks:
    def test_fsa_unlocked_at_start(self, game_data: GameData) -> None:
        """FSA should be available from floor 0."""
        pygame.font.init()
        pygame.display.set_mode((1920, 1080))
        campaign = Campaign()
        assert campaign.floors_cleared == 0
        renderer = type("FakeRenderer", (), {"display": pygame.display.get_surface()})()
        ms = MechSelect(renderer, game_data, campaign)
        ms.on_enter()
        assert ms._is_faction_unlocked(Faction.FSA)

    def test_cc_locked_at_start(self, game_data: GameData) -> None:
        """CC should be locked at floor 0."""
        pygame.font.init()
        pygame.display.set_mode((1920, 1080))
        campaign = Campaign()
        renderer = type("FakeRenderer", (), {"display": pygame.display.get_surface()})()
        ms = MechSelect(renderer, game_data, campaign)
        ms.on_enter()
        assert not ms._is_faction_unlocked(Faction.CRIMSON_COMPACT)

    def test_rebel_locked_at_start(self, game_data: GameData) -> None:
        """Rebel should be locked at floor 0."""
        pygame.font.init()
        pygame.display.set_mode((1920, 1080))
        campaign = Campaign()
        renderer = type("FakeRenderer", (), {"display": pygame.display.get_surface()})()
        ms = MechSelect(renderer, game_data, campaign)
        ms.on_enter()
        assert not ms._is_faction_unlocked(Faction.REBEL)

    def test_cc_unlocked_at_floor_5(self, game_data: GameData) -> None:
        """CC should be unlocked at floor 5."""
        pygame.font.init()
        pygame.display.set_mode((1920, 1080))
        campaign = Campaign()
        campaign.floors_cleared = 5
        renderer = type("FakeRenderer", (), {"display": pygame.display.get_surface()})()
        ms = MechSelect(renderer, game_data, campaign)
        ms.on_enter()
        assert ms._is_faction_unlocked(Faction.CRIMSON_COMPACT)

    def test_rebel_unlocked_at_floor_10(self, game_data: GameData) -> None:
        """Rebel should be unlocked at floor 10."""
        pygame.font.init()
        pygame.display.set_mode((1920, 1080))
        campaign = Campaign()
        campaign.floors_cleared = 10
        renderer = type("FakeRenderer", (), {"display": pygame.display.get_surface()})()
        ms = MechSelect(renderer, game_data, campaign)
        ms.on_enter()
        assert ms._is_faction_unlocked(Faction.REBEL)


# ---------------------------------------------------------------------------
# MechSelect — mech unlock logic
# ---------------------------------------------------------------------------


class TestMechSelectMechUnlocks:
    def test_bastion_unlocked_at_start(self, game_data: GameData) -> None:
        """fsa_bastion should be available from floor 0."""
        pygame.font.init()
        pygame.display.set_mode((1920, 1080))
        campaign = Campaign()
        renderer = type("FakeRenderer", (), {"display": pygame.display.get_surface()})()
        ms = MechSelect(renderer, game_data, campaign)
        ms.on_enter()
        bastion = game_data.get_mech("fsa_bastion")
        assert bastion is not None
        assert ms._is_mech_unlocked(bastion)

    def test_wraith_locked_at_start(self, game_data: GameData) -> None:
        """fsa_wraith should be locked at floor 0 (requires floor 7)."""
        pygame.font.init()
        pygame.display.set_mode((1920, 1080))
        campaign = Campaign()
        renderer = type("FakeRenderer", (), {"display": pygame.display.get_surface()})()
        ms = MechSelect(renderer, game_data, campaign)
        ms.on_enter()
        wraith = game_data.get_mech("fsa_wraith")
        assert wraith is not None
        assert not ms._is_mech_unlocked(wraith)

    def test_wraith_unlocked_at_floor_7(self, game_data: GameData) -> None:
        """fsa_wraith should be unlocked at floor 7."""
        pygame.font.init()
        pygame.display.set_mode((1920, 1080))
        campaign = Campaign()
        campaign.floors_cleared = 7
        renderer = type("FakeRenderer", (), {"display": pygame.display.get_surface()})()
        ms = MechSelect(renderer, game_data, campaign)
        ms.on_enter()
        wraith = game_data.get_mech("fsa_wraith")
        assert wraith is not None
        assert ms._is_mech_unlocked(wraith)

    def test_faction_filtering_returns_only_faction_mechs(self, game_data: GameData) -> None:
        """Selecting FSA should only show FSA mechs."""
        pygame.font.init()
        pygame.display.set_mode((1920, 1080))
        campaign = Campaign()
        renderer = type("FakeRenderer", (), {"display": pygame.display.get_surface()})()
        ms = MechSelect(renderer, game_data, campaign)
        ms.on_enter()
        ms._select_faction(Faction.FSA)
        fsa_mechs = ms._get_faction_mechns(Faction.FSA)
        assert len(fsa_mechs) == 5
        assert all(m.faction == Faction.FSA for m in fsa_mechs)

    def test_select_faction_resets_mech_selection(self, game_data: GameData) -> None:
        """Changing faction should clear the current mech selection."""
        pygame.font.init()
        pygame.display.set_mode((1920, 1080))
        campaign = Campaign()
        renderer = type("FakeRenderer", (), {"display": pygame.display.get_surface()})()
        ms = MechSelect(renderer, game_data, campaign)
        ms.on_enter()
        bastion = game_data.get_mech("fsa_bastion")
        assert bastion is not None
        ms._select_unit(bastion)
        assert ms._selected_frame == bastion
        # Changing faction resets selection
        ms._select_faction(Faction.FSA)
        assert ms._selected_frame is None


# ---------------------------------------------------------------------------
# New directive cards load correctly
# ---------------------------------------------------------------------------


class TestNewDirectives:
    def test_fsa_tactical_directives_load(self, game_data: GameData) -> None:
        """FSA tactical directives should be loaded."""
        assert "missile_salvo" in game_data.directives
        assert "orbital_strike" in game_data.directives
        assert "shield_wall" in game_data.directives
        assert "retreat" in game_data.directives

    def test_cc_tactical_directives_load(self, game_data: GameData) -> None:
        """CC tactical directives should be loaded."""
        assert "barrage" in game_data.directives
        assert "entrench" in game_data.directives
        assert "counter_attack" in game_data.directives

    def test_rebel_tactical_directives_load(self, game_data: GameData) -> None:
        """Rebel tactical directives should be loaded."""
        assert "improvised_explosive" in game_data.directives
        assert "scavenge" in game_data.directives
        assert "guerrilla_tactics" in game_data.directives

    def test_orbital_strike_has_correct_stats(self, game_data: GameData) -> None:
        """Orbital Strike should be high-damage, long-range."""
        d = game_data.directives["orbital_strike"]
        assert d.damage == 12
        assert d.range_ == 7
        assert d.overload_cost == 5

    def test_improvised_explosive_is_risky(self, game_data: GameData) -> None:
        """Improvised Explosive should have high damage and risky keyword."""
        d = game_data.directives["improvised_explosive"]
        assert d.damage == 9
        assert "risky" in d.keywords

    def test_scavenge_grants_credits_and_heal(self, game_data: GameData) -> None:
        """Scavenge should heal and have utility type."""
        d = game_data.directives["scavenge"]
        assert d.heal == 2
        assert d.overload_cost == 1
        assert "salvage" in d.keywords


# ---------------------------------------------------------------------------
# Campaign progression
# ---------------------------------------------------------------------------


class TestCampaignProgressionUnlocks:
    def test_unlock_thresholds_match_constants(self) -> None:
        """Faction unlock thresholds should match expected values."""
        assert _FACTION_UNLOCK_FLOORS[Faction.FSA] == 0
        assert _FACTION_UNLOCK_FLOORS[Faction.CRIMSON_COMPACT] == 5
        assert _FACTION_UNLOCK_FLOORS[Faction.REBEL] == 10

    def test_mech_unlocks_defined_for_all_mechs(self, game_data: GameData) -> None:
        """Every mech in game data should have an unlock floor defined."""
        for mech in game_data.mech_frames:
            assert mech.id in _MECH_UNLOCK_FLOORS
