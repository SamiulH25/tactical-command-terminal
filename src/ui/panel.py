"""Terminal-styled panel — a bordered window with an optional title.

Panels are the fundamental UI container.  Every piece of content is
rendered inside a panel with thin green borders and a ``>`` prefixed
title line.  No rounded corners, no gradients — pure box geometry.
"""

from __future__ import annotations

import pygame

from src import config

# Thin single-pixel box-drawing characters for the border.
_CORNER_TL = "+"
_CORNER_TR = "+"
_CORNER_BL = "+"
_CORNER_BR = "+"
_HORIZ = "-"
_VERT = "|"


class Panel:
    """A rectangular bordered panel with an optional title.

    The panel draws a thin single-character border and renders the title
    on the top line with the canonical ``>`` prefix.
    """

    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        title: str = "",
    ) -> None:
        """Create a Panel.

        Args:
            x: Left edge in pixels.
            y: Top edge in pixels.
            width: Panel width in pixels.
            height: Panel height in pixels.
            title: Optional title text (rendered without ``>`` prefix —
                the prefix is added automatically).
        """
        self.rect = pygame.Rect(x, y, width, height)
        self.title = title

    def render(
        self,
        surface: pygame.Surface,
        font: pygame.font.Font,
        title_font: pygame.font.Font | None = None,
    ) -> None:
        """Draw the panel border and title.

        Args:
            surface: Target surface to draw on.
            font: Default font for the border characters.
            title_font: Optional larger font for the title.
                Falls back to *font* if not provided.
        """
        border_colour = config.PHOSPHOR_GREEN
        tf = title_font if title_font is not None else font

        # --- Border lines ---
        left = self.rect.left
        right = self.rect.right - 1
        top = self.rect.top
        bottom = self.rect.bottom - 1

        # Top and bottom edges
        for px in range(left, right + 1):
            surface.set_at((px, top), border_colour)
            surface.set_at((px, bottom), border_colour)
        # Left and right edges
        for py in range(top, bottom + 1):
            surface.set_at((left, py), border_colour)
            surface.set_at((right, py), border_colour)
        # Corners
        for px, py in [(left, top), (right, top), (left, bottom), (right, bottom)]:
            surface.set_at((px, py), border_colour)

        # --- Title ---
        if self.title:
            display_title = f"> {self.title}"
            title_surf = tf.render(display_title, True, border_colour)
            # Center the title horizontally, positioned just below top border
            tx = left + (self.rect.width - title_surf.get_width()) // 2
            ty = top + 4
            surface.blit(title_surf, (tx, ty))
