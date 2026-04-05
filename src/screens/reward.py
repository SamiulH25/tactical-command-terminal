"""Post-combat reward screen — card pick and credit allocation.

After winning a combat encounter, the Coordinator is offered rewards:
- Credits added to the campaign pool.
- A choice of 3 new directives to add to the deck.

Lore framing:  Salvaged enemy telemetry data reveals new tactical
protocols that can be integrated into your command directives.
"""

from __future__ import annotations

from collections.abc import Callable

import pygame

from src import config
from src.core.terminal import TerminalRenderer
from src.models.campaign import Campaign
from src.models.card import Directive
from src.screens.base_screen import Screen
from src.ui.button import TerminalButton
from src.ui.panel import Panel
from src.ui.text import pad


class RewardScreen(Screen):
    """The post-combat reward selection screen."""

    def __init__(
        self,
        renderer: TerminalRenderer,
        campaign: Campaign,
        card_choices: list[Directive],
        credits_earned: int,
        on_confirm: Callable[[], None] | None = None,
    ) -> None:
        """Create the RewardScreen.

        Args:
            renderer: The CRT terminal renderer.
            campaign: Current campaign state.
            card_choices: 3 directives to choose from.
            credits_earned: Credits awarded from this combat.
            on_confirm: Callback when the player confirms their choice.
        """
        super().__init__(renderer)
        self._campaign = campaign
        self._card_choices = card_choices
        self._credits_earned = credits_earned
        self.on_confirm = on_confirm
        self._font: pygame.font.Font | None = None
        self._small_font: pygame.font.Font | None = None
        self._mouse_pos: tuple[int, int] | None = None
        self._selected_index: int = 0
        self._buttons: list[TerminalButton] = []
        self._confirm_btn: TerminalButton | None = None

    def on_enter(self) -> None:
        """Initialise fonts and layout."""
        self._font = pygame.font.SysFont("consolas", config.FONT_SIZE)
        self._small_font = pygame.font.SysFont("consolas", config.FONT_SIZE_SMALL)
        self._build_buttons()

    def _build_buttons(self) -> None:
        """Create card choice buttons and confirm button."""
        self._buttons.clear()
        font = self._font
        small_font = self._small_font
        if font is None or small_font is None:
            return

        w, _ = self.display.get_size()
        btn_w = 360
        btn_h = 50
        btn_x = (w - btn_w) // 2
        y_start = 200
        spacing = 58

        for i, d in enumerate(self._card_choices):
            label = f"[{i + 1}] {d.name.upper()}"
            btn = TerminalButton(
                btn_x,
                y_start + i * spacing,
                btn_w,
                btn_h,
                label=label,
                on_click=self._make_select_callback(i),
            )
            self._buttons.append(btn)

        # Confirm button
        confirm_y = y_start + len(self._card_choices) * spacing + 20
        self._confirm_btn = TerminalButton(
            btn_x,
            confirm_y,
            btn_w,
            40,
            "[CONFIRM SELECTION]",
            on_click=self._on_confirm,
        )

    def _make_select_callback(self, index: int) -> Callable[[], None]:
        """Create a typed callback for card selection."""

        def callback() -> None:
            self._selected_index = index

        return callback

    def _on_confirm(self) -> None:
        """Add selected card to campaign and trigger callback."""
        if self.on_confirm is not None:
            self.on_confirm()

    def handle_event(self, event: pygame.event.Event) -> None:
        """Handle mouse clicks."""
        if event.type == pygame.MOUSEMOTION:
            self._mouse_pos = event.pos
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._mouse_pos = event.pos
            for btn in self._buttons:
                btn.set_hover(self._mouse_pos)
                btn.click()
            if self._confirm_btn:
                self._confirm_btn.set_hover(self._mouse_pos)
                self._confirm_btn.click()

    def update(self, dt: float) -> None:
        """Update hover state."""
        for btn in self._buttons:
            btn.set_hover(self._mouse_pos)
        if self._confirm_btn:
            self._confirm_btn.set_hover(self._mouse_pos)

    def render(self) -> None:
        """Draw the reward screen."""
        surface = self.display
        font = self._font
        small_font = self._small_font
        assert font is not None
        assert small_font is not None

        w, _h = surface.get_size()

        # === Header ===
        title = font.render("> SALVAGE RECOVERED", True, config.PHOSPHOR_GREEN)
        surface.blit(title, ((w - title.get_width()) // 2, 20))

        # === Credits ===
        cred_text = (
            f"  CREDITS AWARDED: +{pad(self._credits_earned, 4)}"
            f"    TOTAL: {pad(self._campaign.current_credits, 4)}"
        )
        cred_surf = font.render(cred_text, True, config.PHOSPHOR_GREEN)
        surface.blit(cred_surf, ((w - cred_surf.get_width()) // 2, 60))

        # === Directive selection panel ===
        panel_h = 200 + len(self._card_choices) * 58
        panel = Panel((w - 420) // 2, 100, 420, panel_h, "DIRECTIVE SELECTION")
        panel.render(surface, font, font)

        # === Card choices ===
        for i, d in enumerate(self._card_choices):
            y = panel.rect.top + 30 + i * 58
            selected = i == self._selected_index
            col = config.PHOSPHOR_BRIGHT if selected else config.PHOSPHOR_GREEN
            prefix = ">> " if selected else "   "

            name_surf = font.render(f"{prefix}{d.name.upper()}", True, col)
            surface.blit(name_surf, (panel.rect.left + 16, y))

            detail_text = (
                f"       TYPE: {d.directive_type.name}  "
                f"DMG: {d.damage:02d}  OL: {d.overload_cost:02d}"
            )
            if d.range_ > 0:
                detail_text += f"  RNG: {d.range_:02d}"
            detail_surf = small_font.render(detail_text, True, config.PHOSPHOR_DIM)
            surface.blit(detail_surf, (panel.rect.left + 16, y + 22))

            # Description
            if d.description:
                desc_surf = small_font.render(f"       {d.description}", True, config.PHOSPHOR_DIM)
                surface.blit(desc_surf, (panel.rect.left + 16, y + 38))

        # === Buttons ===
        for btn in self._buttons:
            btn.render(surface, font)
        if self._confirm_btn:
            self._confirm_btn.render(surface, font)
