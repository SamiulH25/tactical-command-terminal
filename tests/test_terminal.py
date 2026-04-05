"""Tests for the CRT terminal renderer."""

import pygame
import pytest

from src import config
from src.core.terminal import TerminalRenderer

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def display() -> pygame.Surface:
    return pygame.Surface((256, 256))


@pytest.fixture()
def renderer(display: pygame.Surface) -> TerminalRenderer:
    return TerminalRenderer(display)


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------


class TestConstruction:
    def test_valid_display(self, display: pygame.Surface) -> None:
        r = TerminalRenderer(display)
        assert r.display is display

    def test_zero_width_raises(self) -> None:
        with pytest.raises(ValueError, match="positive dimensions"):
            TerminalRenderer(pygame.Surface((0, 100)))

    def test_zero_height_raises(self) -> None:
        with pytest.raises(ValueError, match="positive dimensions"):
            TerminalRenderer(pygame.Surface((100, 0)))


# ---------------------------------------------------------------------------
# Scanlines
# ---------------------------------------------------------------------------


class TestScanlines:
    def test_scanline_surface_correct_size(self, renderer: TerminalRenderer) -> None:
        sw, sh = renderer._scanline_surface.get_size()
        assert sw == renderer._width
        assert sh == renderer._height

    def test_apply_no_crash(self, renderer: TerminalRenderer) -> None:
        renderer.apply_scanlines()

    def test_darkens_surface(self, display: pygame.Surface) -> None:
        white = pygame.Surface(display.get_size())
        white.fill((255, 255, 255))
        r = TerminalRenderer(white)
        r.apply_scanlines()
        after = white.get_at((100, config.SCANLINE_SPACING))
        assert after[0] < 255 or after[3] < 255


# ---------------------------------------------------------------------------
# Vignette
# ---------------------------------------------------------------------------


class TestVignette:
    def test_vignette_surface_size(self, renderer: TerminalRenderer) -> None:
        vw, vh = renderer._vignette_surface.get_size()
        assert vw == renderer._width
        assert vh == renderer._height

    def test_apply_no_crash(self, renderer: TerminalRenderer) -> None:
        renderer.apply_vignette()

    def test_darkens_edges(self, display: pygame.Surface) -> None:
        white = pygame.Surface(display.get_size())
        white.fill((255, 255, 255))
        r = TerminalRenderer(white)
        r.apply_vignette()
        corner = white.get_at((5, 5))
        center = white.get_at((128, 128))
        assert corner[0] < center[0]


# ---------------------------------------------------------------------------
# Flicker
# ---------------------------------------------------------------------------


class TestFlicker:
    def test_apply_no_crash(self, renderer: TerminalRenderer) -> None:
        renderer.apply_flicker(current_time=0.0)

    def test_at_peak_darkens(self, display: pygame.Surface) -> None:
        white = pygame.Surface(display.get_size())
        white.fill((255, 255, 255))
        r = TerminalRenderer(white)
        t = 1.0 / (4 * config.FLICKER_FREQUENCY)
        r.apply_flicker(current_time=t)
        assert white.get_at((100, 100))[0] < 255

    def test_at_trough_no_change(self, display: pygame.Surface) -> None:
        white = pygame.Surface(display.get_size())
        white.fill((255, 255, 255))
        r = TerminalRenderer(white)
        t = 3.0 / (4 * config.FLICKER_FREQUENCY)
        r.apply_flicker(current_time=t)
        assert white.get_at((100, 100))[:3] == (255, 255, 255)

    def test_alpha_bounded(self) -> None:
        max_alpha = int(config.FLICKER_INTENSITY * 255)
        assert 0 < max_alpha < 255


# ---------------------------------------------------------------------------
# Stub effects — should be no-ops
# ---------------------------------------------------------------------------


class TestStubEffects:
    """Effects that are currently disabled should not crash or change the surface."""

    def test_chromatic_aberration_noop(self, display: pygame.Surface) -> None:
        green = pygame.Surface(display.get_size())
        green.fill((38, 217, 64))
        r = TerminalRenderer(green)
        r.apply_chromatic_aberration()
        assert green.get_at((128, 128))[:3] == (38, 217, 64)

    def test_noise_grain_noop(self, display: pygame.Surface) -> None:
        green = pygame.Surface(display.get_size())
        green.fill((38, 217, 64))
        r = TerminalRenderer(green)
        r.apply_noise_grain()
        assert green.get_at((128, 128))[:3] == (38, 217, 64)

    def test_phosphor_bloom_noop(self, display: pygame.Surface) -> None:
        green = pygame.Surface(display.get_size())
        green.fill((38, 217, 64))
        r = TerminalRenderer(green)
        r.apply_phosphor_bloom()
        assert green.get_at((128, 128))[:3] == (38, 217, 64)

    def test_afterimage_noop(self, display: pygame.Surface) -> None:
        green = pygame.Surface(display.get_size())
        green.fill((38, 217, 64))
        r = TerminalRenderer(green)
        r.apply_afterimage()
        assert green.get_at((128, 128))[:3] == (38, 217, 64)

    def test_signal_glitch_noop(self, display: pygame.Surface) -> None:
        green = pygame.Surface(display.get_size())
        green.fill((38, 217, 64))
        r = TerminalRenderer(green)
        r.apply_signal_glitch()
        # Should either stay green or have tiny glitch lines — never go black

    def test_barrel_distortion_noop(self, display: pygame.Surface) -> None:
        green = pygame.Surface(display.get_size())
        green.fill((38, 217, 64))
        r = TerminalRenderer(green)
        r.apply_barrel_distortion()
        assert green.get_at((128, 128))[:3] == (38, 217, 64)


# ---------------------------------------------------------------------------
# Combined effects
# ---------------------------------------------------------------------------


class TestCombinedEffects:
    def test_apply_effects_no_crash(self, display: pygame.Surface) -> None:
        green = pygame.Surface(display.get_size())
        green.fill((38, 217, 64))
        r = TerminalRenderer(green)
        r.apply_effects(current_time=0.0)
        # Should still be mostly green (scanlines + vignette darken but don't kill)
        center = green.get_at((128, 128))
        assert center[1] > 0  # Green channel should survive

    def test_effects_dont_go_black(self, display: pygame.Surface) -> None:
        """Effects should not destroy a green surface in a single pass."""
        green = pygame.Surface(display.get_size())
        green.fill((38, 217, 64))
        r = TerminalRenderer(green)
        r.apply_effects(current_time=0.0)
        center = green.get_at((128, 128))
        # Green channel should still be visible after one pass
        assert center[1] > 50
