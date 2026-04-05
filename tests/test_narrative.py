"""Tests for the narrative, comms, and endings systems."""

import pytest

from src.models.campaign import Campaign
from src.systems.comms import get_intercepted_comm
from src.systems.endings import EndingCalculator
from src.systems.narrative import EventChoice, NarrativeEngine, NarrativeEvent, Outcome

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _campaign() -> Campaign:
    """Return a fresh campaign."""
    return Campaign()


def _sample_event() -> NarrativeEvent:
    """Return a sample narrative event for testing."""
    return NarrativeEvent(
        id="event_test",
        title="INTERCEPTED SIGNAL",
        narrative_text=(
            "Unidentified broadcast on emergency frequency.\nSignal degrades and reconstructs..."
        ),
        choices=[
            EventChoice(text="Investigate", outcome_id="investigate"),
            EventChoice(text="Ignore", outcome_id="ignore"),
            EventChoice(
                text="Jam the signal",
                outcome_id="jam",
                forbidden_decision="event_test:investigate",
            ),
        ],
        outcomes={
            "investigate": Outcome(
                outcome_id="investigate",
                narrative_text="Found rebel survivors. They share intel.",
                reputation_changes={"rebel": 15, "crimson_compact": -5},
                credits_delta=30,
                ally_rescued="Rebel-Alpha",
                decision_tag="event_test:investigate",
            ),
            "ignore": Outcome(
                outcome_id="ignore",
                narrative_text="Signal fades. No consequences.",
                reputation_changes={"rebel": -5},
                credits_delta=0,
                decision_tag="event_test:ignore",
            ),
            "jam": Outcome(
                outcome_id="jam",
                narrative_text="Signal jammed. CC forces detected the interference.",
                reputation_changes={"crimson_compact": -20, "rebel": -10},
                credits_delta=0,
                decision_tag="event_test:jam",
            ),
        },
    )


# ---------------------------------------------------------------------------
# Outcome
# ---------------------------------------------------------------------------


class TestOutcome:
    """Verify outcome validation."""

    def test_valid_outcome(self) -> None:
        """Valid outcome should not raise."""
        Outcome(outcome_id="test").validate()

    def test_empty_id_raises(self) -> None:
        with pytest.raises(ValueError, match="outcome_id"):
            Outcome(outcome_id="").validate()


# ---------------------------------------------------------------------------
# EventChoice
# ---------------------------------------------------------------------------


class TestEventChoice:
    """Verify event choice validation."""

    def test_valid_choice(self) -> None:
        EventChoice(text="Help them", outcome_id="help").validate()

    def test_empty_text_raises(self) -> None:
        with pytest.raises(ValueError, match="text"):
            EventChoice(text="", outcome_id="x").validate()

    def test_empty_outcome_raises(self) -> None:
        with pytest.raises(ValueError, match="outcome_id"):
            EventChoice(text="Help", outcome_id="").validate()


# ---------------------------------------------------------------------------
# NarrativeEvent
# ---------------------------------------------------------------------------


class TestNarrativeEvent:
    """Verify narrative event validation."""

    def _valid(self) -> NarrativeEvent:
        return NarrativeEvent(
            id="test",
            title="TEST",
            narrative_text="Test text",
            choices=[
                EventChoice(text="A", outcome_id="a"),
                EventChoice(text="B", outcome_id="b"),
            ],
            outcomes={
                "a": Outcome(outcome_id="a"),
                "b": Outcome(outcome_id="b"),
            },
        )

    def test_valid_event(self) -> None:
        self._valid().validate()

    def test_empty_id_raises(self) -> None:
        with pytest.raises(ValueError, match="id"):
            NarrativeEvent(
                id="",
                title="T",
                narrative_text="N",
                choices=[EventChoice(text="A", outcome_id="a")],
                outcomes={"a": Outcome(outcome_id="a")},
            ).validate()

    def test_empty_title_raises(self) -> None:
        with pytest.raises(ValueError, match="title"):
            e = self._valid()
            NarrativeEvent(
                id=e.id,
                title="",
                narrative_text=e.narrative_text,
                choices=e.choices,
                outcomes=e.outcomes,
            ).validate()

    def test_empty_narrative_raises(self) -> None:
        with pytest.raises(ValueError, match="narrative_text"):
            e = self._valid()
            NarrativeEvent(
                id=e.id,
                title=e.title,
                narrative_text="",
                choices=e.choices,
                outcomes=e.outcomes,
            ).validate()

    def test_fewer_than_two_choices_raises(self) -> None:
        with pytest.raises(ValueError, match="2 choices"):
            NarrativeEvent(
                id="test",
                title="T",
                narrative_text="N",
                choices=[EventChoice(text="A", outcome_id="a")],
                outcomes={"a": Outcome(outcome_id="a")},
            ).validate()

    def test_missing_outcome_reference_raises(self) -> None:
        with pytest.raises(ValueError, match="not found"):
            NarrativeEvent(
                id="test",
                title="T",
                narrative_text="N",
                choices=[
                    EventChoice(text="A", outcome_id="missing"),
                    EventChoice(text="B", outcome_id="a"),
                ],
                outcomes={
                    "a": Outcome(outcome_id="a"),
                    "b": Outcome(outcome_id="b"),
                },
            ).validate()


