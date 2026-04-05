"""Victory screen — operational report shown after clearing a floor.

Lore-accurate format::

    > FSA-TD-47                                       CH:01 // LINK ACTIVE
    ════════════════════════════════════════════════════════════════════
    ────────────────────────────────────────────────────────────────────

    > MISSION COMPLETE
      OPERATIONAL REPORT

      FLOORS CLEARED:     05
      ENEMIES DEFEATED:   023
      CARDS PLAYED:       187
      CREDITS EARNED:     0450
      CASUALTIES:         001

      OUTPOST ALPHA CLEARED. First base down.

      [RETURN TO BASE]
"""

from __future__ import annotations

import pygame

from src import config
from src.core.terminal import TerminalRenderer
from src.models.campaign import Campaign
from src.screens.base_screen import Screen
from src.systems.combat import CombatResult
from src.ui.button import TerminalButton
from src.ui.layout import refresh, sx, sy
from src.ui.text import pad


class VictoryScreen(Screen):
    """The mission complete screen shown after winning a combat."""

    def __init__(
        self,
        renderer: TerminalRenderer,
        campaign: Campaign,
        result: CombatResult,
    ) -> None:
        """Create the VictoryScreen.

        Args:
            renderer: The CRT terminal renderer.
            campaign: Current campaign state (for outpost name, etc.).
            result: The combat result with statistics.
        """
        super().__init__(renderer)
        self._campaign = campaign
        self._result = result
        self._font: pygame.font.Font | None = None
        self._small_font: pygame.font.Font | None = None
        self._mouse_pos: tuple[int, int] | None = None
        self._btn: TerminalButton | None = None

    def on_enter(self) -> None:
        """Initialise fonts and layout."""
        self._font = pygame.font.SysFont("consolas", config.FONT_SIZE)
        self._small_font = pygame.font.SysFont("consolas", config.FONT_SIZE_SMALL)
        refresh(self.display)
        w, _h = self.display.get_size()
        btn_w = sx(280)
        btn_h = sy(40)
        btn_x = (w - btn_w) // 2
        btn_y = sy(450)
        self._btn = TerminalButton(
            btn_x,
            btn_y,
            btn_w,
            btn_h,
            "[RETURN TO BASE]",
            on_click=self._on_return,
        )

    def _on_return(self) -> None:
        """Placeholder: return to ship menu."""
        pass

    def handle_event(self, event: pygame.event.Event) -> None:
        """Handle mouse clicks."""
        if event.type == pygame.MOUSEMOTION:
            self._mouse_pos = event.pos
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._mouse_pos = event.pos
            if self._btn:
                self._btn.set_hover(self._mouse_pos)
                self._btn.click()

    def update(self, dt: float) -> None:
        """Update hover."""
        if self._btn:
            self._btn.set_hover(self._mouse_pos)

    def render(self) -> None:
        """Draw the victory screen."""
        surface = self.display
        font = self._font
        small_font = self._small_font
        assert font is not None
        assert small_font is not None
        assert self._btn is not None

        refresh(surface)
        w, _h = surface.get_size()
        c = self._campaign
        r = self._result

        # === Top bezel — match MainMenu style ===
        left = font.render("> FSA-TD-47", True, config.PHOSPHOR_GREEN)
        right = font.render("CH:01 // LINK ACTIVE", True, config.PHOSPHOR_DIM)
        surface.blit(left, (sx(40), sy(20)))
        surface.blit(right, (w - right.get_width() - sx(40), sy(20)))

        # Thick + thin divider
        pygame.draw.line(
            surface,
            config.PHOSPHOR_GREEN,
            (sx(40), sy(50)),
            (w - sx(40), sy(50)),
            2,
        )
        pygame.draw.line(
            surface,
            config.PHOSPHOR_DIM,
            (sx(40), sy(56)),
            (w - sx(40), sy(56)),
        )

        # === Header ===
        title = font.render("> MISSION COMPLETE", True, config.PHOSPHOR_GREEN)
        tx = (w - title.get_width()) // 2
        surface.blit(title, (tx, sy(80)))

        subtitle = font.render("OPERATIONAL REPORT", True, config.PHOSPHOR_DIM)
        surface.blit(subtitle, (tx, sy(110)))

        # === Divider ===
        pygame.draw.line(
            surface,
            config.PHOSPHOR_GREEN,
            (sx(200), sy(145)),
            (w - sx(200), sy(145)),
        )

        # === Stats ===
        stats = [
            ("FLOORS CLEARED:", c.floors_cleared, 4),
            ("ENEMIES DEFEATED:", r.enemies_defeated, 3),
            ("CARDS PLAYED:", r.cards_played, 3),
            ("CREDITS EARNED:", r.current_credits_earned, 4),
            ("CASUALTIES:", c.casualties, 3),
        ]
        y = sy(165)
        for label, value, width in stats:
            line = f"  {label:<22s} {pad(value, width)}"
            surf = font.render(line, True, config.PHOSPHOR_GREEN)
            surface.blit(surf, (w // 2 - surf.get_width() // 2, y))
            y += sy(28)

        # === Narrative text ===
        outpost_text = f"{c.outpost_name} CLEARED. First base down."
        nar_surf = small_font.render(outpost_text, True, config.PHOSPHOR_DIM)
        surface.blit(nar_surf, (w // 2 - nar_surf.get_width() // 2, y + sy(20)))

        # === Button ===
        self._btn.render(surface, font)
