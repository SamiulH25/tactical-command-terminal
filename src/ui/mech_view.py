"""Mech status view — renders mech HP/OL bars, IFF symbol, and status tags.

The view shows everything a Coordinator needs to know about a single mech
on the tactical display: callsign, HP bar, OL bar, status tag, and the
geometric IFF symbol that identifies it on the grid.
"""

from __future__ import annotations

import pygame

from src import config
from src.models.faction import FACTION_COLOUR
from src.models.mech import DeployedMech
from src.ui.text import ratio_bar, status_tag

# Unicode IFF symbol characters keyed by IffShape name
_IFF_SYMBOLS: dict[str, str] = {
    "SQUARE": "\u25c8",  # ◇
    "DIAMOND": "\u25c6",  # ◆
    "HEXAGON": "\u2b22",  # ⬢
    "CIRCLE_CROSS": "\u25c9",  # ◉
    "CHEVRON": "\u27e9",  # ⟩
    "TRIANGLE": "\u25b2",  # ▲
    "RECTANGLE": "\u25ac",  # ▬
    "CIRCLE": "\u25cf",  # ●
    "CROSS": "\u271b",  # ✛
}


class MechView:
    """A compact mech status panel for the HUD or ship menu.

    Renders as::

        ◈ ALPHA-1    HP: ████████████████░░░░  025/030  [ACTIVE]
                     OL: ████░░░░░░░░░░░░░░░░  04/012
    """

    def __init__(
        self,
        x: int,
        y: int,
        mech: DeployedMech,
        callsign: str | None = None,
        friendly: bool = True,
    ) -> None:
        """Create a MechView.

        Args:
            x: Left edge in pixels.
            y: Top edge in pixels.
            mech: The deployed mech to display.
            callsign: Override callsign.  Defaults to ``mech.pilot_callsign``.
            friendly: If ``True``, colour the IFF symbol cyan/green;
                if ``False``, colour it red (hostile).
        """
        self.rect = pygame.Rect(x, y, 420, 48)
        self.mech = mech
        self.callsign = callsign if callsign is not None else mech.pilot_callsign
        self.friendly = friendly

    def _iff_symbol_text(self) -> str:
        """Return the geometric IFF symbol character."""
        return _IFF_SYMBOLS.get(self.mech.frame.iff_shape.name, "\u25c6")

    def _iff_colour(self) -> tuple[int, int, int]:
        """Return the display colour for the IFF symbol."""
        if not self.friendly:
            return config.COLOR_ENEMY
        return FACTION_COLOUR.get(self.mech.frame.faction, config.PHOSPHOR_GREEN)

    def render(
        self,
        surface: pygame.Surface,
        font: pygame.font.Font,
        small_font: pygame.font.Font,
    ) -> None:
        """Draw the mech status panel.

        Args:
            surface: Target surface.
            font: Primary font for callsign and values.
            small_font: Smaller font for labels.
        """
        text_col = config.PHOSPHOR_GREEN if self.friendly else config.COLOR_ENEMY

        # --- IFF Symbol ---
        iff_sym = self._iff_symbol_text()
        iff_col = self._iff_colour()
        sym_surf = font.render(iff_sym, True, iff_col)
        surface.blit(sym_surf, (self.rect.left + 4, self.rect.top + 2))

        # --- Callsign ---
        callsign_surf = font.render(self.callsign, True, text_col)
        surface.blit(callsign_surf, (self.rect.left + 28, self.rect.top + 2))

        # --- HP bar ---
        hp_bar = ratio_bar(self.mech.current_hp, self.mech.max_hp)
        hp_text = f"HP: {hp_bar}  {self.mech.current_hp:03d}/{self.mech.max_hp:03d}"
        hp_surf = small_font.render(hp_text, True, text_col)
        surface.blit(hp_surf, (self.rect.left + 4, self.rect.top + 22))

        # --- OL bar ---
        ol_bar = ratio_bar(self.mech.max_ol - self.mech.current_ol, self.mech.max_ol)
        ol_text = f"OL: {ol_bar}  {self.mech.current_ol:02d}/{self.mech.max_ol:02d}"
        ol_surf = small_font.render(ol_text, True, config.COLOR_WARNING)
        surface.blit(ol_surf, (self.rect.left + 4, self.rect.top + 36))

        # --- Status tag ---
        tag = status_tag(self.mech.current_hp, self.mech.max_hp)
        tag_col = config.PHOSPHOR_GREEN
        if tag == "[CRITICAL]":
            tag_col = config.COLOR_WARNING
        elif tag == "[OFFLINE]":
            tag_col = config.COLOR_DISABLED
        tag_surf = small_font.render(tag, True, tag_col)
        tag_x = self.rect.right - tag_surf.get_width() - 4
        surface.blit(tag_surf, (tag_x, self.rect.top + 2))
