"""Tests for the main entry point module.

Verifies that Pygame initializes correctly, the monitor frame is created,
and the module structure is sound before any game logic is layered on top.
"""

import main
import pygame

from src import config
from src.core.monitor_frame import MonitorFrame


class TestPygameInit:
    """Verify Pygame subsystem initialization."""

    def test_init_pygame_returns_tuple(self) -> None:
        """_init_pygame should return (display, monitor, renderer)."""
        result = main._init_pygame()
        assert isinstance(result, tuple)
        assert len(result) == 3
        display, monitor, _renderer = result
        assert isinstance(display, pygame.Surface)
        assert isinstance(monitor, MonitorFrame)

    def test_display_size_matches_config(self) -> None:
        """Display surface should match the configured resolution."""
        display, _monitor, _renderer = main._init_pygame()
        assert display.get_size() == (config.SCREEN_WIDTH, config.SCREEN_HEIGHT)

    def test_monitor_game_surface_is_1080p(self) -> None:
        """Monitor's game surface should be 1920x1080."""
        _display, monitor, _renderer = main._init_pygame()
        assert monitor.game_surface.get_size() == (1920, 1080)

    def test_display_caption_is_terminal_id(self) -> None:
        """Window caption should include the terminal designation."""
        main._init_pygame()
        caption = pygame.display.get_caption()[0]
        assert "Tactical Command Terminal" in caption


class TestMainReturn:
    """Verify main() return behaviour."""

    def test_main_returns_zero_on_clean_exit(self) -> None:
        """main() should return 0 when the loop exits normally."""
        main._init_pygame()
        pygame.event.post(pygame.Event(pygame.QUIT))
        result = main.main()
        assert result == 0

    def test_main_quits_pygame_afterwards(self) -> None:
        """After main() returns, pygame must be cleanly shut down."""
        main._init_pygame()
        pygame.event.post(pygame.Event(pygame.QUIT))
        main.main()
        assert pygame.get_init() is False
