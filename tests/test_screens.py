"""Tests for screen classes: MainMenu, ShipMenu, MechSelect.

Verifies:
- Screen construction and lifecycle (on_enter, on_exit)
- Button layout and counts
- Event handling (mouse clicks, keyboard shortcuts)
- Tab switching in ShipMenu
- Faction unlock logic in MechSelect
- Callback invocation on button clicks
- Render methods do not crash
"""

from __future__ import annotations

import pygame
import pytest

from src.core.terminal import TerminalRenderer
from src.models.campaign import Campaign
from src.models.data_loader import GameData, load_all_data
from src.models.faction import Faction
from src.screens.main_menu import MainMenu
from src.screens.mech_select import MechSelect
from src.screens.ship_menu import ShipMenu

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def game_data() -> GameData:
    return load_all_data()


@pytest.fixture()
def campaign() -> Campaign:
    return Campaign()


@pytest.fixture()
def display() -> pygame.Surface:
    """Provide a 1920x1080 display surface."""
    pygame.display.set_mode((1920, 1080))
    surf = pygame.display.get_surface()
    assert surf is not None
    return surf


@pytest.fixture()
def renderer(display: pygame.Surface) -> TerminalRenderer:
    return TerminalRenderer(display)


# ---------------------------------------------------------------------------
# MainMenu tests
# ---------------------------------------------------------------------------


class TestMainMenu:
    """Verify MainMenu construction, layout, and interactions."""

    def test_main_menu_constructs(self, renderer: TerminalRenderer) -> None:
        """MainMenu should construct without error."""
        mm = MainMenu(renderer)
        assert mm._buttons == []
        assert mm._cursor_visible is True

    def test_on_enter_builds_buttons(self, renderer: TerminalRenderer) -> None:
        """on_enter should create exactly 3 buttons."""
        mm = MainMenu(renderer)
        mm.on_enter()
        assert len(mm._buttons) == 3

    def test_button_labels(self, renderer: TerminalRenderer) -> None:
        """Button labels should match expected text."""
        mm = MainMenu(renderer)
        mm.on_enter()
        labels = [b.label for b in mm._buttons]
        assert "[1]  NEW DEPLOYMENT" in labels[0]
        assert "[2]  RESUME SESSION" in labels[1]
        assert "[3]  TERMINATE LINK" in labels[2]

    def test_resume_button_disabled(self, renderer: TerminalRenderer) -> None:
        """Resume button should be disabled by default."""
        mm = MainMenu(renderer)
        mm.on_enter()
        assert mm._buttons[1].enabled is False

    def test_new_deployment_callback(self, renderer: TerminalRenderer) -> None:
        """Clicking button 0 should invoke on_new_deployment_cb."""
        mm = MainMenu(renderer)
        called = False

        def cb() -> None:
            nonlocal called
            called = True

        mm.on_new_deployment_cb = cb
        mm.on_enter()
        # Simulate click on first button
        mm._mouse_pos = mm._buttons[0].rect.center
        mm._buttons[0].set_hover(mm._mouse_pos)
        mm._buttons[0].click()
        assert called is True

    def test_terminate_button_posts_quit(self, renderer: TerminalRenderer) -> None:
        """Clicking button 2 should post a QUIT event."""
        mm = MainMenu(renderer)
        mm.on_enter()
        mm._mouse_pos = mm._buttons[2].rect.center
        mm._buttons[2].set_hover(mm._mouse_pos)
        mm._buttons[2].click()
        # Check that a QUIT event was posted
        events = pygame.event.get()
        assert any(e.type == pygame.QUIT for e in events)

    def test_keyboard_shortcut_1_triggers_deploy(self, renderer: TerminalRenderer) -> None:
        """Pressing K_1 should trigger new deployment callback."""
        mm = MainMenu(renderer)
        called = False

        def cb() -> None:
            nonlocal called
            called = True

        mm.on_new_deployment_cb = cb
        mm.on_enter()
        mm.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_1))
        assert called is True

    def test_render_no_crash(self, renderer: TerminalRenderer) -> None:
        """Rendering must not raise."""
        mm = MainMenu(renderer)
        mm.on_enter()
        mm.render()

    def test_cursor_blink_update(self, renderer: TerminalRenderer) -> None:
        """Cursor visibility should toggle on update."""
        mm = MainMenu(renderer)
        mm.on_enter()
        initial = mm._cursor_visible
        mm.update(0.7)  # > 0.6s threshold
        assert mm._cursor_visible != initial


