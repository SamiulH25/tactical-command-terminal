"""War comms widget — scrolling tactical feed with typewriter effect.

Displays war effort comms on any screen.  Messages appear one character
at a time using the TypingText effect, then scroll upward as new
messages arrive.  All text is clipped to the widget bounds.
"""

from __future__ import annotations

import pygame

from src import config
from src.systems.war_comms import get_random_comms
from src.ui.typing_text import TypingText

# Maximum messages visible at once (not including the typing line)
_MAX_VISIBLE = 3
# Seconds between new comms messages
_COMMS_INTERVAL = 12.0
# Typing speed — chars per second (slow, deliberate terminal feel)
_TYPE_SPEED = 12.0


class WarCommsWidget:
    """A scrolling war effort comms feed with typewriter effect."""

    def __init__(self) -> None:
        self._messages: list[str] = []  # Completed messages
        self._typing: TypingText | None = None
        self._typing_text: str = ""
        self._timer: float = 0.0
        self._small_font: pygame.font.Font | None = None

    def set_fonts(self, font: pygame.font.Font, small_font: pygame.font.Font) -> None:
        """Set the fonts used for rendering."""
        self._small_font = small_font

    def update(self, dt: float) -> None:
        """Advance the typewriter and check for new messages."""
        self._timer += dt

        # Update typing text
        if self._typing is not None:
            self._typing.update(dt)
            if self._typing.finished:
                self._messages.append(self._typing_text)
                self._typing = None
                self._typing_text = ""
                # Trim old messages
                if len(self._messages) > _MAX_VISIBLE:
                    self._messages = self._messages[-_MAX_VISIBLE:]

        # Check if we should start a new message
        if self._typing is None and self._timer >= _COMMS_INTERVAL:
            self._timer = 0.0
            self._start_new_message()

    def _start_new_message(self) -> None:
        """Begin typing a new comm message."""
        if self._small_font is None:
            return
        text = get_random_comms()
        self._typing_text = text
        self._typing = TypingText(
            text,
            self._small_font,
            colour=config.PHOSPHOR_DIM,
            chars_per_second=_TYPE_SPEED,
            max_width=0,  # No wrapping
        )

    def render(
        self,
        surface: pygame.Surface,
        x: int,
        y: int,
        width: int,
        height: int,
    ) -> None:
        """Render the comms feed, clipped to the given bounds."""
        if self._small_font is None:
            return

        # Clip rendering to widget bounds
        clip_rect = pygame.Rect(x, y, width, height)
        prev_clip = surface.get_clip()
        surface.set_clip(clip_rect)

        # Background panel
        bg_surf = pygame.Surface((width, height), pygame.SRCALPHA)
        bg_surf.fill((5, 8, 3, 200))
        surface.blit(bg_surf, (x, y))
        pygame.draw.rect(surface, config.PHOSPHOR_DIM, (x, y, width, height), 1)

        # Title
        title_surf = self._small_font.render("> WAR EFFORT FEED", True, config.PHOSPHOR_GREEN)
        surface.blit(title_surf, (x + 6, y + 4))

        # Divider line under title
        title_bottom = y + 20
        pygame.draw.line(
            surface, config.PHOSPHOR_DIM, (x + 6, title_bottom), (x + width - 6, title_bottom)
        )

        # Messages start below the divider with padding
        line_h = self._small_font.get_height() + 4
        content_y = title_bottom + 8

        # Completed messages (oldest at top)
        visible_msgs = self._messages[-_MAX_VISIBLE:]
        max_chars = max(20, (width - 20) // 8)  # Aggressive truncation
        for i, text in enumerate(visible_msgs):
            display_text = text
            if len(text) > max_chars:
                display_text = text[: max_chars - 3] + "..."
            msg_surf = self._small_font.render(display_text, True, config.PHOSPHOR_DIM)
            surface.blit(msg_surf, (x + 6, content_y + i * line_h))

        # Currently typing message (below completed messages)
        if self._typing is not None:
            typing_y = content_y + len(visible_msgs) * line_h
            # Check if there's room
            if typing_y + line_h <= y + height - 4:
                self._typing.render(surface, x + 6, typing_y)

        # Restore previous clip
        surface.set_clip(prev_clip)
