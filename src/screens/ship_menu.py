"""Ship Menu — Mission Command screen.

The inter-combat hub where the Coordinator reviews mech/squad status,
deck composition, and selects the next target.  All positions scaled
proportionally from 1920x1080.
"""

from __future__ import annotations

from collections.abc import Callable

import pygame

from src import config
from src.core.terminal import TerminalRenderer
from src.models.campaign import Campaign
from src.models.mech import DeployedMech
from src.screens.base_screen import Screen
from src.ui.button import TerminalButton
from src.ui.layout import refresh, s, sx, sy
from src.ui.panel import Panel
from src.ui.text import BLOCK_EMPTY, BLOCK_FULL, pad, status_tag
from src.ui.war_comms_widget import WarCommsWidget

# IFF shape symbols for roster display.
_IFF_SYMBOLS: dict[str, str] = {
    "SQUARE": "\u25c8",
    "DIAMOND": "\u25c6",
    "HEXAGON": "\u2b22",
    "CIRCLE_CROSS": "\u25c9",
    "CHEVRON": "\u27e9",
    "TRIANGLE": "\u25b2",
    "RECTANGLE": "\u25ac",
    "CIRCLE": "\u25cf",
    "CROSS": "\u271b",
}

_MAX_SQUAD = 4


class ShipMenu(Screen):
    """The Mission Command screen — inter-combat hub."""

    def __init__(
        self,
        renderer: TerminalRenderer,
        campaign: Campaign,
        mech: DeployedMech | None = None,
        on_assault: Callable[[], None] | None = None,
        on_salvage: Callable[[], None] | None = None,
        on_rest: Callable[[], None] | None = None,
    ) -> None:
        super().__init__(renderer)
        self._campaign = campaign
        self._mech = mech
        self._on_assault_cb = on_assault
        self._on_salvage_cb = on_salvage
        self._on_rest_cb = on_rest
        self._font: pygame.font.Font | None = None
        self._small_font: pygame.font.Font | None = None
        self._mouse_pos: tuple[int, int] | None = None

        self._briefing_cache: list[object] = []
        self._briefing_mech_id: str = ""
        self._war_comms = WarCommsWidget()

        self._tab_briefing: TerminalButton | None = None
        self._tab_ops: TerminalButton | None = None
        self._active_tab: str = "briefing"

        self._room_buttons: list[TerminalButton] = []

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def on_enter(self) -> None:
        self._font = pygame.font.SysFont("consolas", config.FONT_SIZE)
        self._small_font = pygame.font.SysFont("consolas", config.FONT_SIZE_SMALL)
        self._briefing_cache.clear()
        self._briefing_mech_id = ""
        self._war_comms.set_fonts(self._font, self._small_font)
        self._build_layout()

    def _build_layout(self) -> None:
        refresh(self.display)
        font = self._font
        assert font is not None

        tab_y = sy(42)
        self._tab_briefing = TerminalButton(
            *s(30, tab_y, 130, 30),
            "[BRIEFING]",
            on_click=lambda: setattr(self, "_active_tab", "briefing"),
        )
        self._tab_ops = TerminalButton(
            *s(170, tab_y, 150, 30),
            "[OPERATIONS]",
            on_click=lambda: setattr(self, "_active_tab", "operations"),
        )

        btn_y = sy(220)
        self._room_buttons = [
            TerminalButton(
                *s(60, btn_y, 340, 44),
                "[ASSAULT] Enemy Patrol",
                on_click=self._on_assault,
            ),
            TerminalButton(
                *s(60, btn_y + sy(54), 340, 44),
                "[SALVAGE] Wreckage Site",
                on_click=self._on_salvage,
            ),
            TerminalButton(
                *s(60, btn_y + sy(108), 340, 44),
                "[R&R] Forward Camp",
                on_click=self._on_rest,
            ),
        ]

    def _on_assault(self) -> None:
        if self._on_assault_cb is not None:
            self._on_assault_cb()

    def _on_salvage(self) -> None:
        if self._on_salvage_cb is not None:
            self._on_salvage_cb()

    def _on_rest(self) -> None:
        if self._on_rest_cb is not None:
            self._on_rest_cb()

    # ------------------------------------------------------------------
    # Events
    # ------------------------------------------------------------------

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEMOTION:
            self._mouse_pos = event.pos
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._mouse_pos = event.pos
            if self._tab_briefing:
                self._tab_briefing.set_hover(self._mouse_pos)
                self._tab_briefing.click()
            if self._tab_ops:
                self._tab_ops.set_hover(self._mouse_pos)
                self._tab_ops.click()
            if self._active_tab == "operations":
                for btn in self._room_buttons:
                    btn.set_hover(self._mouse_pos)
                    btn.click()

    def update(self, dt: float) -> None:
        if self._tab_briefing:
            self._tab_briefing.set_hover(self._mouse_pos)
        if self._tab_ops:
            self._tab_ops.set_hover(self._mouse_pos)
        for btn in self._room_buttons:
            btn.set_hover(self._mouse_pos)
        self._war_comms.update(dt)

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def render(self) -> None:
        surface = self.display
        refresh(surface)
        font = self._font
        small_font = self._small_font
        assert font is not None
        assert small_font is not None

        w, h = surface.get_size()
        c = self._campaign

        # Top bar
        top_text = (
            f"> MISSION COMMAND"
            f"{'':>{w // 3 - 18}}"
            f"Floor {c.current_floor} - {c.outpost_name}"
            f"    CR:{pad(c.current_credits, 4)}"
        )
        surface.blit(font.render(top_text, True, config.PHOSPHOR_GREEN), (sx(8), sy(10)))
        pygame.draw.line(surface, config.PHOSPHOR_DIM, (sx(8), sy(38)), (w - sx(8), sy(38)))

        # Tabs
        if self._tab_briefing:
            self._tab_briefing.render(surface, font)
        if self._tab_ops:
            self._tab_ops.render(surface, font)

        # Active tab underline
        if self._active_tab == "briefing" and self._tab_briefing:
            pygame.draw.rect(
                surface,
                config.PHOSPHOR_GREEN,
                (
                    self._tab_briefing.rect.left,
                    self._tab_briefing.rect.bottom,
                    self._tab_briefing.rect.width,
                    2,
                ),
            )
        elif self._active_tab == "operations" and self._tab_ops:
            pygame.draw.rect(
                surface,
                config.PHOSPHOR_GREEN,
                (self._tab_ops.rect.left, self._tab_ops.rect.bottom, self._tab_ops.rect.width, 2),
            )

        if self._active_tab == "briefing":
            self._render_briefing(surface, font, small_font, w, h)
        elif self._active_tab == "operations":
            self._render_operations(surface, font, small_font, w, h)

    def _render_briefing(
        self,
        surface: pygame.Surface,
        font: pygame.font.Font,
        small_font: pygame.font.Font,
        w: int,
        h: int,
    ) -> None:
        """Two-column briefing: left = SQUAD ROSTER (up to 4 mechs),
        right = placeholder for future module."""
        mech = self._mech
        mech_id = mech.frame.id if mech else ""

        if mech_id != self._briefing_mech_id:
            self._briefing_cache = (
                self._build_briefing_cache(mech, font, small_font, w) if mech else []
            )
            self._briefing_mech_id = mech_id

        # Left panel — squad roster
        roster_panel = Panel(*s(20, 84, 560, h - sy(110)), "SQUAD ROSTER")
        roster_panel.render(surface, font, font)

        if not self._briefing_cache:
            surface.blit(
                small_font.render("  [VACANT]", True, config.PHOSPHOR_DIM),
                (sx(36), sy(120)),
            )

        # Blit cached roster items
        for item in self._briefing_cache:
            if isinstance(item, tuple) and len(item) == 2:
                surf, pos = item
                if surf == "divider":
                    pygame.draw.line(
                        surface,
                        config.PHOSPHOR_DIM,
                        (pos[0], pos[1]),
                        (sx(564), pos[1]),
                    )
                elif isinstance(surf, pygame.Surface):
                    surface.blit(surf, pos)

        # Right panel — placeholder
        right_panel = Panel(*s(600, 84, w - sx(640), h - sy(110)), "TACTICAL OVERLAY")
        right_panel.render(surface, font, font)
        overlay_lines = [
            "> MODULE OFFLINE",
            "",
            "  Tactical overlay module is not yet",
            "  available in this terminal build.",
            "",
            "  Awaiting software patch from",
            "  FSA Engineering — Floor 15+",
        ]
        oy = sy(120)
        for line in overlay_lines:
            colour = config.PHOSPHOR_GREEN if line.startswith(">") else config.PHOSPHOR_DIM
            lsurf = small_font.render(line, True, colour)
            surface.blit(lsurf, (sx(620), oy))
            oy += sy(20)

    def _build_briefing_cache(
        self,
        mech: DeployedMech,
        font: pygame.font.Font,
        small_font: pygame.font.Font,
        w: int,
    ) -> list[object]:
        """Build cached surfaces for the squad roster (left column).
        Shows up to 4 mech slots: populated for the deployed mech,
        [VACANT] for the rest."""
        surfaces: list[object] = []
        x = sx(36)
        y = sy(112)
        entry_height = sy(190)

        for i in range(_MAX_SQUAD):
            slot_y = y + i * entry_height

            if i == 0 and mech is not None:
                # Render the deployed mech
                frame_text = f"{mech.frame.name.upper():<12s}  {mech.frame.role.upper()}"
                surfaces.append((font.render(frame_text, True, config.PHOSPHOR_GREEN), (x, slot_y)))

                # IFF symbol + callsign
                iff_sym = _IFF_SYMBOLS.get(mech.frame.iff_shape.name, "?")
                iff_col = config.PHOSPHOR_GREEN
                surfaces.append((font.render(iff_sym, True, iff_col), (x, slot_y + sy(22))))
                surfaces.append(
                    (
                        small_font.render(
                            f"  OP: {mech.pilot_type.title()}", True, config.PHOSPHOR_DIM
                        ),
                        (x + sx(22), slot_y + sy(22)),
                    )
                )

                # HP bar
                hp_filled = round(mech.current_hp / mech.max_hp * 16)
                hp_bar = BLOCK_FULL * hp_filled + BLOCK_EMPTY * (16 - hp_filled)
                hp_text = f"  HP: {hp_bar}  {mech.current_hp:03d}/{mech.max_hp:03d}"
                hp_col = (
                    config.PHOSPHOR_GREEN
                    if mech.current_hp > mech.max_hp // 2
                    else config.COLOR_WARNING
                )
                surfaces.append((small_font.render(hp_text, True, hp_col), (x, slot_y + sy(46))))

                # OL bar
                ol_filled = round((mech.max_ol - mech.current_ol) / mech.max_ol * 16)
                ol_bar = BLOCK_FULL * ol_filled + BLOCK_EMPTY * (16 - ol_filled)
                ol_text = f"  OL: {ol_bar}  {mech.current_ol:02d}/{mech.max_ol:02d}"
                surfaces.append(
                    (
                        small_font.render(ol_text, True, config.COLOR_WARNING),
                        (x, slot_y + sy(68)),
                    )
                )

                # Equipment summary
                eq_offset = sy(94)
                for slot_name in ("weapon", "armor", "utility"):
                    eq_id = mech.frame.equipment_slots.get(slot_name)
                    eq_label = eq_id.upper() if eq_id else "(none)"
                    surfaces.append(
                        (
                            small_font.render(
                                f"  {slot_name.upper():>8s}: {eq_label}",
                                True,
                                config.PHOSPHOR_DIM,
                            ),
                            (x, slot_y + eq_offset),
                        )
                    )
                    eq_offset += sy(18)

                # Trait / passive
                if mech.frame.trait:
                    trait_part = mech.frame.trait.split(":")[0].upper()
                    surfaces.append(
                        (
                            small_font.render(
                                f"  [{trait_part}] {mech.frame.trait}", True, config.PHOSPHOR_DIM
                            ),
                            (x, slot_y + sy(94)),
                        )
                    )

                # Status tag
                status = status_tag(mech.current_hp, mech.max_hp)
                surfaces.append(
                    (
                        small_font.render(f"  {status}", True, config.PHOSPHOR_GREEN),
                        (x, slot_y + sy(154)),
                    )
                )

            else:
                # Vacant slot
                surfaces.append(
                    (small_font.render(f"  SLOT {i + 1}", True, config.PHOSPHOR_DIM), (x, slot_y))
                )
                surfaces.append(
                    (
                        small_font.render("  [VACANT]", True, config.PHOSPHOR_DIM),
                        (x, slot_y + sy(22)),
                    )
                )
                surfaces.append(
                    (
                        small_font.render("  HP: ---/--  OL: --/--", True, config.PHOSPHOR_DIM),
                        (x, slot_y + sy(46)),
                    )
                )
                surfaces.append(
                    (
                        small_font.render("  STATUS: [OFFLINE]", True, config.PHOSPHOR_DIM),
                        (x, slot_y + sy(68)),
                    )
                )

            # Divider between entries
            div_y = slot_y + entry_height - sy(8)
            surfaces.append(("divider", (x, div_y)))

        return surfaces

    def _render_operations(
        self,
        surface: pygame.Surface,
        font: pygame.font.Font,
        small_font: pygame.font.Font,
        w: int,
        h: int,
    ) -> None:
        refresh(self.display)
        log_panel = Panel(*s(20, 84, w - sx(40), sy(120)), "MISSION LOG")
        log_panel.render(surface, font, font)

        log_text = "  Dropship insertion confirmed.  Enemy patrols detected at"
        surface.blit(
            small_font.render(log_text, True, config.PHOSPHOR_GREEN),
            (log_panel.rect.left + sx(16), log_panel.rect.top + sy(30)),
        )
        log_text2 = f"  {self._campaign.outpost_name} perimeter.  Intel suggests light resistance."
        surface.blit(
            small_font.render(log_text2, True, config.PHOSPHOR_GREEN),
            (log_panel.rect.left + sx(16), log_panel.rect.top + sy(52)),
        )

        room_panel = Panel(*s(20, sy(206), w - sx(40), h - sy(230)), "SELECT NEXT TARGET")
        room_panel.render(surface, font, font)

        for btn in self._room_buttons:
            btn.render(surface, font)

        # War effort comms — bottom right, full width to edge
        comms_w = sx(700)
        comms_h = sy(120)
        comms_x = w - sx(730)
        comms_y = h - comms_h - sy(40)
        self._war_comms.render(surface, comms_x, comms_y, comms_w, comms_h)
