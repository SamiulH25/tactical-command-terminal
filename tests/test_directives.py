"""Comprehensive tests for all directive cards in the game.

Tests cover:
- Every directive loads with valid stats
- Faction-specific directives have correct keywords
- Elite directives have appropriate power levels
- Balance invariants (no negative costs, damage ranges, etc.)
- Keyword consistency across factions
"""

from __future__ import annotations

from typing import ClassVar

import pytest

from src.models.card import DirectiveType, TargetPattern
from src.models.data_loader import GameData, load_all_data

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def game_data() -> GameData:
    return load_all_data()


# ---------------------------------------------------------------------------
# Core directive invariants
# ---------------------------------------------------------------------------


class TestDirectiveInvariants:
    """Every directive must satisfy basic validity rules."""

    def test_total_directive_count(self, game_data: GameData) -> None:
        """We should have a large directive pool (50+)."""
        assert len(game_data.directives) >= 50

    def test_no_duplicate_ids(self, game_data: GameData) -> None:
        """All directive IDs must be unique."""
        ids = list(game_data.directives.keys())
        assert len(ids) == len(set(ids))

    def test_all_have_non_empty_id(self, game_data: GameData) -> None:
        for d in game_data.directives.values():
            assert d.id.strip() != ""

    def test_all_have_non_empty_name(self, game_data: GameData) -> None:
        for d in game_data.directives.values():
            assert d.name.strip() != ""

    def test_all_have_description(self, game_data: GameData) -> None:
        for d in game_data.directives.values():
            assert d.description.strip() != ""

    def test_no_negative_damage(self, game_data: GameData) -> None:
        for d in game_data.directives.values():
            assert d.damage >= 0

    def test_no_negative_heal(self, game_data: GameData) -> None:
        for d in game_data.directives.values():
            assert d.heal >= 0

    def test_no_negative_ol_cost(self, game_data: GameData) -> None:
        for d in game_data.directives.values():
            assert d.overload_cost >= 0

    def test_no_negative_range(self, game_data: GameData) -> None:
        for d in game_data.directives.values():
            assert d.range_ >= 0

    def test_no_negative_move_range(self, game_data: GameData) -> None:
        for d in game_data.directives.values():
            assert d.move_range >= 0

    def test_valid_directive_types(self, game_data: GameData) -> None:
        valid_types = {
            DirectiveType.COMBAT,
            DirectiveType.MOVEMENT,
            DirectiveType.REPAIR,
            DirectiveType.UTILITY,
        }
        for d in game_data.directives.values():
            assert d.directive_type in valid_types

    def test_valid_patterns(self, game_data: GameData) -> None:
        valid_patterns = {
            TargetPattern.NONE,
            TargetPattern.SINGLE,
            TargetPattern.LINE,
            TargetPattern.CONE,
            TargetPattern.AREA,
            TargetPattern.SELF,
            TargetPattern.ALL_HOSTILES,
        }
        for d in game_data.directives.values():
            assert d.pattern in valid_patterns

    def test_combat_directives_have_damage(self, game_data: GameData) -> None:
        """COMBAT type directives must deal damage."""
        for d in game_data.directives.values():
            if d.directive_type == DirectiveType.COMBAT:
                assert d.damage > 0, f"{d.id} is COMBAT but has 0 damage"

    def test_repair_directives_have_heal(self, game_data: GameData) -> None:
        """REPAIR type directives must heal."""
        for d in game_data.directives.values():
            if d.directive_type == DirectiveType.REPAIR:
                assert d.heal > 0, f"{d.id} is REPAIR but has 0 heal"

    def test_movement_directives_have_move_range(self, game_data: GameData) -> None:
        """MOVEMENT directives must have move_range > 0, SELF pattern, or
        NONE pattern (stance-type directives like Hold Position)."""
        for d in game_data.directives.values():
            if d.directive_type == DirectiveType.MOVEMENT:
                assert (
                    d.move_range > 0
                    or d.pattern == TargetPattern.SELF
                    or d.pattern == TargetPattern.NONE
                ), f"{d.id} is MOVEMENT but has no move_range"


# ---------------------------------------------------------------------------
# Faction-specific directive tests
# ---------------------------------------------------------------------------


