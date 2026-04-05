"""Tests for the monitor frame (physical monitor bezel)."""

import pygame

from src import config
from src.core.monitor_frame import MonitorFrame


class TestMonitorFrame:
    """Verify monitor frame construction and compositing."""

    def test_construction(self) -> None:
        mf = MonitorFrame(1920, 1080)
        assert mf.game_surface.get_size() == (1920, 1080)

    def test_screen_rect_fits_in_window(self) -> None:
        mf = MonitorFrame(1920, 1080)
        rect = mf.screen_rect
        assert rect.left >= 0
        assert rect.right <= 1920
        assert rect.bottom <= 1080

    def test_screen_rect_maintains_aspect_ratio(self) -> None:
        mf = MonitorFrame(1920, 1080)
        rect = mf.screen_rect
        ratio = rect.width / rect.height
        assert abs(ratio - 16 / 9) < 0.01

    def test_blit_to_no_crash(self) -> None:
        mf = MonitorFrame(1920, 1080)
        mf.game_surface.fill(config.COLOR_BG)
        window = pygame.Surface((1920, 1080))
        mf.blit_to(window)

    def test_bezel_thickness(self) -> None:
        mf_thin = MonitorFrame(1920, 1080, bezel_thickness=5)
        mf_thick = MonitorFrame(1920, 1080, bezel_thickness=30)
        assert mf_thick.screen_rect.width < mf_thin.screen_rect.width

    def test_different_window_sizes(self) -> None:
        mf = MonitorFrame(2560, 1440, bezel_thickness=50)
        assert mf.game_surface.get_size() == (1920, 1080)
        rect = mf.screen_rect
        assert rect.width > 0
        cx = rect.left + rect.width // 2
        cy = rect.top + rect.height // 2
        assert abs(cx - 2560 // 2) < 2
        assert abs(cy - 1440 // 2) < 2

    def test_game_to_window_conversion(self) -> None:
        mf = MonitorFrame(1920, 1080)
        wx, wy = mf.game_to_window(0, 0)
        assert wx == mf.screen_rect.left
        assert wy == mf.screen_rect.top
        wx2, wy2 = mf.game_to_window(1919, 1079)
        assert wx2 <= mf.screen_rect.right
        assert wy2 <= mf.screen_rect.bottom
