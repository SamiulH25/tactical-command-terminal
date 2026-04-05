"""Screen transition system — degraded tactical terminal signal effects.

Provides lore-accurate transitions between all game screens.  Each
transition feels like a degraded terminal losing and re-acquiring signal,
complete with static noise, typing animations, and screen shake.

Transition Types
================

- **SIGNAL_LOST** — Combat ends (victory or defeat).  Screen shakes,
  fades to black with increasing static.
- **SIGNAL_ACQUIRE** — Menu navigates to a new screen.  Static fades
  into the new screen with a brief flicker.
- **SECTOR_UPLOAD** — Floor transitions.  Screen wipes to black,
  static burst, then text crawl with sector data.
- **DEPLOYMENT** — Mech select to ship menu.  Brief static, boot-like
  sequence.
- **BRIEF** — Quick transitions (tab switches).  Brief flicker, no text.

Usage
=====

::

    from src.core.transitions import TransitionManager, make_signal_lost

    transitions = TransitionManager()

    # Start a transition
    transitions.start("signal_lost", victory=True, outpost_name="Outpost 7")

    # In the game loop
    while transitions.update(dt):
        transitions.render(screen, behind_surface)

    # Or skip with any key
    transitions.skip()
"""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence

import numpy as np
import pygame

from src.config import FONT_SIZE, FONT_SIZE_SMALL, PHOSPHOR_GREEN
from src.ui.layout import sx, sy

# ---------------------------------------------------------------------------
# Static noise cache — generated once, reused across all transitions
# ---------------------------------------------------------------------------

_static_noise_cache: dict[tuple[int, int], pygame.Surface] = {}
_STATIC_NOISE_COUNT: int = 32  # Number of pre-generated noise frames


def _generate_static_noise_surface(width: int, height: int, alpha: int = 180) -> pygame.Surface:
    """Generate a single frame of static noise.

    Args:
        width: Surface width in pixels.
        height: Surface height in pixels.
        alpha: Opacity of the noise overlay (0-255).

    Returns:
        A pygame Surface with static noise.
    """
    surface = pygame.Surface((width, height), pygame.SRCALPHA)
    # Generate noise with numpy — green phosphor static
    noise = np.random.randint(0, 255, (height, width), dtype=np.uint8)
    # Make it mostly transparent with occasional bright pixels
    noise_array = np.zeros((height, width, 4), dtype=np.uint8)
    noise_array[:, :, 0] = 38  # Green channel base
    noise_array[:, :, 1] = 217  # Green channel
    noise_array[:, :, 2] = 64  # Blue tint
    noise_array[:, :, 3] = np.where(noise > 200, alpha, 0)

    noise_surface = pygame.image.frombuffer(noise_array.tobytes(), (width, height), "RGBA")
    surface.blit(noise_surface, (0, 0))
    return surface


def _get_static_noise_frames(width: int, height: int) -> list[pygame.Surface]:
    """Get cached static noise frames, generating if needed.

    Args:
        width: Frame width in pixels.
        height: Frame height in pixels.

    Returns:
        List of noise surface frames.
    """
    cache_key = (width, height)
    if cache_key not in _static_noise_cache:
        frames: list[pygame.Surface] = []
        for _ in range(_STATIC_NOISE_COUNT):
            frames.append(_generate_static_noise_surface(width, height))
        _static_noise_cache[cache_key] = frames  # type: ignore[assignment]
    return _static_noise_cache[cache_key]  # type: ignore[return-value]


def _get_noise_frame(width: int, height: int, frame_index: int) -> pygame.Surface:
    """Get a single noise frame by index (cycles through cached frames).

    Args:
        width: Frame width.
        height: Frame height.
        frame_index: Frame index (wraps around cache size).

    Returns:
        A noise surface frame.
    """
    frames = _get_static_noise_frames(width, height)
    return frames[frame_index % len(frames)]


# ---------------------------------------------------------------------------
# Typing animation helper
# ---------------------------------------------------------------------------


