"""Abstract base class for game screens.

Every screen in the game inherits from this class.  Screens are pushed
onto and popped off a stack managed by the Game state machine.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

import pygame

if TYPE_CHECKING:
    from src.core.terminal import TerminalRenderer


class Screen(ABC):
    """Base class representing a single full-screen view.

    Subclasses must implement :meth:`render`.  Event handling and
    per-frame updates are optional overrides.

    Lifecycle:
    - ``on_enter()`` is called once when the screen is pushed.
    - ``handle_event()`` and ``update()`` are called each frame while active.
    - ``render()`` draws the screen onto the display.
    - ``on_exit()`` is called once when the screen is popped.

    Subclass responsibilities:
    - Call ``super().on_enter()`` and ``super().on_exit()`` if overriding.
    - ``render()`` **must** be overridden.
    """

    def __init__(self, renderer: TerminalRenderer) -> None:
        """Create a Screen bound to the given terminal renderer.

        Args:
            renderer: The CRT terminal renderer for drawing.
        """
        self._renderer = renderer

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def on_enter(self) -> None:  # noqa: B027
        """Called once immediately after this screen is pushed."""

    def on_exit(self) -> None:  # noqa: B027
        """Called once immediately before this screen is popped."""

    # ------------------------------------------------------------------
    # Per-frame hooks
    # ------------------------------------------------------------------

    def handle_event(self, event: pygame.event.Event) -> None:  # noqa: B027
        """Process a single Pygame event.

        Override to respond to mouse clicks, key presses, etc.
        The default implementation does nothing.

        Args:
            event: The Pygame event to handle.
        """

    def update(self, dt: float) -> None:  # noqa: B027
        """Update screen state for the current frame.

        Override for animations, timers, or logic that runs every frame.

        Args:
            dt: Delta time since last frame in seconds.
        """

    @abstractmethod
    def render(self) -> None:
        """Draw the screen onto the renderer's display surface.

        Must be overridden by every subclass.
        The display should be cleared by the caller before this call.
        """
        raise NotImplementedError

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @property
    def display(self) -> pygame.Surface:
        """Convenience access to the underlying display surface."""
        return self._renderer.display
