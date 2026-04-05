"""CRT terminal renderer — scanlines, flicker, and vignette.

Only effects that are proven safe: pre-built dark overlays blitted on top.
No blend modes, no surface copies, no PixelArray.
"""

from __future__ import annotations

import math
import time

import pygame

from src import config


class TerminalRenderer:
    """Applies CRT terminal effects to the game surface each frame."""

    def __init__(self, display: pygame.Surface) -> None:
        width, height = display.get_size()
        if width <= 0 or height <= 0:
            raise ValueError(f"Display must have positive dimensions, got {width}x{height}")
        self._display = display
        self._width = width
        self._height = height

        # Pre-built overlays (generated once, blitted every frame)
        self._scanline_surface = self._build_scanline_overlay()
        self._vignette_surface = self._build_vignette()
        self._flicker_surface = pygame.Surface((self._width, self._height), pygame.SRCALPHA)

    @property
    def display(self) -> pygame.Surface:
        return self._display

    # ------------------------------------------------------------------
    # Scanlines
    # ------------------------------------------------------------------

    def _build_scanline_overlay(self) -> pygame.Surface:
        surface = pygame.Surface((self._width, self._height), pygame.SRCALPHA)
        surface.fill((0, 0, 0, 0))
        spacing = config.SCANLINE_SPACING
        alpha = config.SCANLINE_ALPHA
        for row in range(0, self._height, spacing):
            pygame.draw.line(surface, (0, 0, 0, alpha), (0, row), (self._width, row))
        return surface

    def apply_scanlines(self) -> None:
        self._display.blit(self._scanline_surface, (0, 0))

    # ------------------------------------------------------------------
    # Vignette
    # ------------------------------------------------------------------

    def _build_vignette(self) -> pygame.Surface:
        surface = pygame.Surface((self._width, self._height), pygame.SRCALPHA)
        strength = config.VIGNETTE_STRENGTH
        if strength <= 0:
            return surface

        cx = self._width // 2
        cy = self._height // 2
        max_dist = math.sqrt(cx * cx + cy * cy)

        steps = 40
        for i in range(steps, 0, -1):
            t = i / steps
            factor = t**2 * strength
            radius = int(t * max_dist)
            if radius <= 0:
                continue
            alpha = max(0, min(255, int(factor * 255)))
            pygame.draw.circle(surface, (0, 0, 0, alpha), (cx, cy), radius)
        return surface

    def apply_vignette(self) -> None:
        if config.VIGNETTE_STRENGTH <= 0:
            return
        self._display.blit(self._vignette_surface, (0, 0))

    # ------------------------------------------------------------------
    # Flicker
    # ------------------------------------------------------------------

    def apply_flicker(self, current_time: float | None = None) -> None:
        if current_time is None:
            current_time = time.monotonic()
        wave = math.sin(current_time * 2.0 * math.pi * config.FLICKER_FREQUENCY)
        if wave > 0:
            alpha = int(wave * config.FLICKER_INTENSITY * 255)
            if alpha > 0:
                self._flicker_surface.fill((0, 0, 0, alpha))
                self._display.blit(self._flicker_surface, (0, 0))

    # ------------------------------------------------------------------
    # Stubs for effects that need more work
    # ------------------------------------------------------------------

    def apply_chromatic_aberration(self) -> None:
        pass  # TODO: needs safe additive-only implementation

    def apply_noise_grain(self) -> None:
        pass  # TODO: needs safe additive-only implementation

    def apply_phosphor_bloom(self) -> None:
        pass  # TODO: needs safe additive-only implementation

    def apply_afterimage(self) -> None:
        pass  # TODO: needs safe additive-only implementation

    def apply_signal_glitch(self) -> None:
        pass  # TODO: needs safe implementation

    def apply_barrel_distortion(self) -> None:
        pass

    # ------------------------------------------------------------------
    # Combined effects
    # ------------------------------------------------------------------

    def apply_effects(self, current_time: float | None = None) -> None:
        """Apply all CRT effects.

        Currently active: afterimage (disabled) → flicker → chromatic
        aberration (disabled) → vignette → scanlines → noise (disabled)
        → bloom (disabled) → glitch (disabled).
        """
        self.apply_afterimage()
        self.apply_flicker(current_time)
        self.apply_chromatic_aberration()
        self.apply_vignette()
        self.apply_scanlines()
        self.apply_noise_grain()
        self.apply_phosphor_bloom()
        self.apply_signal_glitch()