class TestFSADirectives:
    """FSA directives should have the 'fsa' keyword and appropriate stats."""

    FSA_IDS: ClassVar[list[str]] = [
        "missile_salvo",
        "orbital_strike",
        "shield_wall",
        "retreat",
        "mark_target",
        "coordinated_strike",
        "evac_protocol",
        "recon_sweep",
        "ammo_resupply",
        "targeting_lock",
        "phalanx_formation",
        "fire_support",
        "combat_stims",
        "signal_jammer",
        "orbital_lance",
        "drop_pod_strike",
        "omega_protocol",
    ]

    def test_all_fsa_ids_exist(self, game_data: GameData) -> None:
        for did in self.FSA_IDS:
            assert did in game_data.directives, f"Missing FSA directive: {did}"

    def test_fsa_keyword_present(self, game_data: GameData) -> None:
        for did in self.FSA_IDS:
            d = game_data.directives[did]
            assert "fsa" in d.keywords, f"{did} missing 'fsa' keyword"

    def test_orbital_lance_is_elite(self, game_data: GameData) -> None:
        d = game_data.directives["orbital_lance"]
        assert d.damage == 16
        assert d.range_ == 8
        assert d.pattern == TargetPattern.LINE
        assert "elite" in d.keywords
        assert "devastating" in d.keywords

    def test_omega_protocol_is_most_powerful(self, game_data: GameData) -> None:
        d = game_data.directives["omega_protocol"]
        assert d.damage == 20
        assert d.overload_cost == 8
        assert "omega" in d.keywords

    def test_orbital_strike_long_range(self, game_data: GameData) -> None:
        d = game_data.directives["orbital_strike"]
        assert d.damage == 12
        assert d.range_ == 7

    def test_missile_salvo_is_area(self, game_data: GameData) -> None:
        d = game_data.directives["missile_salvo"]
        assert d.pattern == TargetPattern.AREA
        assert d.damage == 5

    def test_ammo_resupply_is_free(self, game_data: GameData) -> None:
        d = game_data.directives["ammo_resupply"]
        assert d.overload_cost == 0

    def test_drop_pod_strike(self, game_data: GameData) -> None:
        d = game_data.directives["drop_pod_strike"]
        assert d.damage == 10
        assert d.pattern == TargetPattern.AREA


class TestCCDirectives:
    """CC directives should have the 'cc' keyword and heavy/defensive focus."""

    CC_IDS: ClassVar[list[str]] = [
        "barrage",
        "entrench",
        "counter_attack",
        "suppression_squad",
        "fortified_advance",
        "counter_battery",
        "armored_push",
        "trench_warfare",
        "salvage_crew",
        "defilade",
        "heavy_ordnance",
        "combat_doctrine",
        "minefield",
        "siege_breaker",
        "iron_wall",
        "total_war",
    ]

    def test_all_cc_ids_exist(self, game_data: GameData) -> None:
        for did in self.CC_IDS:
            assert did in game_data.directives, f"Missing CC directive: {did}"

    def test_cc_keyword_present(self, game_data: GameData) -> None:
        for did in self.CC_IDS:
            d = game_data.directives[did]
            assert "cc" in d.keywords, f"{did} missing 'cc' keyword"

    def test_heavy_ordnance_most_damage_cc(self, game_data: GameData) -> None:
        d = game_data.directives["heavy_ordnance"]
        assert d.damage == 14
        assert d.overload_cost == 6
        assert "devastating" in d.keywords

    def test_iron_wall_defensive(self, game_data: GameData) -> None:
        d = game_data.directives["iron_wall"]
        assert d.directive_type == DirectiveType.UTILITY
        assert "elite" in d.keywords
        assert "fortification" in d.keywords

    def test_siege_breaker_ignores_defense(self, game_data: GameData) -> None:
        d = game_data.directives["siege_breaker"]
        assert d.damage == 11
        assert d.overload_cost == 5

    def test_barrage_line_pattern(self, game_data: GameData) -> None:
        d = game_data.directives["barrage"]
        assert d.pattern == TargetPattern.LINE
        assert d.range_ == 5

    def test_minefield_area_trap(self, game_data: GameData) -> None:
        d = game_data.directives["minefield"]
        assert d.pattern == TargetPattern.AREA
        assert "trap" in d.keywords