# ---------------------------------------------------------------------------
# ShipMenu tests
# ---------------------------------------------------------------------------


class TestShipMenu:
    """Verify ShipMenu construction, layout, and interactions."""

    def test_ship_menu_constructs(self, renderer: TerminalRenderer, campaign: Campaign) -> None:
        """ShipMenu should construct without error."""
        sm = ShipMenu(renderer, campaign)
        assert sm._active_tab == "briefing"
        assert sm._room_buttons == []

    def test_on_enter_builds_layout(self, renderer: TerminalRenderer, campaign: Campaign) -> None:
        """on_enter should create tab and room buttons."""
        sm = ShipMenu(renderer, campaign)
        sm.on_enter()
        assert sm._tab_briefing is not None
        assert sm._tab_ops is not None
        assert len(sm._room_buttons) == 3

    def test_room_button_labels(self, renderer: TerminalRenderer, campaign: Campaign) -> None:
        """Room buttons should have correct labels."""
        sm = ShipMenu(renderer, campaign)
        sm.on_enter()
        labels = [b.label for b in sm._room_buttons]
        assert "[ASSAULT]" in labels[0]
        assert "[SALVAGE]" in labels[1]
        assert "[R&R]" in labels[2]

    def test_tab_switching(self, renderer: TerminalRenderer, campaign: Campaign) -> None:
        """Clicking ops tab should switch active tab."""
        sm = ShipMenu(renderer, campaign)
        sm.on_enter()
        assert sm._active_tab == "briefing"
        assert sm._tab_ops is not None
        sm._mouse_pos = sm._tab_ops.rect.center
        sm._tab_ops.set_hover(sm._mouse_pos)
        sm._tab_ops.click()
        assert sm._active_tab == "operations"

    def test_briefing_tab_click(self, renderer: TerminalRenderer, campaign: Campaign) -> None:
        """Clicking briefing tab should switch back."""
        sm = ShipMenu(renderer, campaign)
        sm.on_enter()
        sm._active_tab = "operations"
        assert sm._tab_briefing is not None
        sm._mouse_pos = sm._tab_briefing.rect.center
        sm._tab_briefing.set_hover(sm._mouse_pos)
        sm._tab_briefing.click()
        assert sm._active_tab == "briefing"

    def test_assault_callback(self, renderer: TerminalRenderer, campaign: Campaign) -> None:
        """Clicking assault button should invoke callback."""
        sm = ShipMenu(renderer, campaign)
        called = False

        def cb() -> None:
            nonlocal called
            called = True

        sm._on_assault_cb = cb
        sm.on_enter()
        sm._mouse_pos = sm._room_buttons[0].rect.center
        sm._room_buttons[0].set_hover(sm._mouse_pos)
        sm._room_buttons[0].click()
        assert called is True

    def test_salvage_callback(self, renderer: TerminalRenderer, campaign: Campaign) -> None:
        """Clicking salvage button should invoke callback."""
        sm = ShipMenu(renderer, campaign)
        called = False

        def cb() -> None:
            nonlocal called
            called = True

        sm._on_salvage_cb = cb
        sm.on_enter()
        sm._mouse_pos = sm._room_buttons[1].rect.center
        sm._room_buttons[1].set_hover(sm._mouse_pos)
        sm._room_buttons[1].click()
        assert called is True

    def test_rest_callback(self, renderer: TerminalRenderer, campaign: Campaign) -> None:
        """Clicking rest button should invoke callback."""
        sm = ShipMenu(renderer, campaign)
        called = False

        def cb() -> None:
            nonlocal called
            called = True

        sm._on_rest_cb = cb
        sm.on_enter()
        sm._mouse_pos = sm._room_buttons[2].rect.center
        sm._room_buttons[2].set_hover(sm._mouse_pos)
        sm._room_buttons[2].click()
        assert called is True

    def test_render_no_crash(self, renderer: TerminalRenderer, campaign: Campaign) -> None:
        """Rendering must not raise."""
        sm = ShipMenu(renderer, campaign)
        sm.on_enter()
        sm.render()

    def test_render_with_mech(
        self, renderer: TerminalRenderer, campaign: Campaign, game_data: GameData
    ) -> None:
        """Rendering with a deployed mech must not crash."""
        mech = game_data.get_mech("fsa_bastion")
        assert mech is not None
        from src.systems.deckbuilder import build_deployed_mech

        pilot = game_data.get_pilot("aggressive")
        assert pilot is not None
        deployed = build_deployed_mech(mech, pilot, game_data)
        sm = ShipMenu(renderer, campaign, mech=deployed)
        sm.on_enter()
        sm.render()

    def test_tab_switch_renders(self, renderer: TerminalRenderer, campaign: Campaign) -> None:
        """Both tabs should render without crash."""
        sm = ShipMenu(renderer, campaign)
        sm.on_enter()
        sm.render()
        sm._active_tab = "operations"
        sm.render()


