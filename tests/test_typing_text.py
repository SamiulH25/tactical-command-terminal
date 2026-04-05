"""Tests for the TypingText typewriter effect."""

import pygame

from src.ui.typing_text import TypingText


class TestTypingText:
    """Verify typewriter text behaviour."""

    def test_instant_reveal_at_zero_speed(self) -> None:
        """Zero speed should reveal all text immediately."""
        pygame.font.init()
        font = pygame.font.Font(None, 20)
        tt = TypingText("Hello", font, chars_per_second=0.0)
        assert tt.finished is True
        assert tt.progress == 1.0

    def test_reveal_progress(self) -> None:
        """Progress should increase over time."""
        pygame.font.init()
        font = pygame.font.Font(None, 20)
        tt = TypingText("Hello World Test", font, chars_per_second=10.0)
        assert tt.finished is False
        tt.update(0.5)
        assert 0.0 < tt.progress < 1.0
        assert tt.finished is False

    def test_finish_after_duration(self) -> None:
        """Should finish after enough time."""
        pygame.font.init()
        font = pygame.font.Font(None, 20)
        text = "Hello"
        tt = TypingText(text, font, chars_per_second=5.0)
        tt.update(2.0)  # 5 * 2 = 10 > 5 chars
        assert tt.finished is True
        assert tt.progress == 1.0

    def test_skip_reveals_all(self) -> None:
        """Skipping should instantly finish."""
        pygame.font.init()
        font = pygame.font.Font(None, 20)
        tt = TypingText("Hello World", font, chars_per_second=1.0)
        assert not tt.finished
        tt.skip()
        assert tt.finished

    def test_skip_not_allowed(self) -> None:
        """Non-skippable text should not skip."""
        pygame.font.init()
        font = pygame.font.Font(None, 20)
        tt = TypingText("Hello", font, skippable=False)
        tt.skip()
        assert not tt.finished

    def test_render_no_crash(self) -> None:
        """Rendering must not raise and return a valid rect."""
        pygame.font.init()
        font = pygame.font.Font(None, 20)
        tt = TypingText("Hello Coordinator", font, chars_per_second=20.0)
        surf = pygame.Surface((400, 200))
        tt.update(2.0)  # Fully reveal
        rect = tt.render(surf, 10, 10)
        assert rect.width > 0
        assert rect.height > 0

    def test_handle_event_skips_on_click(self) -> None:
        """Mouse click should skip text when skippable."""
        pygame.font.init()
        font = pygame.font.Font(None, 20)
        tt = TypingText("Hello", font, chars_per_second=0.5)
        event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 1})
        tt.handle_event(event)
        assert tt.finished

    def test_handle_event_skips_on_key(self) -> None:
        """Key press should skip text when skippable."""
        pygame.font.init()
        font = pygame.font.Font(None, 20)
        tt = TypingText("Hello", font, chars_per_second=0.5)
        event = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_SPACE})
        tt.handle_event(event)
        assert tt.finished

    def test_multiline_text(self) -> None:
        """Multiline text should be counted correctly."""
        pygame.font.init()
        font = pygame.font.Font(None, 20)
        tt = TypingText("Line one\nLine two", font, chars_per_second=20.0)
        # 8 + 8 = 16 chars (no newline counted)
        assert tt._total_chars == 16
        tt.update(2.0)
        assert tt.finished

    def test_wrapped_text(self) -> None:
        """Long text should wrap when max_width is set."""
        pygame.font.init()
        font = pygame.font.Font(None, 20)
        long_text = "This is a very long sentence that should wrap"
        tt = TypingText(long_text, font, max_width=200)
        assert len(tt._wrapped_lines) >= 1
        total = sum(len(line) for line in tt._wrapped_lines)
        # Wrapped lines preserve chars (minus spaces added during wrapping)
        assert total >= len(long_text) - 5