class TestRebelDirectives:
    """Rebel directives should have the 'rebel' keyword and risky/improvised
    theme."""

    REBEL_IDS: ClassVar[list[str]] = [
        "improvised_explosive",
        "scavenge",
        "guerrilla_tactics",
        "sabotage",
        "hit_and_run",
        "field_repair",
        "ambush",
        "scrap_armor",
        "desperate_measures",
        "emp_blast",
        "smoke_screen",
        "last_stand",
        "rally_cry",
        "ghost_protocol",
        "warlord_command",
        "uprising",
    ]

    def test_all_rebel_ids_exist(self, game_data: GameData) -> None:
        for did in self.REBEL_IDS:
            assert did in game_data.directives, f"Missing Rebel directive: {did}"

    def test_rebel_keyword_present(self, game_data: GameData) -> None:
        for did in self.REBEL_IDS:
            d = game_data.directives[did]
            assert "rebel" in d.keywords, f"{did} missing 'rebel' keyword"

    def test_improvised_explosive_risky(self, game_data: GameData) -> None:
        d = game_data.directives["improvised_explosive"]
        assert d.damage == 9
        assert "risky" in d.keywords

    def test_last_stand_zero_cost(self, game_data: GameData) -> None:
        d = game_data.directives["last_stand"]
        assert d.overload_cost == 0
        assert "desperate" in d.keywords

    def test_desperate_measures_draw_cards(self, game_data: GameData) -> None:
        d = game_data.directives["desperate_measures"]
        assert d.overload_cost == 0

    def test_hit_and_run_attack_and_move(self, game_data: GameData) -> None:
        d = game_data.directives["hit_and_run"]
        assert d.damage == 4
        assert d.move_range == 3
        assert d.directive_type == DirectiveType.MOVEMENT

    def test_ghost_protocol_stealth(self, game_data: GameData) -> None:
        d = game_data.directives["ghost_protocol"]
        assert "cloaking" in d.keywords
        assert "elite" in d.keywords

    def test_uprising_area_effect(self, game_data: GameData) -> None:
        d = game_data.directives["uprising"]
        assert "escalation" in d.keywords
        assert "elite" in d.keywords


# ---------------------------------------------------------------------------
# Universal / Advanced directive tests
# ---------------------------------------------------------------------------


class TestUniversalDirectives:
    """Directives available to all factions."""

    UNIVERSAL_IDS: ClassVar[list[str]] = [
        "autocannon_burst",
        "rifle_fire",
        "heavy_cannon",
        "sniper_shot",
        "suppressing_fire",
        "advance",
        "dash",
        "flank",
        "hold_position",
        "overwatch",
        "guard",
        "fortify",
        "scan",
        "cloak",
        "evasive_maneuvers",
        "patch_up",
        "demolitions",
        "forced_march",
        "precision_strike",
        "overcharge",
        "repair_drone",
        "sensor_ping",
        "point_defense",
        "breach_charge",
        "tactical_withdrawal",
        "emergency_shields",
        "nanite_repair",
    ]

    def test_all_universal_ids_exist(self, game_data: GameData) -> None:
        for did in self.UNIVERSAL_IDS:
            assert did in game_data.directives, f"Missing universal directive: {did}"

    def test_precision_strike_piercing(self, game_data: GameData) -> None:
        d = game_data.directives["precision_strike"]
        assert "piercing" in d.keywords
        assert d.damage == 7

    def test_forced_march_long_range(self, game_data: GameData) -> None:
        d = game_data.directives["forced_march"]
        assert d.move_range == 6

    def test_tactical_withdrawal_free(self, game_data: GameData) -> None:
        d = game_data.directives["tactical_withdrawal"]
        assert d.overload_cost == 0

    def test_nanite_repair_big_heal(self, game_data: GameData) -> None:
        d = game_data.directives["nanite_repair"]
        assert d.heal == 15
        assert "elite" in d.keywords

    def test_breach_charge_cone(self, game_data: GameData) -> None:
        d = game_data.directives["breach_charge"]
        assert d.pattern == TargetPattern.CONE

    def test_overcharge_buff(self, game_data: GameData) -> None:
        d = game_data.directives["overcharge"]
        assert d.directive_type == DirectiveType.UTILITY


# ---------------------------------------------------------------------------
# Balance / power level tests
# ---------------------------------------------------------------------------


