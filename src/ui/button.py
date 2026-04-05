"""Terminal-styled button — clickable text with hover state.

Buttons are displayed as numbered CLI commands (e.g. ``[1] NEW
DEPLOYMENT``) or bracketed labels (e.g. ``[EXECUTE]``).  Hover
brightens the text; click triggers an action callback.
"""

from __future__ import annotations

from collections.abc import Callable

import pygame

from src import config


class TerminalButton:
    """A clickable terminal-style button.

    The button label is rendered as-is (brackets are part of the label
    string, not added automatically).  Hover state brightens the text.
    An optional keyboard shortcut (integer key code) can activate the
    button via keyboard input.
    """

    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        label: str,
        on_click: Callable[[], None],
        key: int | None = None,
        enabled: bool = True,
    ) -> None:
        """Create a TerminalButton.

        Args:
            x: Left edge in pixels.
            y: Top edge in pixels.
            width: Button width in pixels (text is left-aligned inside).
            height: Button height in pixels.
            label: The text to display (include brackets if desired).
            on_click: Callback invoked when the button is activated.
            key: Optional Pygame key code for keyboard shortcut
                (e.g. ``pygame.K_1``).
            enabled: If ``False``, the button is rendered dimmed and
                does not respond to input.
        """
        self.rect = pygame.Rect(x, y, width, height)
        self.label = label
        self.on_click = on_click
        self.key = key
        self._enabled = enabled
        self.hovered = False

    # ------------------------------------------------------------------
    # State
    # ------------------------------------------------------------------

    @property
    def enabled(self) -> bool:
        """Whether the button responds to input."""
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool) -> None:
        self._enabled = value
        if not value:
            self.hovered = False

    # ------------------------------------------------------------------
    # Interaction
    # ------------------------------------------------------------------

    def contains(self, pos: tuple[int, int] | None) -> bool:
        """Return ``True`` if the position is inside the button."""
        if pos is None:
            return False
        return self.rect.collidepoint(pos)

    def set_hover(self, pos: tuple[int, int] | None) -> None:
        """Update hover state based on mouse position."""
        if not self.enabled:
            self.hovered = False
            return
        self.hovered = self.contains(pos)

    def click(self) -> bool:
        """Activate the button if enabled and hovered.

        Returns:
            ``True`` if the on_click callback was invoked.
        """
        if not self.enabled:
            return False
        if self.hovered:
            self.on_click()
            return True
        return False

    def press_key(self, key: int) -> bool:
        """Activate the button via keyboard shortcut.

        Args:
            key: The Pygame key code that was pressed.

        Returns:
            ``True`` if this button's shortcut matched and fired.
        """
        if not self.enabled:
            return False
        if self.key is not None and key == self.key:
            self.on_click()
            return True
        return False

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def render(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        """Draw the button label onto the surface.

        Colour is bright green when hovered, normal green when enabled
        but not hovered, and grey when disabled.

        Args:
            surface: Target surface.
            font: Font to render the label with.
        """
        if not self.enabled:
            colour = config.COLOR_DISABLED
        elif self.hovered:
            colour = config.PHOSPHOR_BRIGHT
        else:
            colour = config.PHOSPHOR_GREEN

        surf = font.render(self.label, True, colour)
        # Center vertically, left-align with padding
        px = self.rect.left + 8
        py = self.rect.top + (self.rect.height - surf.get_height()) // 2
        surface.blit(surf, (px, py))
