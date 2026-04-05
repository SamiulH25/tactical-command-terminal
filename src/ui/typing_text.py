"""Typewriter text — character-by-character reveal animation.

Renders text one character at a time at a configurable speed.
Optionally skippable by clicking or pressing any key.

Lore framing:  Terminal text arrives over a degraded comm link,
so characters appear one at a time rather than all at once.
"""

from __future__ import annotations

import pygame

from src import config


class TypingText:
    """A text surface that reveals characters over time.

    Usage::

        tt = TypingText("Hello Coordinator", font, max_width=400)
        # Each frame:
        tt.update(dt)
        tt.render(surface, x, y)
        if tt.finished:
            ...  # animation complete
    """

    def __init__(
        self,
        text: str,
        font: pygame.font.Font,
        colour: tuple[int, int, int] = config.PHOSPHOR_GREEN,
        chars_per_second: float = 40.0,
        max_width: int = 0,
        skippable: bool = True,
    ) -> None:
        """Create a TypingText instance.

        Args:
            text: The full text to reveal.
            font: Font to render with.
            colour: Text colour.
            chars_per_second: How many characters appear per second.
            max_width: If > 0, wrap lines to this width.
            skippable: If ``True``, clicking or pressing a key reveals
                all text instantly.
        """
        self._full_text = text
        self._font = font
        self._colour = colour
        self._speed = max(chars_per_second, 0.0)
        self._skippable = skippable
        self._elapsed: float = 0.0
        self._done: bool = self._speed <= 0.0
        self._surface: pygame.Surface | None = None
        self._rendered_lines: list[pygame.Surface] = []
        self._line_ys: list[int] = []
        self._total_height: int = 0

        # Build wrapped lines
        self._wrapped_lines: list[str] = (
            self._wrap_text(text, font, max_width) if max_width > 0 else text.split("\n")
        )

        # Total character count across all lines (no newline chars)
        self._total_chars = sum(len(line) for line in self._wrapped_lines)
        self._duration = self._total_chars / self._speed if self._speed > 0 else 0.0

    @property
    def finished(self) -> bool:
        """Whether all characters have been revealed."""
        return self._done

    @property
    def progress(self) -> float:
        """Reveal progress from 0.0 to 1.0."""
        if self._duration <= 0:
            return 1.0
        return min(1.0, self._elapsed / self._duration)

    def update(self, dt: float) -> None:
        """Advance the reveal timer.

        Args:
            dt: Delta time in seconds.
        """
        if self._done:
            return
        self._elapsed += dt
        if self._elapsed >= self._duration:
            self._done = True
            self._surface = None  # Force full re-render

    def skip(self) -> None:
        """Instantly reveal all remaining text."""
        if not self._skippable:
            return
        self._done = True
        self._surface = None

    def render(
        self,
        surface: pygame.Surface,
        x: int,
        y: int,
    ) -> pygame.Rect:
        """Render the currently revealed text.

        Args:
            surface: Target surface.
            x: Left edge in pixels.
            y: Top edge in pixels.

        Returns:
            The bounding rect of the rendered text block.
        """
        if self._done and self._surface is not None:
            surface.blit(self._surface, (x, y))
            return self._surface.get_rect(topleft=(x, y))

        # Determine how many characters to show
        chars_to_show = int(self._elapsed * self._speed)
        chars_to_show = min(chars_to_show, self._total_chars)

        # Rebuild surfaces if the reveal amount changed
        if self._surface is None or self._done:
            self._rendered_lines = []
            self._line_ys = []
            remaining = chars_to_show
            line_height = self._font.get_height() + 2
            total_w = 0

            for i, line in enumerate(self._wrapped_lines):
                if remaining <= 0:
                    self._rendered_lines.append(self._font.render("", True, self._colour))
                elif remaining >= len(line):
                    s = self._font.render(line, True, self._colour)
                    self._rendered_lines.append(s)
                    remaining -= len(line)
                    total_w = max(total_w, s.get_width())
                else:
                    s = self._font.render(line[:remaining], True, self._colour)
                    self._rendered_lines.append(s)
                    remaining = 0
                    total_w = max(total_w, s.get_width())

                self._line_ys.append(y + i * line_height)

            self._total_height = (
                len(self._wrapped_lines) * line_height - 2 if self._wrapped_lines else 0
            )

            # If done, cache the full surface
            if self._done:
                self._surface = pygame.Surface((total_w, self._total_height), pygame.SRCALPHA)
                for s, ly in zip(self._rendered_lines, self._line_ys, strict=False):
                    self._surface.blit(s, (0, ly - y))
                return self._surface.get_rect(topleft=(x, y))

        # Blit each line
        total_w = 0
        for s, ly in zip(self._rendered_lines, self._line_ys, strict=False):
            surface.blit(s, (x, ly))
            total_w = max(total_w, s.get_width())

        return pygame.Rect(x, y, total_w, self._total_height)

    def handle_event(self, event: pygame.event.Event) -> None:
        """Allow skipping on click or keypress."""
        if not self._skippable or self._done:
            return
        if event.type == pygame.KEYDOWN or (
            event.type == pygame.MOUSEBUTTONDOWN and event.button == 1
        ):
            self.skip()

    @staticmethod
    def _wrap_text(
        text: str,
        font: pygame.font.Font,
        max_width: int,
    ) -> list[str]:
        """Simple word-wrap a string to fit within *max_width* pixels."""
        wrapped: list[str] = []
        for paragraph in text.split("\n"):
            words = paragraph.split(" ")
            current_line = ""
            for word in words:
                test = current_line + (" " if current_line else "") + word
                if font.size(test)[0] <= max_width:
                    current_line = test
                else:
                    if current_line:
                        wrapped.append(current_line)
                    current_line = word
            if current_line:
                wrapped.append(current_line)
        return wrapped if wrapped else [text]
