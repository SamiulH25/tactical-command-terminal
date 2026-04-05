"""Game Over screen — signal lost notification.

Lore-accurate format::

    > FSA-TD-47                                       CH:01 // LINK ACTIVE
    ════════════════════════════════════════════════════════════════════
    ────────────────────────────────────────────────────────────────────

    > SIGNAL LOST
      UNIT LOST IN ACTION

      FLOORS CLEARED:     03
      FINAL POSITION:     GRID 14,07

      No extraction available. Another coordinator needed.

      [REDEPLOY]    [RETURN TO BASE]
"""

from __future__ import annotations

import pygame

from src import config
from src.core.terminal import TerminalRenderer
from src.screens.base_screen import Screen
from src.systems.combat import CombatState
from src.ui.button import TerminalButton
from src.ui.layout import refresh, sx, sy
from src.ui.text import coord, pad


class GameOverScreen(Screen):
    """The defeat screen shown when all friendly mechs are destroyed."""

    def __init__(
        self,
        renderer: TerminalRenderer,
        combat_state: CombatState,
        floors_cleared: int = 0,
    ) -> None:
        """Create the GameOverScreen.

        Args:
            renderer: The CRT terminal renderer.
            combat_state: The final combat state.
            floors_cleared: Number of floors completed before this fight.
        """
        super().__init__(renderer)
        self._combat = combat_state
        self._floors_cleared = floors_cleared
        self._font: pygame.font.Font | None = None
        self._small_font: pygame.font.Font | None = None
        self._mouse_pos: tuple[int, int] | None = None
        self._btn_redeploy: TerminalButton | None = None
        self._btn_return: TerminalButton | None = None

    def on_enter(self) -> None:
        """Initialise fonts and layout."""
        self._font = pygame.font.SysFont("consolas", config.FONT_SIZE)
        self._small_font = pygame.font.SysFont("consolas", config.FONT_SIZE_SMALL)
        refresh(self.display)
        w, _h = self.display.get_size()
        btn_w = sx(180)
        btn_h = sy(40)
        btn_y = sy(420)
        gap = sx(20)
        total_w = btn_w * 2 + gap
        btn_x = (w - total_w) // 2
        self._btn_redeploy = TerminalButton(
            btn_x,
            btn_y,
            btn_w,
            btn_h,
            "[REDEPLOY]",
            on_click=self._on_redeploy,
        )
        self._btn_return = TerminalButton(
            btn_x + btn_w + gap,
            btn_y,
            sx(220),
            btn_h,
            "[RETURN TO BASE]",
            on_click=self._on_return,
        )

    def _on_redeploy(self) -> None:
        """Placeholder: restart the current floor."""
        pass

    def _on_return(self) -> None:
        """Placeholder: return to main menu."""
        pass

    def handle_event(self, event: pygame.event.Event) -> None:
        """Handle mouse clicks."""
        if event.type == pygame.MOUSEMOTION:
            self._mouse_pos = event.pos
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._mouse_pos = event.pos
            for btn in (self._btn_redeploy, self._btn_return):
                if btn:
                    btn.set_hover(self._mouse_pos)
                    btn.click()

    def update(self, dt: float) -> None:
        """Update hover."""
        for btn in (self._btn_redeploy, self._btn_return):
            if btn:
                btn.set_hover(self._mouse_pos)

    def render(self) -> None:
        """Draw the game over screen."""
        surface = self.display
        font = self._font
        small_font = self._small_font
        assert font is not None
        assert small_font is not None

        refresh(surface)
        w, _h = surface.get_size()

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

        # === SIGNAL LOST header (red — COLOR_ENEMY) ===
        title = font.render("> SIGNAL LOST", True, config.COLOR_ENEMY)
        tx = (w - title.get_width()) // 2
        surface.blit(title, (tx, sy(80)))

        subtitle = font.render("UNIT LOST IN ACTION", True, config.COLOR_ENEMY)
        surface.blit(subtitle, (tx, sy(110)))

        # === Divider ===
        pygame.draw.line(
            surface,
            config.COLOR_ENEMY,
            (sx(200), sy(140)),
            (w - sx(200), sy(140)),
        )

        # === Stats ===
        stats = [
            ("FLOORS CLEARED:", self._floors_cleared, 4),
        ]
        y = sy(160)
        for label, value, width in stats:
            line = f"  {label:<22s} {pad(value, width)}"
            surf = font.render(line, True, config.PHOSPHOR_GREEN)
            surface.blit(surf, (w // 2 - surf.get_width() // 2, y))
            y += sy(28)

        # Final position (from last surviving friendly or default)
        final_pos = coord(14, 7)
        pos_surf = font.render(
            f"  {'FINAL POSITION:':<22s} {final_pos}",
            True,
            config.PHOSPHOR_DIM,
        )
        surface.blit(pos_surf, (w // 2 - pos_surf.get_width() // 2, y))
        y += sy(28)

        # === Narrative ===
        nar_text = "No extraction available. Another coordinator needed."
        nar_surf = small_font.render(nar_text, True, config.PHOSPHOR_DIM)
        surface.blit(nar_surf, (w // 2 - nar_surf.get_width() // 2, y + sy(30)))

        # === Buttons (side by side) ===
        if self._btn_redeploy:
            self._btn_redeploy.render(surface, font)
        if self._btn_return:
            self._btn_return.render(surface, font)