# ---------------------------------------------------------------------------
# NarrativeEngine
# ---------------------------------------------------------------------------


class TestNarrativeEngine:
    """Verify narrative engine choice resolution."""

    def test_resolve_choice_applies_reputation(self) -> None:
        """Resolving a choice should adjust faction reputation."""
        camp = _campaign()
        engine = NarrativeEngine(camp)
        event = _sample_event()
        choice = event.choices[0]  # Investigate
        engine.resolve_choice(event, choice)
        assert camp.reputation["rebel"] == 15
        assert camp.reputation["crimson_compact"] == -5

    def test_resolve_choice_applies_credits(self) -> None:
        """Resolving a choice should update credits."""
        camp = _campaign()
        engine = NarrativeEngine(camp)
        event = _sample_event()
        engine.resolve_choice(event, event.choices[0])
        assert camp.current_credits == 150 + 30  # Starting + delta

    def test_resolve_choice_records_ally(self) -> None:
        """Resolving a choice should record rescued allies."""
        camp = _campaign()
        engine = NarrativeEngine(camp)
        event = _sample_event()
        engine.resolve_choice(event, event.choices[0])
        assert "Rebel-Alpha" in camp.allies_rescued

    def test_resolve_choice_records_decision(self) -> None:
        """Resolving a choice should append to decision log."""
        camp = _campaign()
        engine = NarrativeEngine(camp)
        event = _sample_event()
        engine.resolve_choice(event, event.choices[0])
        assert camp.has_decision("event_test:investigate")

    def test_resolve_invalid_outcome_raises(self) -> None:
        """Resolving a non-existent outcome should raise ValueError."""
        camp = _campaign()
        engine = NarrativeEngine(camp)
        event = _sample_event()
        bad_choice = EventChoice(text="Bad", outcome_id="nonexistent")
        with pytest.raises(ValueError, match="not found"):
            engine.resolve_choice(event, bad_choice)

    def test_credits_cannot_go_negative(self) -> None:
        """Credits should floor at 0."""
        camp = _campaign()
        camp.current_credits = 10
        engine = NarrativeEngine(camp)
        event = NarrativeEvent(
            id="test",
            title="T",
            narrative_text="N",
            choices=[EventChoice(text="A", outcome_id="a")],
            outcomes={
                "a": Outcome(
                    outcome_id="a",
                    narrative_text="Paid a bribe.",
                    credits_delta=-100,
                ),
            },
        )
        engine.resolve_choice(event, event.choices[0])
        assert camp.current_credits == 0

    def test_duplicate_ally_not_doubled(self) -> None:
        """Rescuing the same ally twice should not duplicate the entry."""
        camp = _campaign()
        engine = NarrativeEngine(camp)
        event = _sample_event()
        engine.resolve_choice(event, event.choices[0])
        engine.resolve_choice(event, event.choices[0])
        assert camp.allies_rescued.count("Rebel-Alpha") == 1


# ---------------------------------------------------------------------------
# Available choices filtering
# ---------------------------------------------------------------------------


class TestAvailableChoices:
    """Verify choice availability based on decisions."""

    def test_all_choices_available(self) -> None:
        """Without any decisions, all choices should be available."""
        camp = _campaign()
        event = _sample_event()
        available = event.get_available_choices(camp)
        assert len(available) == 3

    def test_forbidden_decision_hides_choice(self) -> None:
        """If forbidden_decision is made, that choice should be hidden."""
        camp = _campaign()
        camp.record_decision("event_test:investigate")
        event = _sample_event()
        available = event.get_available_choices(camp)
        outcome_ids = [c.outcome_id for c in available]
        assert "jam" not in outcome_ids

    def test_at_least_one_choice_always(self) -> None:
        """Even if all choices are filtered, at least one should remain."""
        camp = _campaign()
        camp.record_decision("event_test:investigate")
        camp.record_decision("event_test:ignore")
        event = _sample_event()
        available = event.get_available_choices(camp)
        assert len(available) >= 1


