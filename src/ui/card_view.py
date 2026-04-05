"""Directive (card) view — terminal-formatted tactical order display.

Directives are rendered as command-line entries rather than playing cards,
reinforcing the degraded command terminal aesthetic.

Lore-accurate format::

    > DIRECTIVE: AUTOCANNON BURST
      TYPE: ATTACK | DMG: 06 | OL: 02
      [EXECUTE]
"""

from __future__ import annotations

from typing import ClassVar

import pygame

from src import config
from src.models.card import Directive, DirectiveType
from src.ui.text import pad


class DirectiveView:
    """A single directive rendered as a terminal command entry.

    Hover highlights the entry and shows additional telemetry
    (range, pattern, keywords) as a tooltip.
    """

    # Type colour mapping — terminal-appropriate
    _TYPE_COLOUR: ClassVar[dict[DirectiveType, tuple[int, int, int]]] = {
        DirectiveType.COMBAT: config.COLOR_ENEMY,
        DirectiveType.MOVEMENT: config.COLOR_FRIENDLY,
        DirectiveType.REPAIR: config.PHOSPHOR_GREEN,
        DirectiveType.UTILITY: config.COLOR_WARNING,
    }

    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        directive: Directive,
        weapon_bonus: int = 0,
        ol_discount: int = 0,
    ) -> None:
        """Create a DirectiveView.

        Args:
            x: Left edge in pixels.
            y: Top edge in pixels.
            width: Directive entry width.
            directive: The directive to display.
            weapon_bonus: Flat damage bonus from equipment/pilot.
            ol_discount: Overload reduction from equipment.
        """
        self.rect = pygame.Rect(x, y, width, 54)
        self.directive = directive
        self.weapon_bonus = weapon_bonus
        self.ol_discount = ol_discount
        self.hovered = False

    # ------------------------------------------------------------------
    # Interaction
    # ------------------------------------------------------------------

    def contains(self, pos: tuple[int, int] | None) -> bool:
        """Check whether a position is inside the directive area."""
        if pos is None:
            return False
        return self.rect.collidepoint(pos)

    def set_hover(self, pos: tuple[int, int] | None) -> None:
        """Update hover state from mouse position."""
        self.hovered = self.contains(pos)

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def _type_label(self) -> str:
        """Short type label for the directive."""
        labels: dict[DirectiveType, str] = {
            DirectiveType.COMBAT: "ATTACK",
            DirectiveType.MOVEMENT: "MOVE",
            DirectiveType.REPAIR: "REPAIR",
            DirectiveType.UTILITY: "UTILITY",
        }
        return labels.get(self.directive.directive_type, "UNKNOWN")

    def render(
        self,
        surface: pygame.Surface,
        font: pygame.font.Font,
        small_font: pygame.font.Font,
    ) -> None:
        """Draw the directive entry in terminal style.

        Args:
            surface: Target surface.
            font: Font for the directive name.
            small_font: Smaller font for telemetry details.
        """
        d = self.directive
        type_col = self._TYPE_COLOUR.get(d.directive_type, config.PHOSPHOR_GREEN)
        text_col = config.PHOSPHOR_BRIGHT if self.hovered else config.PHOSPHOR_GREEN
        dim_col = config.PHOSPHOR_DIM

        bg_col = config.COLOR_PANEL_BG
        if self.hovered:
            # Slight highlight
            bg_col = (8, 18, 6)
        bg_surf = pygame.Surface((self.rect.width, self.rect.height))
        bg_surf.fill(bg_col)
        surface.blit(bg_surf, self.rect.topleft)

        # Line 1: > DIRECTIVE: NAME
        line1 = f"> DIRECTIVE: {d.name.upper()}"
        name_surf = font.render(line1, True, text_col)
        surface.blit(name_surf, (self.rect.left + 6, self.rect.top + 2))

        # Line 2: TYPE: x | DMG: xx | OL: xx
        dmg = d.effective_damage(self.weapon_bonus)
        ol = d.effective_ol_cost(self.ol_discount)
        type_label = self._type_label()
        line2 = f"  TYPE: {type_label} | DMG: {pad(dmg)} | OL: {pad(ol)}"
        if d.range_ > 0:
            line2 += f" | RNG: {pad(d.range_)}"
        line2_surf = small_font.render(line2, True, dim_col)
        surface.blit(line2_surf, (self.rect.left + 6, self.rect.top + 20))

        # Line 3: [EXECUTE] with type-colour brackets
        exec_text = "EXECUTE"
        bracket_surf = small_font.render("[", True, type_col)
        cmd_surf = small_font.render(exec_text, True, text_col)
        bracket2_surf = small_font.render("]", True, type_col)
        bx = self.rect.left + 6
        by = self.rect.top + 36
        surface.blit(bracket_surf, (bx, by))
        surface.blit(cmd_surf, (bx + bracket_surf.get_width(), by))
        bx2 = bx + bracket_surf.get_width() + cmd_surf.get_width()
        surface.blit(bracket2_surf, (bx2, by))

        # Hover tooltip
        if self.hovered and d.keywords:
            kw = ", ".join(sorted(d.keywords))
            kw_surf = small_font.render(f"  KEYWORDS: {kw}", True, dim_col)
            surface.blit(kw_surf, (bx2 + bracket2_surf.get_width() + 8, by))