class _TypingAnimation:
    """Manages character-by-character typing animation for text lines.

    Each line appears one character at a time, like text being received
    over a slow tactical feed.
    """

    def __init__(
        self,
        lines: Sequence[str],
        chars_per_second: float = 60.0,
        line_delay: float = 0.15,
    ) -> None:
        """Initialise the typing animation.

        Args:
            lines: Text lines to animate.
            chars_per_second: Typing speed in characters per second.
            line_delay: Pause between lines in seconds.
        """
        self._lines = list(lines)
        self._chars_per_second = chars_per_second
        self._line_delay = line_delay
        self._elapsed: float = 0.0
        self._current_char: int = 0
        self._current_line: int = 0
        self._line_start_times: list[float] = []

    @property
    def is_complete(self) -> bool:
        """Whether all lines have been fully typed."""
        return self._current_line >= len(self._lines)

    @property
    def current_char_count(self) -> int:
        """Number of characters visible on the current line."""
        if self._current_line >= len(self._lines):
            return 0
        return min(self._current_char, len(self._lines[self._current_line]))

    @property
    def current_line_index(self) -> int:
        """Index of the line currently being typed."""
        return min(self._current_line, len(self._lines) - 1)

    def update(self, dt: float) -> None:
        """Advance the typing animation.

        Args:
            dt: Delta time in seconds.
        """
        if self.is_complete:
            return

        self._elapsed += dt

        # Calculate total characters that should be visible
        char_time = 1.0 / self._chars_per_second
        total_chars = int(self._elapsed / char_time)

        # Distribute characters across lines
        remaining = total_chars
        self._current_line = 0
        self._current_char = 0

        for i, line in enumerate(self._lines):
            line_len = len(line)
            if remaining >= line_len:
                remaining -= line_len
                self._current_line = i + 1
                self._current_char = 0
            else:
                self._current_line = i
                self._current_char = remaining
                return

        # All characters displayed
        self._current_line = len(self._lines)
        self._current_char = 0

    def get_visible_text(self) -> list[str]:
        """Get the text as it should currently appear.

        Returns:
            List of lines with partial characters for the active line.
        """
        result: list[str] = []
        for i, line in enumerate(self._lines):
            if i < self._current_line:
                result.append(line)
            elif i == self._current_line:
                result.append(line[: self.current_char_count])
            else:
                break
        return result


# ---------------------------------------------------------------------------
# TransitionEffect
# ---------------------------------------------------------------------------


