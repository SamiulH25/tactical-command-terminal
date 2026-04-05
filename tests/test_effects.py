"""Tests for the visual effects module."""

import pygame

from src.core.effects import (
    FloatingNumber,
    PhosphorGlow,
    ShakeEffect,
    SignalFade,
    StaticBurst,
)

# ---------------------------------------------------------------------------
# ShakeEffect
# ---------------------------------------------------------------------------


class TestShakeEffect:
    """Verify screen shake behaviour."""

    def test_initial_state(self) -> None:
        """Shake should not be finished at start."""
        s = ShakeEffect(intensity=5, duration=0.3)
        assert s.finished is False
        assert s.offset == (0, 0)

    def test_offset_nonzero_after_update(self) -> None:
        """After update, offset should be non-zero."""
        s = ShakeEffect(intensity=5, duration=0.3)
        s.update(0.05)
        dx, dy = s.offset
        assert abs(dx) + abs(dy) > 0

    def test_finished_after_duration(self) -> None:
        """Shake should finish after its duration."""
        s = ShakeEffect(intensity=5, duration=0.3)
        s.update(0.31)
        assert s.finished is True
        assert s.offset == (0, 0)

    def test_decay_reduces_max_offset(self) -> None:
        """Later updates should produce smaller maximum offsets."""
        s = ShakeEffect(intensity=10, duration=0.5)
        s.update(0.05)
        # At 10% of duration, decay = 0.9, max offset = 9
        assert abs(s.offset[0]) <= 10
        s.update(0.3)
        # At 70% of duration, decay = 0.3, max offset = 3
        assert abs(s.offset[0]) <= 3


# ---------------------------------------------------------------------------
# FloatingNumber
# ---------------------------------------------------------------------------


class TestFloatingNumber:
    """Verify floating damage number animation."""

    def test_initial_state(self) -> None:
        """Should start at full alpha and starting position."""
        fn = FloatingNumber(x=100, y=200, value=6)
        assert fn.finished is False
        assert fn.alpha == 0  # Starts at 0, fades in

    def test_alpha_reaches_max(self) -> None:
        """Alpha should reach 255 during first 20% of animation."""
        fn = FloatingNumber(x=100, y=200, value=6, duration=1.0)
        fn.update(0.2)  # Exactly 20%
        assert fn.alpha == 255

    def test_alpha_fades_to_zero(self) -> None:
        """Alpha should be 0 when animation completes."""
        fn = FloatingNumber(x=100, y=200, value=6, duration=0.5)
        fn.update(0.5)
        assert fn.finished is True
        assert fn.alpha == 0

    def test_y_rises(self) -> None:
        """The number should rise over time."""
        fn = FloatingNumber(x=100, y=200, value=6, rise_speed=100)
        fn.update(0.5)
        assert fn.current_y < 200

    def test_render_no_crash(self) -> None:
        """Rendering must not raise."""
        pygame.font.init()
        font = pygame.font.Font(None, 24)
        fn = FloatingNumber(x=100, y=200, value=12)
        surf = pygame.Surface((200, 200))
        fn.update(0.1)
        fn.render(surf, font)


# ---------------------------------------------------------------------------
# StaticBurst
# ---------------------------------------------------------------------------


class TestStaticBurst:
    """Verify static burst noise effect."""

    def test_initial_state(self) -> None:
        """Should not be finished at start."""
        s = StaticBurst(duration=0.3)
        assert s.finished is False

    def test_finished_after_duration(self) -> None:
        """Should finish after duration."""
        s = StaticBurst(duration=0.3)
        s.update(0.31, (100, 100))
        assert s.finished is True

    def test_render_no_crash(self) -> None:
        """Rendering must not raise."""
        s = StaticBurst(duration=0.3)
        s.update(0.1, (100, 100))
        surf = pygame.Surface((100, 100))
        s.render(surf)

    def test_render_after_finish_no_crash(self) -> None:
        """Rendering after completion must not raise."""
        s = StaticBurst(duration=0.2)
        s.update(0.3, (100, 100))
        surf = pygame.Surface((100, 100))
        s.render(surf)  # Should be a no-op


# ---------------------------------------------------------------------------
# SignalFade
# ---------------------------------------------------------------------------


class TestSignalFade:
    """Verify fade to/from black."""

    def test_fade_out_starts_clear(self) -> None:
        """Fade out should start at alpha 0."""
        f = SignalFade(duration=0.5, fade_in=False)
        assert f.alpha == 0

    def test_fade_out_completes_black(self) -> None:
        """Fade out should end at full alpha."""
        f = SignalFade(duration=0.5, fade_in=False)
        f.update(0.5, (100, 100))
        assert f.finished is True
        assert f.alpha == 255

    def test_fade_in_starts_black(self) -> None:
        """Fade in should start at alpha 255."""
        f = SignalFade(duration=0.5, fade_in=True)
        assert f.alpha == 255

    def test_fade_in_completes_clear(self) -> None:
        """Fade in should end at alpha 0."""
        f = SignalFade(duration=0.5, fade_in=True)
        f.update(0.5, (100, 100))
        assert f.finished is True
        assert f.alpha == 0

    def test_render_no_crash(self) -> None:
        """Rendering must not raise."""
        f = SignalFade(duration=0.3, fade_in=False)
        f.update(0.15, (100, 100))
        surf = pygame.Surface((100, 100))
        f.render(surf)


# ---------------------------------------------------------------------------
# PhosphorGlow
# ---------------------------------------------------------------------------


class TestPhosphorGlow:
    """Verify phosphor glow generation."""

    def test_glow_larger_than_text(self) -> None:
        """Glow surface should be larger than the text by spread."""
        pygame.font.init()
        font = pygame.font.Font(None, 20)
        text_surf = font.render("TEST", True, (255, 255, 255))
        glow = PhosphorGlow(spread=2)
        glow_surf = glow.make_glow(text_surf)
        assert glow_surf.get_width() > text_surf.get_width()
        assert glow_surf.get_height() > text_surf.get_height()

    def test_glow_has_alpha(self) -> None:
        """Glow surface should use SRCALPHA."""
        pygame.font.init()
        font = pygame.font.Font(None, 20)
        text_surf = font.render("TEST", True, (255, 255, 255))
        glow = PhosphorGlow(spread=2, alpha=40)
        glow_surf = glow.make_glow(text_surf)
        assert glow_surf.get_flags() & pygame.SRCALPHA
