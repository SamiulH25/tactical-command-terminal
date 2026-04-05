"""Tests for the Game state machine and Screen base class.

Verifies screen stack management, lifecycle callbacks, and event
dispatch correctness.
"""

import pygame
import pytest

from src.core.terminal import TerminalRenderer
from src.game import Game
from src.screens.base_screen import Screen

# ---------------------------------------------------------------------------
# Concrete test screens
# ---------------------------------------------------------------------------


class _DummyScreen(Screen):
    """Minimal screen for testing — records lifecycle calls."""

    def __init__(self, renderer: TerminalRenderer) -> None:
        """Create a dummy screen."""
        super().__init__(renderer)
        self.entered = False
        self.exited = False
        self.events_handled: list[pygame.event.Event] = []
        self.updates: list[float] = []
        self.render_count = 0

    def on_enter(self) -> None:
        """Mark entry."""
        self.entered = True

    def on_exit(self) -> None:
        """Mark exit."""
        self.exited = True

    def handle_event(self, event: pygame.event.Event) -> None:
        """Record the event."""
        self.events_handled.append(event)

    def update(self, dt: float) -> None:
        """Record the delta time."""
        self.updates.append(dt)

    def render(self) -> None:
        """Increment render counter."""
        self.render_count += 1


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def display() -> pygame.Surface:
    """Provide a minimal display surface."""
    return pygame.Surface((256, 256))


@pytest.fixture()
def renderer(display: pygame.Surface) -> TerminalRenderer:
    """Provide a terminal renderer."""
    return TerminalRenderer(display)


@pytest.fixture()
def game(renderer: TerminalRenderer) -> Game:
    """Provide a Game instance (not running)."""
    return Game(renderer, renderer.display, monitor=None)


# ---------------------------------------------------------------------------
# Screen base class
# ---------------------------------------------------------------------------


class TestScreenBase:
    """Verify Screen abstract interface."""

    def test_render_is_abstract(self, renderer: TerminalRenderer) -> None:
        """Screen cannot be instantiated without implementing render()."""
        with pytest.raises(TypeError, match="abstract class"):
            Screen(renderer)  # type: ignore[abstract]

    def test_display_property(self, renderer: TerminalRenderer) -> None:
        """Screen.display returns the underlying display surface."""
        screen = _DummyScreen(renderer)
        assert screen.display is renderer.display


# ---------------------------------------------------------------------------
# Game: screen stack
# ---------------------------------------------------------------------------


class TestGameScreenStack:
    """Verify Game screen stack operations."""

    def test_push_screen_calls_enter(self, game: Game) -> None:
        """Pushing a screen must call its on_enter()."""
        screen = _DummyScreen(game._renderer)
        game.push_screen(screen)
        assert screen.entered is True

    def test_pop_screen_calls_exit(self, game: Game) -> None:
        """Popping a screen must call its on_exit()."""
        screen = _DummyScreen(game._renderer)
        game.push_screen(screen)
        game.pop_screen()
        assert screen.exited is True

    def test_pop_returns_screen(self, game: Game) -> None:
        """pop_screen must return the screen that was popped."""
        screen = _DummyScreen(game._renderer)
        game.push_screen(screen)
        result = game.pop_screen()
        assert result is screen

    def test_pop_empty_raises(self, game: Game) -> None:
        """Popping from empty stack must raise RuntimeError."""
        with pytest.raises(RuntimeError, match="empty screen stack"):
            game.pop_screen()

    def test_current_screen_top_of_stack(self, game: Game) -> None:
        """current_screen must return the most recently pushed screen."""
        s1 = _DummyScreen(game._renderer)
        s2 = _DummyScreen(game._renderer)
        game.push_screen(s1)
        game.push_screen(s2)
        assert game.current_screen is s2

    def test_current_screen_empty_raises(self, game: Game) -> None:
        """Accessing current_screen with no screens must raise."""
        with pytest.raises(RuntimeError, match="No screen"):
            _ = game.current_screen

    def test_replace_screen_pops_old(self, game: Game) -> None:
        """replace_screen must pop the previous screen."""
        s1 = _DummyScreen(game._renderer)
        s2 = _DummyScreen(game._renderer)
        game.push_screen(s1)
        game.replace_screen(s2)
        assert s1.exited is True
        assert game.current_screen is s2

    def test_stack_depth_after_operations(self, game: Game) -> None:
        """Stack depth must reflect push/pop operations."""
        s1 = _DummyScreen(game._renderer)
        s2 = _DummyScreen(game._renderer)
        game.push_screen(s1)
        game.push_screen(s2)
        assert len(game._screen_stack) == 2
        game.pop_screen()
        assert len(game._screen_stack) == 1
        assert game.current_screen is s1

    def test_running_property_initial(self, game: Game) -> None:
        """running must be False before run() is called."""
        assert game.running is False
