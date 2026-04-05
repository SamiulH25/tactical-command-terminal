"""Transition screen — wraps a TransitionEffect as a full-screen view.

This screen renders a :class:`~src.core.transitions.TransitionEffect` each
frame and calls an ``on_complete`` callback when the effect finishes.  The
transition can be skipped by pressing any key or clicking the mouse.

Usage::

    def show_next():
        game.replace_screen(NextScreen(...))

    ts = TransitionScreen(
        renderer,
        make_signal_lost(victory=True, outpost_name="Outpost 7"),
        on_complete=show_next,
    )
    game.replace_screen(ts)
"""

from __future__ import annotations

from collections.abc import Callable

import pygame

from src.core.terminal import TerminalRenderer
from src.core.transitions import TransitionEffect
from src.screens.base_screen import Screen


class TransitionScreen(Screen):
    """Screen that plays a transition effect and then calls a callback."""

    def __init__(
        self,
        renderer: TerminalRenderer,
        effect: TransitionEffect,
        on_complete: Callable[[], None],
    ) -> None:
        """Create a transition screen.

        Args:
            renderer: The CRT terminal renderer.
            effect: The transition effect to play.
            on_complete: Callback invoked when the transition finishes
                (or is skipped).
        """
        super().__init__(renderer)
        self._effect = effect
        self._on_complete = on_complete
        self._done = False

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
            self._effect.skip()

    def update(self, dt: float) -> None:
        if self._done:
            return
        complete = self._effect.update(dt)
        if complete:
            self._done = True
            self._on_complete()

    def render(self) -> None:
        surface = self.display
        surface.fill((0, 0, 0))
        self._effect.render(surface)
