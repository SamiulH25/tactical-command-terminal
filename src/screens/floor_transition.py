"""Floor transition screen — static burst and text crawl between floors.

Lore-accurate format::

    > UPLOADING SECTOR DATA...
    > SECTOR 06 LOADED
    > New sector entered.  Outpost Bravo perimeter detected.
    > SIGNAL RE-ACQUIRED

The transition plays for a fixed duration then automatically advances
to the next screen.
"""

from __future__ import annotations

from collections.abc import Callable

import pygame

from src import config
from src.core.terminal import TerminalRenderer
from src.screens.base_screen import Screen


class FloorTransitionScreen(Screen):
    """A brief transition screen simulating signal degradation and re-acquire."""

    def __init__(
        self,
        renderer: TerminalRenderer,
        transition_text: str,
        on_complete: Callable[[], None] | None = None,
        duration: float = 3.0,
    ) -> None:
        """Create the FloorTransitionScreen.

        Args:
            renderer: The CRT terminal renderer.
            transition_text: Multi-line text to display during transition.
            on_complete: Callback invoked when the transition ends.
            duration: How long the transition lasts in seconds.
        """
        super().__init__(renderer)
        self._transition_text = transition_text
        self.on_complete = on_complete
        self._duration = duration
        self._elapsed: float = 0.0
        self._font: pygame.font.Font | None = None
        self._small_font: pygame.font.Font | None = None

    def on_enter(self) -> None:
        """Initialise fonts and start timer."""
        self._font = pygame.font.SysFont("consolas", config.FONT_SIZE)
        self._small_font = pygame.font.SysFont("consolas", config.FONT_SIZE_SMALL)
        self._elapsed = 0.0

    def handle_event(self, event: pygame.event.Event) -> None:
        """Allow skipping the transition with any key."""
        if event.type == pygame.KEYDOWN or (
            event.type == pygame.MOUSEBUTTONDOWN and event.button == 1
        ):
            self._elapsed = self._duration

    def update(self, dt: float) -> None:
        """Advance the transition timer."""
        self._elapsed += dt
        if self._elapsed >= self._duration and self.on_complete is not None:
            self.on_complete()

    def render(self) -> None:
        """Draw the transition text with fade-in effect."""
        surface = self.display
        font = self._font
        small_font = self._small_font
        assert font is not None
        assert small_font is not None

        w, h = surface.get_size()
        progress = min(1.0, self._elapsed / self._duration)

        # Background: near-black
        surface.fill(config.COLOR_BG)

        # Static noise overlay (fades out)
        if progress < 0.5:
            import random

            noise_alpha = int(128 * (1 - progress * 2))
            for _ in range(noise_alpha // 2):
                x = random.randint(0, w - 1)
                y = random.randint(0, h - 1)
                surface.set_at(
                    (x, y),
                    (
                        random.randint(0, 40),
                        random.randint(0, 60),
                        random.randint(0, 20),
                    ),
                )

        # Fade-in text
        alpha_text = min(1.0, progress * 3)
        text_col = tuple(int(c * alpha_text) for c in config.PHOSPHOR_GREEN)

        lines = self._transition_text.split("\n")
        total_height = len(lines) * (font.get_height() + 8)
        y_start = (h - total_height) // 2

        for i, line in enumerate(lines):
            if line.startswith(">"):
                col = text_col
                f = font
            else:
                col = tuple(int(c * alpha_text * 0.7) for c in config.PHOSPHOR_DIM)
                f = small_font
            surf = f.render(line, True, col)
            x = (w - surf.get_width()) // 2
            surface.blit(surf, (x, y_start + i * (f.get_height() + 8)))

        # Progress bar at bottom
        bar_w = 200
        bar_h = 4
        bar_x = (w - bar_w) // 2
        bar_y = h - 60
        pygame.draw.rect(surface, config.PHOSPHOR_DIM, (bar_x, bar_y, bar_w, bar_h))
        fill_w = int(bar_w * progress)
        pygame.draw.rect(surface, config.PHOSPHOR_GREEN, (bar_x, bar_y, fill_w, bar_h))