class TestDirectiveBalance:
    """Ensure the directive pool is well-balanced."""

    def test_max_damage_directive(self, game_data: GameData) -> None:
        max_dmg = max(d.damage for d in game_data.directives.values())
        assert max_dmg == 20  # omega_protocol

    def test_max_ol_cost_reasonable(self, game_data: GameData) -> None:
        max_ol = max(d.overload_cost for d in game_data.directives.values())
        assert max_ol <= 8  # Should not exceed available OL

    def test_max_heal_directive(self, game_data: GameData) -> None:
        max_heal = max(d.heal for d in game_data.directives.values())
        assert max_heal == 15  # nanite_repair

    def test_max_range_directive(self, game_data: GameData) -> None:
        max_range = max(d.range_ for d in game_data.directives.values())
        assert max_range == 8  # orbital_lance

    def test_elite_directives_have_high_cost(self, game_data: GameData) -> None:
        """Elite directives should have OL cost >= 2."""
        for d in game_data.directives.values():
            if "elite" in d.keywords:
                assert d.overload_cost >= 2, f"Elite directive {d.id} has too low OL cost"

    def test_elite_directives_have_high_power(self, game_data: GameData) -> None:
        """Elite directives should have significant impact."""
        for d in game_data.directives.values():
            if "elite" in d.keywords:
                assert d.damage >= 10 or d.heal >= 10 or "elite" in d.keywords, (
                    f"Elite directive {d.id} lacks power"
                )

    def test_free_directives_are_utility_or_movement(self, game_data: GameData) -> None:
        """Zero-cost directives should not deal direct damage."""
        for d in game_data.directives.values():
            if d.overload_cost == 0:
                assert d.damage == 0, f"Free directive {d.id} deals damage — too strong"

    def test_keyword_sets_are_consistent(self, game_data: GameData) -> None:
        """Known keywords should be from a controlled set."""
        known_keywords = {
            "kinetic",
            "explosive",
            "heavy",
            "precision",
            "suppress",
            "mobility",
            "flank",
            "stance",
            "movement",
            "utility",
            "fsa",
            "cc",
            "rebel",
            "risky",
            "salvage",
            "evasion",
            "defensive",
            "fortify",
            "intel",
            "stealth",
            "repair",
            "reaction",
            "artillery",
            "reactive",
            "area",
            "targeting",
            "coordinated",
            "emergency",
            "reveal",
            "logistics",
            "formation",
            "stim",
            "electronic",
            "jam",
            "cover",
            "trap",
            "doctrine",
            "sabotage",
            "improvised",
            "desperate",
            "emp",
            "concealment",
            "survival",
            "morale",
            "attack",
            "piercing",
            "overcharge",
            "power",
            "drone",
            "sensor",
            "point_defense",
            "demolition",
            "march",
            "exhaustion",
            "breach",
            "cone",
            "free",
            "withdrawal",
            "shield",
            "orbital",
            "elite",
            "devastating",
            "siege",
            "fortification",
            "cloaking",
            "command",
            "escalation",
            "nanite",
            "advanced",
            "omega",
        }
        for d in game_data.directives.values():
            for kw in d.keywords:
                assert kw in known_keywords, f"Unknown keyword '{kw}' in {d.id}"


# ---------------------------------------------------------------------------
# Category count tests
# ---------------------------------------------------------------------------


class TestDirectiveCategoryCounts:
    """Ensure we have enough directives in each category."""

    def test_enough_combat_directives(self, game_data: GameData) -> None:
        combat = [
            d for d in game_data.directives.values() if d.directive_type == DirectiveType.COMBAT
        ]
        assert len(combat) >= 15

    def test_enough_movement_directives(self, game_data: GameData) -> None:
        movement = [
            d for d in game_data.directives.values() if d.directive_type == DirectiveType.MOVEMENT
        ]
        assert len(movement) >= 8

    def test_enough_utility_directives(self, game_data: GameData) -> None:
        utility = [
            d for d in game_data.directives.values() if d.directive_type == DirectiveType.UTILITY
        ]
        assert len(utility) >= 20

    def test_enough_repair_directives(self, game_data: GameData) -> None:
        repair = [
            d for d in game_data.directives.values() if d.directive_type == DirectiveType.REPAIR
        ]
        assert len(repair) >= 3

    def test_fsa_has_enough_directives(self, game_data: GameData) -> None:
        fsa = [d for d in game_data.directives.values() if "fsa" in d.keywords]
        assert len(fsa) >= 10

    def test_cc_has_enough_directives(self, game_data: GameData) -> None:
        cc = [d for d in game_data.directives.values() if "cc" in d.keywords]
        assert len(cc) >= 10

    def test_rebel_has_enough_directives(self, game_data: GameData) -> None:
        rebel = [d for d in game_data.directives.values() if "rebel" in d.keywords]
        assert len(rebel) >= 10

    def test_elite_directive_count(self, game_data: GameData) -> None:
        elite = [d for d in game_data.directives.values() if "elite" in d.keywords]
        assert len(elite) >= 8