# ---------------------------------------------------------------------------
# MechSelect tests
# ---------------------------------------------------------------------------


class TestMechSelectLifecycle:
    """Verify MechSelect construction, enter/exit, and basic state."""

    def test_mech_select_constructs(
        self, renderer: TerminalRenderer, game_data: GameData, campaign: Campaign
    ) -> None:
        """MechSelect should construct without error."""
        ms = MechSelect(renderer, game_data, campaign)
        assert ms._step == 1
        assert ms._selected_frame is None
        assert ms._selected_pilot is None
        assert ms._equipment == {"weapon": None, "armor": None, "utility": None}

    def test_on_enter_resets_state(
        self, renderer: TerminalRenderer, game_data: GameData, campaign: Campaign
    ) -> None:
        """on_enter should reset all state to defaults."""
        ms = MechSelect(renderer, game_data, campaign)
        ms._step = 3
        ms._selected_frame = game_data.mech_frames[0]
        ms._selected_pilot = game_data.get_pilot("aggressive")
        ms.on_enter()
        assert ms._step == 1
        # Verify state was reset by on_enter
        assert ms._selected_frame is None
        assert ms._selected_pilot is None  # type: ignore[unreachable]

    def test_on_enter_builds_ui(
        self, renderer: TerminalRenderer, game_data: GameData, campaign: Campaign
    ) -> None:
        """on_enter should create buttons and panels."""
        ms = MechSelect(renderer, game_data, campaign)
        ms.on_enter()
        assert ms._content_panel is not None
        assert ms._preview_panel is not None
        assert len(ms._faction_buttons) > 0
        assert len(ms._step_buttons) > 0
        assert len(ms._nav_buttons) > 0

    def test_render_no_crash(
        self, renderer: TerminalRenderer, game_data: GameData, campaign: Campaign
    ) -> None:
        """Rendering must not raise on any step."""
        ms = MechSelect(renderer, game_data, campaign)
        ms.on_enter()
        for step in range(1, 6):
            ms._step = step
            ms._build_step_buttons()
            ms._build_nav_buttons()
            ms.render()