class TransitionEffect:
    """A single screen transition effect.

    Encapsulates the visual effect, text animation, and timing for one
    transition instance.
    """

    def __init__(
        self,
        transition_type: str,
        text_lines: list[str],
        duration: float,
        shake: bool = False,
        shake_duration: float = 0.0,
        shake_intensity: int = 0,
        fade_in: bool = False,
        fade_out: bool = False,
        text_start_delay: float = 0.0,
        text_chars_per_second: float = 60.0,
    ) -> None:
        """Create a transition effect.

        Args:
            transition_type: One of the transition type constants.
            text_lines: Lines of text to display with typing animation.
            duration: Total transition duration in seconds.
            shake: Whether to apply screen shake.
            shake_duration: How long the shake lasts (seconds).
            shake_intensity: Maximum pixel offset for shake.
            fade_in: Whether to fade from black at the start.
            fade_out: Whether to fade to black at the end.
            text_start_delay: Delay before text typing begins (seconds).
            text_chars_per_second: Typing speed for text animation.
        """
        self.transition_type = transition_type
        self.text_lines = text_lines
        self.duration = duration
        self.shake = shake
        self.shake_duration = shake_duration
        self.shake_intensity = shake_intensity
        self.fade_in = fade_in
        self.fade_out = fade_out
        self.text_start_delay = text_start_delay
        self.text_chars_per_second = text_chars_per_second

        self._elapsed: float = 0.0
        self._typing = _TypingAnimation(text_lines, text_chars_per_second)
        self._noise_frame: int = 0
        self._skipped: bool = False

    @property
    def is_complete(self) -> bool:
        """Whether the transition has finished or been skipped."""
        return self._skipped or self._elapsed >= self.duration

    @property
    def alpha(self) -> int:
        """Current fade alpha (0-255)."""
        if self.fade_in and self._elapsed < self.duration * 0.3:
            return int(255 * (1.0 - self._elapsed / (self.duration * 0.3)))
        if self.fade_out and self._elapsed > self.duration * 0.7:
            progress = (self._elapsed - self.duration * 0.7) / (self.duration * 0.3)
            return int(255 * min(1.0, progress))
        if self.fade_out:
            return 0
        if self.fade_in:
            return 255
        # For non-fade transitions, compute static intensity
        return self._compute_static_alpha()

    def _compute_static_alpha(self) -> int:
        """Compute static noise overlay alpha based on transition phase."""
        if self._elapsed < self.duration * 0.2:
            # Ramp up
            return int(180 * (self._elapsed / (self.duration * 0.2)))
        if self._elapsed > self.duration * 0.8:
            # Ramp down
            progress = (self._elapsed - self.duration * 0.8) / (self.duration * 0.2)
            return int(180 * (1.0 - progress))
        return 180

    def update(self, dt: float) -> bool:
        """Advance the transition.

        Args:
            dt: Delta time in seconds.

        Returns:
            True when the transition is complete.
        """
        if self._skipped:
            return True

        self._elapsed += dt
        self._noise_frame += 1

        # Update typing animation (with delay)
        if self._elapsed >= self.text_start_delay:
            typing_dt = min(dt, self._elapsed - self.text_start_delay)
            self._typing.update(typing_dt)

        return self.is_complete

    def render(self, surface: pygame.Surface) -> None:
        """Render the transition effect onto the surface.

        Args:
            surface: The target surface to render onto.
        """
        if self._skipped:
            return

        width, height = surface.get_size()

        # Screen shake offset
        shake_offset = (0, 0)
        if self.shake and self._elapsed < self.shake_duration:
            shake_progress = self._elapsed / self.shake_duration
            intensity = int(self.shake_intensity * (1.0 - shake_progress))
            if intensity > 0:
                shake_offset = (
                    int(math.sin(self._elapsed * 50) * intensity),
                    int(math.cos(self._elapsed * 43) * intensity),
                )

        # Render static noise overlay
        static_alpha = self.alpha
        if static_alpha > 0:
            noise = _get_noise_frame(width, height, self._noise_frame)
            noise_copy = noise.copy()
            noise_copy.set_alpha(static_alpha)
            surface.blit(noise_copy, shake_offset)

        # Render text with typing animation
        visible_text = self._typing.get_visible_text()
        if visible_text:
            self._render_text(surface, visible_text, shake_offset)

        # Fade overlay
        if self.fade_in or self.fade_out:
            fade_alpha = self.alpha
            if fade_alpha > 0:
                fade_surface = pygame.Surface((width, height), pygame.SRCALPHA)
                fade_surface.fill((0, 0, 0, fade_alpha))
                surface.blit(fade_surface, (0, 0))

    def _render_text(
        self,
        surface: pygame.Surface,
        visible_text: list[str],
        offset: tuple[int, int],
    ) -> None:
        """Render typed text lines centered on screen.

        Args:
            surface: Target surface.
            visible_text: Lines of text to render (may be partial).
            offset: Screen shake offset.
        """
        font = pygame.font.Font(None, FONT_SIZE)
        small_font = pygame.font.Font(None, FONT_SIZE_SMALL)

        line_height = sx(30)
        start_y = sy(400)
        start_x = sx(100)

        for i, line in enumerate(visible_text):
            if not line:
                continue

            # Use smaller font for secondary lines
            use_font = font if i == 0 or line.startswith("> ") else small_font
            color = PHOSPHOR_GREEN
            text_surface = use_font.render(line, True, color)

            y_pos = start_y + i * line_height
            surface.blit(text_surface, (start_x + offset[0], y_pos + offset[1]))

            # Blinking cursor on the last line
            if i == len(visible_text) - 1 and not self._typing.is_complete:
                cursor_x = start_x + text_surface.get_width() + offset[0]
                cursor_y = y_pos + offset[1]
                if int(self._elapsed * 4) % 2 == 0:
                    cursor_surf = font.render("_", True, PHOSPHOR_GREEN)
                    surface.blit(cursor_surf, (cursor_x, cursor_y))

    def skip(self) -> None:
        """Skip the transition immediately."""
        self._skipped = True


# ---------------------------------------------------------------------------
# Factory functions
# ---------------------------------------------------------------------------


def make_signal_lost(victory: bool, outpost_name: str = "") -> TransitionEffect:
    """Create a SIGNAL_LOST transition for combat end.

    Args:
        victory: True for victory, False for defeat.
        outpost_name: Optional outpost name for flavor text.

    Returns:
        A configured TransitionEffect.
    """
    if victory:
        text_lines = [
            "> HOSTILES NEUTRALIZED",
            "> SECTOR CLEARED",
            "> RETURNING TO COMMAND FEED...",
        ]
    else:
        text_lines = [
            "> SIGNAL LOST",
            "> ALL UNITS OFFLINE",
            "> TELEMETRY FAILURE",
        ]

    return TransitionEffect(
        transition_type="signal_lost",
        text_lines=text_lines,
        duration=1.5,
        shake=True,
        shake_duration=0.4,
        shake_intensity=sx(8),
        fade_out=True,
        text_start_delay=0.3,
        text_chars_per_second=80.0,
    )


def make_signal_acquire() -> TransitionEffect:
    """Create a SIGNAL_ACQUIRE transition for menu navigation.

    Returns:
        A configured TransitionEffect.
    """
    return TransitionEffect(
        transition_type="signal_acquire",
        text_lines=[
            "> CONNECTING TO TACTICAL FEED...",
            "> LINK ESTABLISHED",
        ],
        duration=1.0,
        fade_in=True,
        text_start_delay=0.1,
        text_chars_per_second=100.0,
    )


