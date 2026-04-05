"""Monitor frame — renders a physical monitor surrounding the game screen.

The entire game is presented as if the player is looking at a real CRT
monitor.  The 1920x1080 game content is rendered to an offscreen surface,
scaled to fit inside the monitor's screen area, then the monitor bezel,
stand, and screen glare are rendered on top.
"""

from __future__ import annotations

import pygame

_BEZEL_COLOR: tuple[int, int, int] = (18, 20, 16)
_BEZEL_HIGHLIGHT: tuple[int, int, int] = (40, 45, 36)
_BEZEL_SHADOW: tuple[int, int, int] = (8, 10, 6)
_STAND_COLOR: tuple[int, int, int] = (22, 25, 19)
_GLARE_ALPHA: int = 10

# The game's native resolution
_GAME_W: int = 1920
_GAME_H: int = 1080


class MonitorFrame:
    """A physical monitor that frames the 1920x1080 game content."""

    def __init__(
        self,
        window_width: int,
        window_height: int,
        bezel_thickness: int = 40,
    ) -> None:
        self._window_w = window_width
        self._window_h = window_height
        self._bezel = bezel_thickness

        # Calculate the inner screen area (maintains 16:9)
        avail_w = window_width - bezel_thickness * 2
        avail_h = window_height - bezel_thickness * 2

        if avail_w / avail_h > _GAME_W / _GAME_H:
            screen_h = avail_h
            screen_w = int(screen_h * _GAME_W / _GAME_H)
        else:
            screen_w = avail_w
            screen_h = int(screen_w * _GAME_H / _GAME_W)

        self._screen_x = (window_width - screen_w) // 2
        self._screen_y = (window_height - screen_h) // 2
        self._screen_w = screen_w
        self._screen_h = screen_h

        # Pre-compute scale factors
        self._scale_x = screen_w / _GAME_W
        self._scale_y = screen_h / _GAME_H

        # Game surface at native 1920x1080
        self._game_surface = pygame.Surface((_GAME_W, _GAME_H))

        # Pre-rendered static overlays
        self._glare_surf = self._make_glare()
        self._stand_surf = self._make_stand()

    @property
    def game_surface(self) -> pygame.Surface:
        """Render all game UI to this 1920x1080 surface."""
        return self._game_surface

    @property
    def screen_rect(self) -> pygame.Rect:
        """Destination rect on the window where game content appears."""
        return pygame.Rect(self._screen_x, self._screen_y, self._screen_w, self._screen_h)

    # ------------------------------------------------------------------
    # Static overlay builders
    # ------------------------------------------------------------------

    def _make_glare(self) -> pygame.Surface:
        """Diagonal glass reflection."""
        surf = pygame.Surface((self._screen_w, self._screen_h), pygame.SRCALPHA)
        points = [
            (0, 0),
            (int(self._screen_w * 0.55), 0),
            (int(self._screen_w * 0.25), self._screen_h),
            (0, int(self._screen_h * 0.65)),
        ]
        pygame.draw.polygon(surf, (200, 215, 190, _GLARE_ALPHA), points)
        return surf

    def _make_stand(self) -> pygame.Surface:
        """Trapezoidal monitor stand."""
        stand_h = int(self._window_h * 0.05)
        self._window_h - stand_h
        top_w = int(self._screen_w * 0.22)
        bot_w = int(self._screen_w * 0.38)
        cx = self._window_w // 2

        surf = pygame.Surface((self._window_w, stand_h), pygame.SRCALPHA)
        pts = [
            (cx - top_w // 2, 0),
            (cx + top_w // 2, 0),
            (cx + bot_w // 2, stand_h),
            (cx - bot_w // 2, stand_h),
        ]
        pygame.draw.polygon(surf, _STAND_COLOR, pts)
        pygame.draw.line(surf, _BEZEL_HIGHLIGHT, pts[0], pts[1], 1)
        return surf

    # ------------------------------------------------------------------
    # Composite
    # ------------------------------------------------------------------

    def blit_to(self, window_surface: pygame.Surface) -> None:
        """Composite game content + monitor bezel onto the window."""
        # Bezel background
        window_surface.fill(_BEZEL_COLOR)

        # Scale game surface → screen area
        scaled = pygame.transform.scale(self._game_surface, (self._screen_w, self._screen_h))
        window_surface.blit(scaled, (self._screen_x, self._screen_y))

        # Screen depth shadow (inner top/left edge)
        for i in range(4):
            a = int(50 * (1 - i / 4))
            line = pygame.Surface((self._screen_w, 1), pygame.SRCALPHA)
            line.fill((0, 0, 0, a))
            window_surface.blit(line, (self._screen_x, self._screen_y + i))
            line_v = pygame.Surface((1, self._screen_h), pygame.SRCALPHA)
            line_v.fill((0, 0, 0, a))
            window_surface.blit(line_v, (self._screen_x + i, self._screen_y))

        # Glass glare
        window_surface.blit(self._glare_surf, (self._screen_x, self._screen_y))

        # Inner bezel highlight
        pygame.draw.rect(
            window_surface,
            _BEZEL_HIGHLIGHT,
            (self._screen_x - 1, self._screen_y - 1, self._screen_w + 2, self._screen_h + 2),
            1,
        )

        # Outer bezel shadow
        bx = self._screen_x - self._bezel
        by = self._screen_y - self._bezel
        bw = self._screen_w + self._bezel * 2
        bh = self._screen_h + self._bezel * 2
        pygame.draw.rect(window_surface, _BEZEL_SHADOW, (bx, by, bw, bh), 2)

        # Stand
        stand_y = self._window_h - self._stand_surf.get_height()
        window_surface.blit(self._stand_surf, (0, stand_y))

        # Power LED (bottom-right of bezel)
        led_x = self._screen_x + self._screen_w - 16
        led_y = self._screen_y + self._screen_h + 10
        pygame.draw.circle(window_surface, (25, 160, 50), (led_x, led_y), 3)
        pygame.draw.circle(window_surface, (50, 240, 90), (led_x, led_y), 2)

    # ------------------------------------------------------------------
    # Coordinate helpers — convert game (1920x1080) coords to window
    # ------------------------------------------------------------------

    def game_to_window(self, gx: int, gy: int) -> tuple[int, int]:
        """Convert a game-surface coordinate to window pixels."""
        return (
            self._screen_x + int(gx * self._scale_x),
            self._screen_y + int(gy * self._scale_y),
        )
