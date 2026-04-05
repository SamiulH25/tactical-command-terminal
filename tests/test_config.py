"""Tests for the configuration module.

Ensures all constants have valid values and are internally consistent.
"""

from src import config


class TestDisplayConfig:
    """Verify display configuration values."""

    def test_screen_dimensions_positive(self) -> None:
        """Screen width and height must be positive integers."""
        assert config.SCREEN_WIDTH > 0
        assert config.SCREEN_HEIGHT > 0
        assert isinstance(config.SCREEN_WIDTH, int)
        assert isinstance(config.SCREEN_HEIGHT, int)

    def test_target_fps_positive(self) -> None:
        """Target FPS must be a positive integer."""
        assert config.TARGET_FPS > 0
        assert isinstance(config.TARGET_FPS, int)


class TestFontConfig:
    """Verify font configuration values."""

    def test_font_path_non_empty(self) -> None:
        """Font path must be a non-empty string."""
        assert isinstance(config.FONT_PATH, str)
        assert len(config.FONT_PATH) > 0

    def test_font_sizes_positive(self) -> None:
        """All font sizes must be positive integers."""
        assert config.FONT_SIZE > 0
        assert config.FONT_SIZE_HEADER > 0
        assert config.FONT_SIZE_SMALL > 0

    def test_font_size_ordering(self) -> None:
        """Header font should be largest, small font smallest."""
        assert config.FONT_SIZE_SMALL < config.FONT_SIZE
        assert config.FONT_SIZE < config.FONT_SIZE_HEADER


class TestCRTConfig:
    """Verify CRT effect configuration values."""

    def test_scanline_alpha_range(self) -> None:
        """Scanline alpha must be in valid range (0-255)."""
        assert 0 < config.SCANLINE_ALPHA <= 255

    def test_scanline_spacing_positive(self) -> None:
        """Scanline spacing must be a positive integer."""
        assert config.SCANLINE_SPACING > 0

    def test_flicker_intensity_range(self) -> None:
        """Flicker intensity must be between 0 and 1."""
        assert 0 < config.FLICKER_INTENSITY < 1.0

    def test_flicker_frequency_positive(self) -> None:
        """Flicker frequency must be positive."""
        assert config.FLICKER_FREQUENCY > 0


class TestColorPalette:
    """Verify all color values are valid RGB tuples."""

    def _assert_valid_rgb(self, color: tuple[int, int, int], name: str) -> None:
        """Assert that a value is a valid 3-component RGB tuple."""
        assert isinstance(color, tuple), f"{name} must be a tuple, got {type(color)}"
        assert len(color) == 3, f"{name} must have 3 components, got {len(color)}"
        for i, channel in enumerate(color):
            assert isinstance(channel, int), f"{name}[{i}] must be int"
            assert 0 <= channel <= 255, f"{name}[{i}] = {channel} out of range [0,255]"

    def test_phosphor_green(self) -> None:
        self._assert_valid_rgb(config.PHOSPHOR_GREEN, "PHOSPHOR_GREEN")

    def test_phosphor_dim(self) -> None:
        self._assert_valid_rgb(config.PHOSPHOR_DIM, "PHOSPHOR_DIM")

    def test_phosphor_bright(self) -> None:
        self._assert_valid_rgb(config.PHOSPHOR_BRIGHT, "PHOSPHOR_BRIGHT")

    def test_color_enemy(self) -> None:
        self._assert_valid_rgb(config.COLOR_ENEMY, "COLOR_ENEMY")

    def test_color_warning(self) -> None:
        self._assert_valid_rgb(config.COLOR_WARNING, "COLOR_WARNING")

    def test_color_friendly(self) -> None:
        self._assert_valid_rgb(config.COLOR_FRIENDLY, "COLOR_FRIENDLY")

    def test_color_disabled(self) -> None:
        self._assert_valid_rgb(config.COLOR_DISABLED, "COLOR_DISABLED")

    def test_color_bg(self) -> None:
        self._assert_valid_rgb(config.COLOR_BG, "COLOR_BG")

    def test_color_panel_bg(self) -> None:
        self._assert_valid_rgb(config.COLOR_PANEL_BG, "COLOR_PANEL_BG")