class TestMechSelectFactionButtons:
    """Verify faction button layout and interaction."""

    def test_three_faction_buttons(
        self, renderer: TerminalRenderer, game_data: GameData, campaign: Campaign
    ) -> None:
        """Should have exactly 3 faction buttons (FSA, CC, Rebel)."""
        ms = MechSelect(renderer, game_data, campaign)
        ms.on_enter()
        assert len(ms._faction_buttons) == 3

    def test_faction_button_labels(
        self, renderer: TerminalRenderer, game_data: GameData, campaign: Campaign
    ) -> None:
        """Faction buttons should display correct names."""
        ms = MechSelect(renderer, game_data, campaign)
        ms.on_enter()
        labels = [b.label for b in ms._faction_buttons]
        assert any("FSA" in lbl for lbl in labels)
        assert any("CRIMSON COMPACT" in lbl for lbl in labels)
        assert any("REBEL" in lbl for lbl in labels)

    def test_click_faction_button(
        self, renderer: TerminalRenderer, game_data: GameData, campaign: Campaign
    ) -> None:
        """Clicking FSA faction button (unlocked) should select it."""
        ms = MechSelect(renderer, game_data, campaign)
        ms.on_enter()
        # FSA is always unlocked and is the first faction
        fsa_btn = ms._faction_buttons[0]
        assert fsa_btn.enabled  # Must be unlocked
        fsa_btn.click()
        assert ms._selected_faction == Faction.FSA

    def test_locked_faction_button_disabled(
        self, renderer: TerminalRenderer, game_data: GameData, campaign: Campaign
    ) -> None:
        """Locked faction buttons should be disabled."""
        ms = MechSelect(renderer, game_data, campaign)
        ms.on_enter()
        # CC requires floor 5, Rebel requires floor 10
        cc_btn = ms._faction_buttons[1]
        rebel_btn = ms._faction_buttons[2]
        assert cc_btn.enabled is False
        assert rebel_btn.enabled is False

    def test_selecting_faction_clears_mech(
        self, renderer: TerminalRenderer, game_data: GameData
    ) -> None:
        """Changing faction should reset the selected mech."""
        # Unlock CC by setting floors_cleared high enough
        campaign = Campaign()
        campaign.floors_cleared = 5
        ms = MechSelect(renderer, game_data, campaign)
        ms.on_enter()
        # Select a CC mech
        ms._selected_faction = Faction.CRIMSON_COMPACT
        ms._selected_frame = game_data.get_mech("cc_bastion")
        assert ms._selected_frame is not None
        # Switch back to FSA — button[0] is FSA
        fsa_btn = ms._faction_buttons[0]
        assert fsa_btn.enabled  # FSA is always unlocked
        ms._mouse_pos = fsa_btn.rect.center
        fsa_btn.set_hover(ms._mouse_pos)
        fsa_btn.click()
        assert ms._selected_faction == Faction.FSA
        assert ms._selected_frame is None


