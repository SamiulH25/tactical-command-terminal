"""Tests for the combat comms (flavour text) system."""

from src.models.campaign import Campaign
from src.systems.combat_comms import CombatComms


def _campaign() -> Campaign:
    c = Campaign()
    c.current_floor = 3
    return c


class TestCombatComms:
    """Verify combat comms message selection."""

    def test_engagement_start_message(self) -> None:
        """Should return a timestamped message for engagement_start."""
        comms = CombatComms(_campaign())
        msg = comms.get_message("engagement_start")
        assert msg is not None
        # Message now has timestamp prefix: "HH:MM:SS // > ..."
        assert " // >" in msg

    def test_damage_taken_low_hp(self) -> None:
        """Low damage should give a minor message."""
        comms = CombatComms(_campaign())
        msg = comms.get_message("damage_taken", hp_ratio=0.8)
        assert msg is not None
        assert "CRITICAL" not in msg

    def test_damage_taken_high_hp(self) -> None:
        """High damage should give a critical message."""
        comms = CombatComms(_campaign())
        msg = comms.get_message("damage_taken", hp_ratio=0.1)
        assert msg is not None
        assert "CRITICAL" in msg or "SEVERE" in msg or "ALARM" in msg

    def test_damage_taken_med_returns_message(self) -> None:
        """Medium damage should return valid messages."""
        comms = CombatComms(_campaign())
        msg = comms.get_message("damage_taken", hp_ratio=0.42)
        assert msg is not None
        # Messages should not contain {hp} literally (should be replaced)
        assert "{hp}" not in msg

    def test_enemy_hit_message(self) -> None:
        """Should return a timestamped message."""
        comms = CombatComms(_campaign())
        msg = comms.get_message("enemy_hit")
        assert msg is not None
        assert " // >" in msg

    def test_enemy_destroyed_message(self) -> None:
        """Should return a timestamped message."""
        comms = CombatComms(_campaign())
        msg = comms.get_message("enemy_destroyed")
        assert msg is not None
        assert " // >" in msg

    def test_enemy_low_hp_message(self) -> None:
        """Should return a timestamped message."""
        comms = CombatComms(_campaign())
        msg = comms.get_message("enemy_low_hp")
        assert msg is not None

    def test_player_low_hp_message(self) -> None:
        """Should return a timestamped message."""
        comms = CombatComms(_campaign())
        msg = comms.get_message("player_low_hp")
        assert msg is not None
        assert "ALERT" in msg or "WARNING" in msg or "CRITICAL" in msg

    def test_ol_warning_message(self) -> None:
        """Should return a timestamped message."""
        comms = CombatComms(_campaign())
        msg = comms.get_message("ol_warning")
        assert msg is not None

    def test_enemy_turn_message(self) -> None:
        """Should return a timestamped message."""
        comms = CombatComms(_campaign())
        msg = comms.get_message("enemy_turn")
        assert msg is not None

    def test_ambient_message(self) -> None:
        """Should return timestamped ambient comms."""
        comms = CombatComms(_campaign())
        msg = comms.get_message("ambient")
        assert msg is not None

    def test_no_duplicate_messages(self) -> None:
        """Should not repeat the same message consecutively."""
        comms = CombatComms(_campaign())
        seen: set[str] = set()
        for _ in range(100):
            msg = comms.get_message("ambient")
            if msg is not None:
                assert msg not in seen, f"Duplicate message: {msg}"
                seen.add(msg)

    def test_faction_specific_comms(self) -> None:
        """Friendly rebel reputation should give rebel comms on 5th call."""
        c = _campaign()
        c.adjust_reputation("rebel", 30)  # Friendly
        comms = CombatComms(c)
        # Skip 4 calls (counter goes 1,2,3,4) — 5th call should hit faction check
        for _ in range(4):
            comms.get_message("ambient")
        msg = comms.get_message("ambient")  # counter = 5, triggers faction check
        assert msg is not None
        assert "Rebel" in msg or "Coordinator" in msg

    def test_start_combat_clears_seen(self) -> None:
        """start_combat should clear the seen messages set."""
        comms = CombatComms(_campaign())
        # Consume some messages
        for _ in range(10):
            comms.get_message("ambient")
        # Start new combat
        from src.models.grid import CombatGrid, GridCell
        from src.systems.combat import CombatState

        cells = [[GridCell(col=c, row=r) for c in range(10)] for r in range(10)]
        grid = CombatGrid(width=10, height=10, cells=cells)
        state = CombatState(grid=grid)
        comms.start_combat(state, 5)
        # Should be able to get messages again
        msg = comms.get_message("engagement_start")
        assert msg is not None

    def test_unknown_event_returns_none(self) -> None:
        """Unknown event types should return None."""
        comms = CombatComms(_campaign())
        assert comms.get_message("nonexistent_event") is None
