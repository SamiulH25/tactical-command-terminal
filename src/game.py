"""Game state machine — manages screen stack and the main event loop.

The Game class owns the display, the CRT renderer, and a stack of Screen
objects.  Each frame it dispatches events to the active screen, updates
it, renders it, applies terminal effects, and composites to the window.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import TYPE_CHECKING

import pygame

from src import config
from src.screens.base_screen import Screen

if TYPE_CHECKING:
    from src.core.monitor_frame import MonitorFrame
    from src.core.terminal import TerminalRenderer

logger = logging.getLogger(__name__)


class Game:
    """State machine that drives screen rendering and input dispatch.

    Invariants:
    - The screen stack is never empty while ``running`` is True.
    - Only the top screen on the stack receives events and renders.
    - Screens are cleanly finalised via ``on_exit()`` before removal.
    """

    def __init__(
        self,
        renderer: TerminalRenderer,
        display: pygame.Surface,
        monitor: MonitorFrame | None = None,
    ) -> None:
        self._renderer = renderer
        self._display = display
        self._monitor = monitor
        self._screen_stack: list[Screen] = []
        self._running = False
        self._clock = pygame.time.Clock()
        self._on_escape: Callable[[], bool] | None = None

    # ------------------------------------------------------------------
    # Screen stack management
    # ------------------------------------------------------------------

    def push_screen(self, screen: Screen) -> None:
        if self._screen_stack:
            logger.debug(
                "Pushing %r on top of %r",
                type(screen).__name__,
                type(self._screen_stack[-1]).__name__,
            )
        self._screen_stack.append(screen)
        screen.on_enter()

    def pop_screen(self) -> Screen:
        if not self._screen_stack:
            raise RuntimeError("Cannot pop from empty screen stack")
        screen = self._screen_stack.pop()
        screen.on_exit()
        logger.debug("Popped %r", type(screen).__name__)
        return screen

    def replace_screen(self, screen: Screen) -> None:
        if self._screen_stack:
            self.pop_screen()
        self.push_screen(screen)

    @property
    def current_screen(self) -> Screen:
        if not self._screen_stack:
            raise RuntimeError("No screen is currently active")
        return self._screen_stack[-1]

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    def run(self, initial_screen: Screen) -> None:
        """Start the main event loop.  Blocks until the game is quit."""
        self.push_screen(initial_screen)
        self._running = True

        while self._running:
            dt = self._clock.tick(config.TARGET_FPS) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._running = False
                    break
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    if self._on_escape is not None and self._on_escape():
                        continue  # Escape was handled (e.g., pause)
                    self._running = False
                    break
                self.current_screen.handle_event(event)

            self.current_screen.update(dt)

            # Clear game surface, render, apply effects
            self._renderer.display.fill(config.COLOR_BG)
            self.current_screen.render()
            self._renderer.apply_effects()

            # Composite to window
            if self._monitor is not None:
                self._monitor.blit_to(self._display)
            pygame.display.flip()

        # Clean up remaining screens
        while self._screen_stack:
            self.pop_screen()
        logger.info("Game loop exited cleanly")

    @property
    def display(self) -> pygame.Surface:
        return self._display

    @property
    def running(self) -> bool:
        return self._running

    @property
    def on_escape(self) -> Callable[[], bool] | None:
        """Optional callback for Escape key handling.

        Return ``True`` to consume the Escape event (e.g. push pause),
        ``False`` or ``None`` to proceed with quitting.
        """
        return self._on_escape

    @on_escape.setter
    def on_escape(self, value: Callable[[], bool] | None) -> None:
        self._on_escape = value