def make_sector_upload(
    floor_num: int,
    narrative_intro: str = "",
) -> TransitionEffect:
    """Create a SECTOR_UPLOAD transition for floor changes.

    Args:
        floor_num: The floor/sector number being loaded.
        narrative_intro: Optional narrative intro text.

    Returns:
        A configured TransitionEffect.
    """
    text_lines = [
        "> UPLOADING SECTOR DATA...",
        f"> SECTOR {floor_num:02d} LOADED",
    ]
    if narrative_intro:
        text_lines.append(narrative_intro)
    text_lines.append("> SIGNAL RE-ACQUIRED")

    return TransitionEffect(
        transition_type="sector_upload",
        text_lines=text_lines,
        duration=2.0,
        fade_out=True,
        fade_in=True,
        text_start_delay=0.2,
        text_chars_per_second=70.0,
    )


def make_deployment() -> TransitionEffect:
    """Create a DEPLOYMENT transition for mech select to ship menu.

    Returns:
        A configured TransitionEffect.
    """
    return TransitionEffect(
        transition_type="deployment",
        text_lines=[
            "> DEPLOYMENT CONFIRMED",
            "> CONNECTING TO TACTICAL FEED...",
            "> LINK ESTABLISHED",
        ],
        duration=1.5,
        fade_in=True,
        text_start_delay=0.15,
        text_chars_per_second=90.0,
    )


def make_brief() -> TransitionEffect:
    """Create a BRIEF transition for quick screen changes (tab switches).

    Returns:
        A configured TransitionEffect with no text.
    """
    return TransitionEffect(
        transition_type="brief",
        text_lines=[],
        duration=0.3,
        text_start_delay=999.0,  # Never show text
    )


# ---------------------------------------------------------------------------
# TransitionManager
# ---------------------------------------------------------------------------


class TransitionManager:
    """Manages active screen transitions.

    Only one transition can be active at a time.  The manager handles
    timing, rendering, and skipping.
    """

    def __init__(self) -> None:
        """Create a TransitionManager with no active transition."""
        self._active: TransitionEffect | None = None

    @property
    def is_active(self) -> bool:
        """Whether a transition is currently running."""
        return self._active is not None and not self._active.is_complete

    def start(self, transition_type: str, **kwargs: object) -> None:
        """Start a new transition.

        Args:
            transition_type: One of: ``signal_lost``, ``signal_acquire``,
                ``sector_upload``, ``deployment``, ``brief``.
            **kwargs: Arguments forwarded to the factory function.
                - For ``signal_lost``: ``victory`` (bool),
                  ``outpost_name`` (str).
                - For ``sector_upload``: ``floor_num`` (int),
                  ``narrative_intro`` (str).

        Raises:
            ValueError: If the transition type is unknown.
        """
        factory_map: dict[str, Callable[..., TransitionEffect]] = {
            "signal_lost": make_signal_lost,
            "signal_acquire": make_signal_acquire,
            "sector_upload": make_sector_upload,
            "deployment": make_deployment,
            "brief": make_brief,
        }

        if transition_type not in factory_map:
            raise ValueError(
                f"Unknown transition type: {transition_type!r}. "
                f"Valid types: {list(factory_map.keys())}"
            )

        self._active = factory_map[transition_type](**kwargs)

    def update(self, dt: float) -> bool:
        """Advance the active transition.

        Args:
            dt: Delta time in seconds.

        Returns:
            True if a transition is active (even if it just completed).
        """
        if self._active is None:
            return False

        self._active.update(dt)

        if self._active.is_complete:
            self._active = None
            return False

        return True

    def render(
        self,
        surface: pygame.Surface,
        behind_surface: pygame.Surface | None = None,
    ) -> None:
        """Render the active transition.

        Args:
            surface: The surface to render the transition onto.
            behind_surface: Optional surface behind the transition.
                If provided, the transition renders on top of it.
        """
        if self._active is None:
            return

        # If there's a behind surface, blit it first
        if behind_surface is not None:
            surface.blit(behind_surface, (0, 0))

        self._active.render(surface)

    def skip(self) -> None:
        """Skip the active transition immediately."""
        if self._active is not None:
            self._active.skip()
            self._active = None

    def handle_event(self, event: pygame.Event) -> bool:
        """Handle a pygame event for transition skipping.

        Args:
            event: A pygame event.

        Returns:
            True if the transition was skipped.
        """
        if self._active is None:
            return False

        if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
            self.skip()
            return True

        return False
