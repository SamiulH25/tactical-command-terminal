"""Main menu — terminal boot screen.

The first screen the Coordinator sees.  All positions are defined in
1920x1080 base coordinates and scaled proportionally.
"""

from __future__ import annotations

from collections.abc import Callable

import pygame

from src import config
from src.core.terminal import TerminalRenderer
from src.screens.base_screen import Screen
from src.ui.button import TerminalButton
from src.ui.layout import refresh, sx, sy
from src.ui.panel import Panel
from src.ui.war_comms_widget import WarCommsWidget


class MainMenu(Screen):
    """The terminal boot screen shown at game launch."""

    on_new_deployment_cb: Callable[[], None] | None = None
    on_resume_cb: Callable[[], None] | None = None
    on_terminate_cb: Callable[[], None] | None = None

    def __init__(self, renderer: TerminalRenderer) -> None:
        super().__init__(renderer)
        self._font: pygame.font.Font | None = None
        self._header_font: pygame.font.Font | None = None
        self._small_font: pygame.font.Font | None = None
        self._mouse_pos: tuple[int, int] | None = None
        self._main_panel: Panel | None = None
        self._status_panel: Panel | None = None
        self._buttons: list[TerminalButton] = []
        self._cursor_visible: bool = True
        self._cursor_timer: float = 0.0
        self._war_comms = WarCommsWidget()

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def on_enter(self) -> None:
        self._font = pygame.font.SysFont("consolas", config.FONT_SIZE)
        self._header_font = pygame.font.SysFont("consolas", config.FONT_SIZE_HEADER)
        self._small_font = pygame.font.SysFont("consolas", config.FONT_SIZE_SMALL)
        self._cursor_visible = True
        self._cursor_timer = 0.0
        self._war_comms.set_fonts(self._font, self._small_font)
        self._build_layout()

    def _build_layout(self) -> None:
        display = self.display
        refresh(display)
        font = self._font
        assert font is not None

        # Main panel
        pw = sx(1140)
        ph = sy(920)
        px = sx(30)
        py = sy(70)
        self._main_panel = Panel(px, py, pw, ph)

        # Session Status — right side, above war comms
        spx = sx(1190)
        spy = sy(70)
        spw = sx(700)
        sph = sy(340)
        self._status_panel = Panel(spx, spy, spw, sph, "SESSION STATUS")

        # Buttons — centered in main panel
        bw = sx(460)
        bh = sy(56)
        bx = px + sx(30)
        by = py + sy(130)
        spacing = sy(80)

        self._buttons = [
            TerminalButton(
                bx,
                by,
                bw,
                bh,
                label="[1]  NEW DEPLOYMENT",
                on_click=lambda: self._call_new_deployment(),
                key=pygame.K_1,
            ),
            TerminalButton(
                bx,
                by + spacing,
                bw,
                bh,
                label="[2]  RESUME SESSION [LOCKED]",
                on_click=lambda: self._call_resume(),
                key=pygame.K_2,
                enabled=False,
            ),
            TerminalButton(
                bx,
                by + spacing * 2,
                bw,
                bh,
                label="[3]  TERMINATE LINK",
                on_click=self._call_terminate,
                key=pygame.K_3,
            ),
        ]

    def _call_new_deployment(self) -> None:
        if self.on_new_deployment_cb is not None:
            self.on_new_deployment_cb()

    def _call_resume(self) -> None:
        if self.on_resume_cb is not None:
            self.on_resume_cb()

    def _call_terminate(self) -> None:
        pygame.event.post(pygame.Event(pygame.QUIT))

    # ------------------------------------------------------------------
    # Events
    # ------------------------------------------------------------------

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEMOTION:
            self._mouse_pos = event.pos
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._mouse_pos = event.pos
            for btn in self._buttons:
                btn.set_hover(self._mouse_pos)
                if btn.click():
                    return
        elif event.type == pygame.KEYDOWN:
            for btn in self._buttons:
                if btn.press_key(event.key):
                    return

    def update(self, dt: float) -> None:
        for btn in self._buttons:
            btn.set_hover(self._mouse_pos)
        self._cursor_timer += dt
        if self._cursor_timer >= 0.6:
            self._cursor_timer = 0.0
            self._cursor_visible = not self._cursor_visible
        self._war_comms.update(dt)

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def render(self) -> None:
        surface = self.display
        refresh(surface)
        font = self._font
        header_font = self._header_font
        small_font = self._small_font
        assert font is not None
        assert header_font is not None
        assert small_font is not None
        assert self._main_panel is not None

        w, h = surface.get_size()

        # Top bezel
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

        # Panel
        self._main_panel.render(surface, font, header_font)

        # Greeting + cursor
        greeting = "> Hello Coordinator"
        if self._cursor_visible:
            greeting += "\u2588"
        greet_surf = header_font.render(greeting, True, config.PHOSPHOR_GREEN)
        surface.blit(greet_surf, (sx(80), sy(130)))

        # Version
        version_surf = small_font.render(
            "> TACTICAL COMMAND TERMINAL v2.7.1", True, config.PHOSPHOR_DIM
        )
        surface.blit(version_surf, (sx(80), sy(168)))

        # Button descriptions
        descriptions = [
            "Initialize new deployment sequence.  Select unit and equipment.",
            "Restore previous session from last checkpoint.",
            "Disconnect from tactical network.  Return to desktop.",
        ]
        for btn, desc in zip(self._buttons, descriptions, strict=False):
            btn.render(surface, font)
            desc_surf = small_font.render(desc, True, config.PHOSPHOR_DIM)
            surface.blit(desc_surf, (btn.rect.left + sx(4), btn.rect.bottom + sy(4)))

        # Footer
        auth_surf = font.render("[AUTHORIZED PERSONNEL ONLY]", True, config.PHOSPHOR_DIM)
        surface.blit(auth_surf, ((w - auth_surf.get_width()) // 2, h - sy(35)))

        # Session Status panel
        assert self._status_panel is not None
        self._status_panel.render(surface, font, header_font)
        sp = self._status_panel.rect

        status_data = [
            ("UNITS: ", "01 / 05", config.PHOSPHOR_GREEN),
            ("DEEPEST: ", "--", config.PHOSPHOR_DIM),
            ("STATUS: ", "[STANDBY]", config.PHOSPHOR_GREEN),
            ("LINK: ", "SECURE", config.PHOSPHOR_GREEN),
        ]
        sy_pos = sp.top + sy(30)
        sx_pos = sp.left + sx(14)
        for label, value, colour in status_data:
            label_surf = small_font.render(label, True, config.PHOSPHOR_DIM)
            value_surf = small_font.render(value, True, colour)
            surface.blit(label_surf, (sx_pos, sy_pos))
            surface.blit(value_surf, (sx_pos + label_surf.get_width(), sy_pos))
            sy_pos += label_surf.get_height() + sy(8)

        # War effort comms — below status panel
        comms_w = sx(700)
        comms_h = sy(400)
        comms_x = sx(1190)
        comms_y = sp.bottom + sy(20)
        self._war_comms.render(surface, comms_x, comms_y, comms_w, comms_h)