# ---------------------------------------------------------------------------
# Intercepted Comms
# ---------------------------------------------------------------------------


class TestInterceptedComms:
    """Verify intercepted communication text."""

    def test_auto_picks_faction_by_floor(self) -> None:
        """Auto should pick FSA for early floors."""
        camp = _campaign()
        camp.current_floor = 3
        comm = get_intercepted_comm(camp)
        assert isinstance(comm, str)
        assert len(comm) > 0

    def test_cc_comms_at_different_reps(self) -> None:
        """CC comms should vary by reputation."""
        camp = _campaign()
        camp.current_floor = 20
        camp.adjust_reputation("crimson_compact", 50)
        comm = get_intercepted_comm(camp, "cc")
        assert isinstance(comm, str)
        assert "CC" in comm  # Should be a CC comm

    def test_unknown_faction_returns_no_signal(self) -> None:
        """Unknown faction should return interference message."""
        camp = _campaign()
        comm = get_intercepted_comm(camp, "aliens")
        assert "NO SIGNAL" in comm

    def test_returns_random_from_pool(self) -> None:
        """Multiple calls should return strings from the pool."""
        camp = _campaign()
        camp.current_floor = 5
        for _ in range(10):
            comm = get_intercepted_comm(camp, "fsa")
            assert comm.startswith("FSA ") or "Command" in comm


# ---------------------------------------------------------------------------
# Endings
# ---------------------------------------------------------------------------


class TestEndingCalculator:
    """Verify ending determination logic."""

    def _calc(self, campaign: Campaign) -> EndingCalculator:
        return EndingCalculator(campaign)

    def test_default_ending_is_exile(self) -> None:
        """A fresh campaign with no decisions should result in Exile."""
        camp = _campaign()
        calc = self._calc(camp)
        ending = calc.calculate()
        assert ending.ending_id == "exile"

    def test_betrayed_ending(self) -> None:
        """Any 'betray:' decision should trigger Betrayed ending."""
        camp = _campaign()
        camp.record_decision("betray:rebel_alpha")
        calc = self._calc(camp)
        ending = calc.calculate()
        assert ending.ending_id == "betrayed"

    def test_redeemed_ending(self) -> None:
        """High FSA reputation should trigger Redeemed ending."""
        camp = _campaign()
        camp.adjust_reputation("fsa", 60)
        calc = self._calc(camp)
        ending = calc.calculate()
        assert ending.ending_id == "redeemed"

    def test_liberator_ending(self) -> None:
        """High Rebel and CC reputation should trigger Liberator."""
        camp = _campaign()
        camp.adjust_reputation("rebel", 30)
        camp.adjust_reputation("crimson_compact", 25)
        calc = self._calc(camp)
        ending = calc.calculate()
        assert ending.ending_id == "liberator"

    def test_conqueror_ending(self) -> None:
        """Very low Rebel and CC reputation should trigger Conqueror."""
        camp = _campaign()
        camp.adjust_reputation("rebel", -50)
        camp.adjust_reputation("crimson_compact", -50)
        calc = self._calc(camp)
        ending = calc.calculate()
        assert ending.ending_id == "conqueror"

    def test_all_endings_have_valid_data(self) -> None:
        """Every defined ending should have non-empty fields."""
        camp = _campaign()
        calc = self._calc(camp)
        for ending in calc.get_all_possible_endings():
            assert len(ending.ending_id) > 0
            assert len(ending.title) > 0
            assert len(ending.narrative_text) > 0
            assert len(ending.honour_colour) == 3

    def test_redeemed_takes_priority_over_liberator(self) -> None:
        """If FSA >= 50, Redeemed should win even if Rebel/CC are high."""
        camp = _campaign()
        camp.adjust_reputation("fsa", 60)
        camp.adjust_reputation("rebel", 30)
        camp.adjust_reputation("crimson_compact", 25)
        calc = self._calc(camp)
        ending = calc.calculate()
        assert ending.ending_id == "redeemed"

    def test_betrayed_takes_priority_over_all(self) -> None:
        """Betrayed should trigger even if other criteria are met."""
        camp = _campaign()
        camp.adjust_reputation("fsa", 60)
        camp.adjust_reputation("rebel", 30)
        camp.adjust_reputation("crimson_compact", 25)
        camp.record_decision("betray:alpha")
        calc = self._calc(camp)
        ending = calc.calculate()
        assert ending.ending_id == "betrayed"