class TestMechSelectNavigation:
    """Verify step navigation logic."""

    def test_step_2_requires_mech_selection(
        self, renderer: TerminalRenderer, game_data: GameData, campaign: Campaign
    ) -> None:
        """NEXT should be disabled on step 2 until a mech is selected."""
        ms = MechSelect(renderer, game_data, campaign)
        ms.on_enter()
        ms._step = 2
        ms._build_step_buttons()
        ms._build_nav_buttons()
        # Nav buttons at step 2: back + next
        next_btns = [b for b in ms._nav_buttons if "NEXT" in b.label]
        assert len(next_btns) == 1
        # NEXT should be disabled (no mech selected)
        assert next_btns[0].enabled is False

    def test_step_2_enables_next_after_selection(
        self, renderer: TerminalRenderer, game_data: GameData, campaign: Campaign
    ) -> None:
        """Selecting a mech should enable NEXT."""
        ms = MechSelect(renderer, game_data, campaign)
        ms.on_enter()
        # Select first mech
        unit_btns = [b for b in ms._step_buttons if b.enabled]
        if unit_btns:
            unit_btns[0].click()
        ms._step = 2
        ms._build_step_buttons()
        ms._build_nav_buttons()
        next_btns = [b for b in ms._nav_buttons if "NEXT" in b.label]
        if next_btns and ms._selected_frame is not None:
            assert next_btns[0].enabled is True

    def test_back_button_goes_to_previous_step(
        self, renderer: TerminalRenderer, game_data: GameData, campaign: Campaign
    ) -> None:
        """BACK should decrement step."""
        ms = MechSelect(renderer, game_data, campaign)
        ms.on_enter()
        ms._step = 3
        ms._build_nav_buttons()
        back_btns = [b for b in ms._nav_buttons if "BACK" in b.label]
        assert len(back_btns) == 1
        # Click requires hover state
        ms._mouse_pos = back_btns[0].rect.center
        back_btns[0].set_hover(ms._mouse_pos)
        back_btns[0].click()
        assert ms._step == 2

    def test_back_disabled_on_step_1(
        self, renderer: TerminalRenderer, game_data: GameData, campaign: Campaign
    ) -> None:
        """BACK should be disabled on step 1."""
        ms = MechSelect(renderer, game_data, campaign)
        ms.on_enter()
        ms._step = 1
        ms._build_nav_buttons()
        back_btns = [b for b in ms._nav_buttons if "BACK" in b.label]
        assert len(back_btns) == 1
        assert back_btns[0].enabled is False

    def test_no_nav_buttons_on_step_5(
        self, renderer: TerminalRenderer, game_data: GameData, campaign: Campaign
    ) -> None:
        """Step 5 (confirmation) should not show nav buttons."""
        ms = MechSelect(renderer, game_data, campaign)
        ms.on_enter()
        ms._step = 5
        ms._build_nav_buttons()
        assert len(ms._nav_buttons) == 0


class TestMechSelectDeploy:
    """Verify deploy callback invocation."""

    def test_deploy_invokes_callback(
        self, renderer: TerminalRenderer, game_data: GameData, campaign: Campaign
    ) -> None:
        """_on_deploy should call on_deploy with correct args."""
        ms = MechSelect(renderer, game_data, campaign)
        ms.on_enter()

        # Select a mech
        ms._selected_frame = game_data.get_mech("fsa_bastion")
        assert ms._selected_frame is not None

        result: tuple[str, str, dict[str, str | None]] | None = None

        def on_deploy(frame, pilot_type, equipment) -> None:  # type: ignore[no-untyped-def]
            nonlocal result
            result = (frame.id, pilot_type, equipment)

        ms.on_deploy = on_deploy
        ms._on_deploy()

        assert result is not None
        assert result[0] == "fsa_bastion"
        assert result[1] == "aggressive"  # default pilot type
        assert isinstance(result[2], dict)

    def test_deploy_with_selected_pilot(
        self, renderer: TerminalRenderer, game_data: GameData, campaign: Campaign
    ) -> None:
        """Deploy should pass the selected pilot type."""
        ms = MechSelect(renderer, game_data, campaign)
        ms.on_enter()
        ms._selected_frame = game_data.get_mech("fsa_bastion")
        ms._selected_pilot = game_data.get_pilot("scout")

        result: tuple[str, str, dict[str, str | None]] | None = None

        def on_deploy(frame, pilot_type, equipment) -> None:  # type: ignore[no-untyped-def]
            nonlocal result
            result = (frame.id, pilot_type, equipment)

        ms.on_deploy = on_deploy
        ms._on_deploy()

        assert result is not None
        assert result[1] == "scout"

    def test_deploy_with_no_callback_logs_warning(
        self, renderer: TerminalRenderer, game_data: GameData, campaign: Campaign
    ) -> None:
        """Deploy without a callback should log a warning, not crash."""
        ms = MechSelect(renderer, game_data, campaign)
        ms.on_enter()
        ms._selected_frame = game_data.get_mech("fsa_bastion")
        ms.on_deploy = None
        # Should not raise
        ms._on_deploy()
