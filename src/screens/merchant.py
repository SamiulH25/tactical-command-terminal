"""Merchant / Supply Depot screen — purchase equipment with credits.

The Coordinator can browse and buy equipment modules from the forward
supply depot.  Each piece costs credits based on its stats.  Purchased
items are added to the campaign's unlocked equipment pool.

Lore framing:  Requisition terminals at forward outposts allow Coordinators
to allocate credits toward salvaged or fabricated hardware.
"""

from __future__ import annotations

from collections.abc import Callable

import pygame

from src import config
from src.core.terminal import TerminalRenderer
from src.models.campaign import Campaign
from src.models.data_loader import load_equipment
from src.models.equipment import Equipment
from src.models.mech import DeployedMech
from src.screens.base_screen import Screen
from src.ui.button import TerminalButton
from src.ui.layout import refresh, s, sx, sy
from src.ui.panel import Panel
from src.ui.text import pad


class MerchantScreen(Screen):
    """Supply Depot screen — equipment purchase terminal."""

    def __init__(
        self,
        renderer: TerminalRenderer,
        campaign: Campaign,
        game_data: object,
        mech: DeployedMech | None,
        on_close: Callable[[], None],
    ) -> None:
        """Create the MerchantScreen.

        Args:
            renderer: The CRT terminal renderer.
            campaign: Current campaign state (credits, unlocked equipment).
            game_data: GameData container holding equipment definitions.
            mech: Currently deployed mech (may be None).
            on_close: Callback to return to the ShipMenu.
        """
        super().__init__(renderer)
        self._campaign = campaign
        self._game_data = game_data
        self._mech = mech
        self._on_close = on_close
        self._font: pygame.font.Font | None = None
        self._small_font: pygame.font.Font | None = None
        self._mouse_pos: tuple[int, int] | None = None
        self._equipment_list: list[Equipment] = []
        self._purchase_buttons: list[TerminalButton] = []
        self._close_btn: TerminalButton | None = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def on_enter(self) -> None:
        """Initialise fonts, load equipment, and build layout."""
        self._font = pygame.font.SysFont("consolas", config.FONT_SIZE)
        self._small_font = pygame.font.SysFont("consolas", config.FONT_SIZE_SMALL)
        self._equipment_list = load_equipment()
        self._build_layout()

    def _build_layout(self) -> None:
        """Create buttons and panel geometry."""
        self._purchase_buttons.clear()
        font = self._font
        small_font = self._small_font
        if font is None or small_font is None:
            return

        refresh(self.display)
        w, h = self.display.get_size()

        panel_x, panel_y = s(30, 60)
        panel_w = w - sx(60)
        panel_h = h - sy(120)

        # Equipment item rows
        row_h = sy(50)
        start_y = panel_y + sy(40)

        for i, eq in enumerate(self._equipment_list):
            y = start_y + i * row_h
            btn_w = sx(140)
            btn_x = panel_x + panel_w - btn_w - sx(16)

            price = self._calc_price(eq)
            can_afford = self._campaign.current_credits >= price
            already_owned = eq.id in self._campaign.unlocked_equipment

            if already_owned:
                label = "[OWNED]"
                enabled = False
            elif can_afford:
                label = "[PURCHASE]"
                enabled = True
            else:
                label = "[INSUFFICIENT CREDITS]"
                enabled = False

            btn = TerminalButton(
                btn_x,
                y + sy(4),
                btn_w,
                sy(32),
                label,
                on_click=self._make_purchase_callback(eq) if enabled else lambda: None,
                enabled=enabled,
            )
            self._purchase_buttons.append(btn)

        # Close button
        close_y = panel_y + panel_h - sy(50)
        self._close_btn = TerminalButton(
            panel_x + sx(16),
            close_y,
            sx(120),
            sy(36),
            "[CLOSE]",
            on_click=self._on_close,
        )

    def _calc_price(self, eq: Equipment) -> int:
        """Calculate purchase price for an equipment piece.

        Formula: hp_bonus*5 + damage_bonus*10 + evasion_bonus*8 + ol_discount*15 + 20
        """
        return (
            eq.hp_bonus * 5 + eq.damage_bonus * 10 + eq.evasion_bonus * 8 + eq.ol_discount * 15 + 20
        )

    def _make_purchase_callback(self, eq: Equipment) -> Callable[[], None]:
        """Create a typed callback for purchasing equipment."""

        def callback() -> None:
            price = self._calc_price(eq)
            if self._campaign.current_credits >= price:
                self._campaign.current_credits -= price
                if eq.id not in self._campaign.unlocked_equipment:
                    self._campaign.unlocked_equipment.append(eq.id)
                self._build_layout()

        return callback

    # ------------------------------------------------------------------
    # Events
    # ------------------------------------------------------------------

    def handle_event(self, event: pygame.event.Event) -> None:
        """Handle mouse input."""
        if event.type == pygame.MOUSEMOTION:
            self._mouse_pos = event.pos
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._mouse_pos = event.pos
            for btn in self._purchase_buttons:
                btn.set_hover(self._mouse_pos)
                btn.click()
            if self._close_btn:
                self._close_btn.set_hover(self._mouse_pos)
                self._close_btn.click()

    def update(self, dt: float) -> None:
        """Update hover state."""
        for btn in self._purchase_buttons:
            btn.set_hover(self._mouse_pos)
        if self._close_btn:
            self._close_btn.set_hover(self._mouse_pos)

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def render(self) -> None:
        """Draw the supply depot screen."""
        surface = self.display
        refresh(surface)
        font = self._font
        small_font = self._small_font
        assert font is not None
        assert small_font is not None

        w, h = surface.get_size()
        c = self._campaign

        # === Top bezel ===
        left_text = "> FSA-TD-47"
        right_text = "CH:01 // LINK ACTIVE"
        header_surf = font.render(left_text, True, config.PHOSPHOR_GREEN)
        surface.blit(header_surf, (sx(16), sy(10)))

        # Right-aligned header text
        right_surf = font.render(right_text, True, config.PHOSPHOR_GREEN)
        surface.blit(right_surf, (w - right_surf.get_width() - sx(16), sy(10)))

        # Thick divider
        pygame.draw.line(
            surface,
            config.PHOSPHOR_GREEN,
            (sx(16), sy(38)),
            (w - sx(16), sy(38)),
        )
        # Thin divider
        pygame.draw.line(
            surface,
            config.PHOSPHOR_DIM,
            (sx(16), sy(42)),
            (w - sx(16), sy(42)),
        )

        # === Title bar with credits ===
        mech_credits = pad(c.current_credits, 4)
        floor_label = f"Floor {c.current_floor}" if c.current_floor > 0 else "Pre-Deployment"
        outpost = c.outpost_name
        title_text = f"> SUPPLY DEPOT     {floor_label} - {outpost}    CR:{mech_credits}"
        title_surf = font.render(title_text, True, config.PHOSPHOR_GREEN)
        surface.blit(title_surf, (sx(16), sy(50)))

        # === Equipment list panel ===
        panel_x, panel_y = s(30, 90)
        panel_w = w - sx(60)
        panel_h = h - sy(160)
        panel = Panel(panel_x, panel_y, panel_w, panel_h, "SUPPLY DEPOT")
        panel.render(surface, font, font)

        # Column headers
        col_y = panel_y + sy(12)
        col_name_x = panel_x + sx(16)
        col_slot_x = panel_x + sx(280)
        col_stats_x = panel_x + sx(400)
        col_price_x = panel_x + sx(620)

        header_surf = small_font.render(
            "ITEM                           SLOT         STATS                     PRICE      ACTION",
            True,
            config.PHOSPHOR_DIM,
        )
        surface.blit(header_surf, (col_name_x, col_y))

        # Thin divider under column headers
        div_y = col_y + sy(18)
        pygame.draw.line(
            surface,
            config.PHOSPHOR_DIM,
            (panel_x + sx(10), div_y),
            (panel_x + panel_w - sx(10), div_y),
        )

        # === Equipment rows ===
        row_h = sy(50)
        start_y = panel_y + sy(40)

        for i, eq in enumerate(self._equipment_list):
            y = start_y + i * row_h
            price = self._calc_price(eq)
            can_afford = c.current_credits >= price
            already_owned = eq.id in c.unlocked_equipment

            # Equipment name
            name_color = config.PHOSPHOR_GREEN
            if already_owned:
                name_color = config.PHOSPHOR_DIM
            name_surf = font.render(f"[{i + 1}] {eq.name.upper()}", True, name_color)
            surface.blit(name_surf, (col_name_x, y))

            # Slot
            slot_label = eq.slot.upper()
            slot_color = config.PHOSPHOR_GREEN
            if eq.slot == "weapon":
                slot_color = config.COLOR_ENEMY
            elif eq.slot == "armor":
                slot_color = config.COLOR_FRIENDLY
            elif eq.slot == "utility":
                slot_color = config.COLOR_WARNING
            slot_surf = small_font.render(slot_label, True, slot_color)
            surface.blit(slot_surf, (col_slot_x, y + sy(2)))

            # Stats
            stats_parts: list[str] = []
            if eq.damage_bonus != 0:
                sign = "+" if eq.damage_bonus > 0 else ""
                stats_parts.append(f"{sign}{eq.damage_bonus} DMG")
            if eq.hp_bonus != 0:
                sign = "+" if eq.hp_bonus > 0 else ""
                stats_parts.append(f"{sign}{eq.hp_bonus} HP")
            if eq.evasion_bonus != 0:
                sign = "+" if eq.evasion_bonus > 0 else ""
                stats_parts.append(f"{sign}{eq.evasion_bonus} EVA")
            if eq.ol_discount != 0:
                sign = "+" if eq.ol_discount > 0 else ""
                stats_parts.append(f"{sign}{eq.ol_discount} OL")
            if not stats_parts:
                stats_parts.append("NO MODS")
            stats_text = "  ".join(stats_parts)
            stats_surf = small_font.render(stats_text, True, config.PHOSPHOR_DIM)
            surface.blit(stats_surf, (col_stats_x, y + sy(2)))

            # Price
            price_text = f"CR:{pad(price, 4)}"
            price_color = config.PHOSPHOR_GREEN if can_afford else config.COLOR_WARNING
            price_surf = small_font.render(price_text, True, price_color)
            surface.blit(price_surf, (col_price_x, y + sy(2)))

        # === Close button ===
        if self._close_btn:
            self._close_btn.render(surface, font)

        # === Purchase buttons ===
        for btn in self._purchase_buttons:
            btn.render(surface, font)
