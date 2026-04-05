"""Pause screen — operations halted overlay.

Pushed on top of the active screen when the player presses Escape.
Displays a semi-transparent overlay with resume, save, and return options.
"""

from __future__ import annotations

from collections.abc import Callable

import pygame

from src import config
from src.core.terminal import TerminalRenderer
from src.screens.base_screen import Screen
from src.ui.button import TerminalButton
from src.ui.layout import refresh, s, sx, sy
from src.ui.panel import Panel


class PauseScreen(Screen):
    """Pause overlay shown when Escape is pressed during gameplay."""

    def __init__(
        self,
        renderer: TerminalRenderer,
        campaign: object,
        on_resume: Callable[[], None] | None = None,
        on_save: Callable[[], None] | None = None,
        on_return_to_base: Callable[[], None] | None = None,
    ) -> None:
        super().__init__(renderer)
        self._campaign = campaign
        self._on_resume = on_resume
        self._on_save = on_save
        self._on_return_to_base = on_return_to_base
        self._font: pygame.font.Font | None = None
        self._small_font: pygame.font.Font | None = None
        self._panel: Panel | None = None
        self._buttons: list[TerminalButton] = []
        self._mouse_pos: tuple[int, int] | None = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def on_enter(self) -> None:
        self._font = pygame.font.SysFont("consolas", config.FONT_SIZE)
        self._small_font = pygame.font.SysFont("consolas", config.FONT_SIZE_SMALL)
        self._build_layout()

    def _build_layout(self) -> None:
        display = self.display
        refresh(display)
        font = self._font
        assert font is not None

        # Centered pause panel
        pw = sx(600)
        ph = sy(320)
        px, py = s(660, 340)
        self._panel = Panel(px, py, pw, ph)

        # Buttons centered in panel
        bw = sx(460)
        bh = sy(56)
        bx = px + (pw - bw) // 2
        by = py + sy(110)
        spacing = sy(72)

        self._buttons = [
            TerminalButton(
                bx,
                by,
                bw,
                bh,
                label="[1] RESUME OPERATIONS",
                on_click=self._call_resume,
                key=pygame.K_1,
            ),
            TerminalButton(
                bx,
                by + spacing,
                bw,
                bh,
                label="[2] SAVE SESSION",
                on_click=self._call_save,
                key=pygame.K_2,
            ),
            TerminalButton(
                bx,
                by + spacing * 2,
                bw,
                bh,
                label="[3] RETURN TO BASE",
                on_click=self._call_return_to_base,
                key=pygame.K_3,
            ),
        ]

    # ------------------------------------------------------------------
    # Callbacks
    # ------------------------------------------------------------------

    def _call_resume(self) -> None:
        if self._on_resume is not None:
            self._on_resume()

    def _call_save(self) -> None:
        if self._on_save is not None:
            self._on_save()

    def _call_return_to_base(self) -> None:
        if self._on_return_to_base is not None:
            self._on_return_to_base()

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
            if event.key in (pygame.K_ESCAPE, pygame.K_1):
                self._call_resume()
                return
            for btn in self._buttons:
                if btn.press_key(event.key):
                    return

    def update(self, dt: float) -> None:
        for btn in self._buttons:
            btn.set_hover(self._mouse_pos)

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
        assert self._panel is not None

        w, h = surface.get_size()

        # Dark semi-transparent overlay
        overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))

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
        self._panel.render(surface, font, font)

        # PAUSED title
        panel = self._panel.rect
        title_surf = font.render("> OPERATIONS HALTED", True, config.PHOSPHOR_GREEN)
        surface.blit(title_surf, (panel.left + sx(30), panel.top + sy(24)))

        paused_surf = font.render("[PAUSED]", True, config.PHOSPHOR_DIM)
        surface.blit(paused_surf, (panel.left + sx(30), panel.top + sy(56)))

        # Buttons
        for btn in self._buttons:
            btn.render(surface, font)

        # Footer hint
        hint_surf = small_font.render(
            "[ESC] RESUME  |  [1-3] SELECT OPTION", True, config.PHOSPHOR_DIM
        )
        surface.blit(
            hint_surf,
            ((w - hint_surf.get_width()) // 2, h - sy(30)),
        )
