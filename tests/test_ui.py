"""Tests for the Panel and TerminalButton UI components."""

import pygame
import pytest

from src import config
from src.ui.button import TerminalButton
from src.ui.panel import Panel


class TestPanel:
    """Verify Panel rendering and properties."""

    @pytest.fixture(autouse=True)
    def _ensure_font(self) -> None:
        """Reinitialise font subsystem in case another test quit pygame."""
        pygame.font.init()

    def test_rect_dimensions(self) -> None:
        """Panel rect must match constructor arguments."""
        panel = Panel(10, 20, 300, 200, "TEST")
        assert panel.rect.left == 10
        assert panel.rect.top == 20
        assert panel.rect.width == 300
        assert panel.rect.height == 200

    def test_title_stored(self) -> None:
        """Panel title must be stored as provided."""
        panel = Panel(0, 0, 100, 100, "MY TITLE")
        assert panel.title == "MY TITLE"

    def _font(self) -> pygame.font.Font:
        """Provide a default font for testing."""
        return pygame.font.Font(None, 16)

    def test_render_no_crash(self) -> None:
        """Rendering a panel must not raise."""
        surface = pygame.Surface((400, 300))
        panel = Panel(10, 10, 200, 150, "TEST")
        panel.render(surface, self._font())

    def test_render_empty_title_no_crash(self) -> None:
        """Panel with no title must render without error."""
        surface = pygame.Surface((400, 300))
        panel = Panel(10, 10, 200, 150)
        panel.render(surface, self._font())

    def test_border_drawn(self) -> None:
        """After rendering, border pixels should differ from background."""
        surface = pygame.Surface((200, 150))
        surface.fill(config.COLOR_BG)
        panel = Panel(10, 10, 100, 80)
        panel.render(surface, self._font())
        # Top-left corner should be green (border)
        corner = surface.get_at((10, 10))
        assert corner[:3] == config.PHOSPHOR_GREEN


class TestTerminalButton:
    """Verify TerminalButton interaction and rendering."""

    @pytest.fixture(autouse=True)
    def _ensure_font(self) -> None:
        """Reinitialise font subsystem in case another test quit pygame."""
        pygame.font.init()

    def _make_button(self) -> TerminalButton:
        return TerminalButton(10, 10, 200, 36, "[1] TEST", lambda: None, key=pygame.K_1)

    def test_hover_detection(self) -> None:
        """Button should register hover when mouse is inside."""
        btn = self._make_button()
        btn.set_hover((50, 25))  # Inside the button
        assert btn.hovered is True
        btn.set_hover((500, 500))  # Outside
        assert btn.hovered is False

    def test_click_when_hovered(self) -> None:
        """Click should fire on_click when hovered."""
        called = False

        def callback() -> None:
            nonlocal called
            called = True

        btn = TerminalButton(10, 10, 200, 36, "TEST", callback)
        btn.set_hover((50, 25))
        result = btn.click()
        assert result is True
        assert called is True

    def test_click_when_not_hovered(self) -> None:
        """Click should not fire when not hovered."""
        btn = TerminalButton(10, 10, 200, 36, "TEST", lambda: None)
        result = btn.click()
        assert result is False

    def test_click_disabled(self) -> None:
        """Disabled button should never fire on_click."""
        called = False
        btn = TerminalButton(10, 10, 200, 36, "TEST", lambda: None, enabled=False)
        btn.set_hover((50, 25))
        result = btn.click()
        assert result is False
        assert called is False
        assert btn.hovered is False

    def test_keyboard_shortcut(self) -> None:
        """Matching key should activate the button."""
        called = False

        def callback() -> None:
            nonlocal called
            called = True

        btn = TerminalButton(10, 10, 200, 36, "[1] TEST", callback, key=pygame.K_1)
        result = btn.press_key(pygame.K_1)
        assert result is True
        assert called is True

    def test_keyboard_shortcut_no_match(self) -> None:
        """Non-matching key should not activate the button."""
        btn = TerminalButton(10, 10, 200, 36, "[1] TEST", lambda: None, key=pygame.K_1)
        result = btn.press_key(pygame.K_2)
        assert result is False

    def test_keyboard_disabled(self) -> None:
        """Keyboard shortcut should not work on disabled button."""
        called = False
        btn = TerminalButton(
            10, 10, 200, 36, "[1] TEST", lambda: None, key=pygame.K_1, enabled=False
        )
        result = btn.press_key(pygame.K_1)
        assert result is False
        assert called is False

    def test_render_no_crash(self) -> None:
        """Rendering a button must not raise."""
        surface = pygame.Surface((400, 300))
        btn = self._make_button()
        btn.render(surface, pygame.font.Font(None, 16))

    def test_contains_with_none(self) -> None:
        """contains(None) should return False."""
        btn = self._make_button()
        assert btn.contains(None) is False
