"""Visual effects — screen shake, floating numbers, static burst, fade.

All effects are designed to be composited on top of the existing display
surface without modifying it destructively.  Each effect has a duration
and a simple update/render cycle.

Lore framing:  Every visual effect is diegetic — screen shake represents
telemetry interference from nearby explosions, floating numbers are
damage spikes on the telemetry feed, static burst is signal loss during
sector transitions.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

import pygame

from src import config

# ---------------------------------------------------------------------------
# Screen shake
# ---------------------------------------------------------------------------


@dataclass
class ShakeEffect:
    """Random screen offset that decays over time.

    Usage::

        shake = ShakeEffect(intensity=5, duration=0.3)
        # Each frame:
        offset = shake.update(dt)
        surface.blit(game_surface, offset)
        shake.render(surface)  # optional overlay
    """

    intensity: float
    """Maximum pixel offset at peak."""
    duration: float
    """Total duration in seconds."""
    _elapsed: float = 0.0
    _offset_x: float = 0.0
    _offset_y: float = 0.0

    @property
    def finished(self) -> bool:
        """Whether the shake has completed."""
        return self._elapsed >= self.duration

    @property
    def offset(self) -> tuple[int, int]:
        """Current shake offset in pixels."""
        return (round(self._offset_x), round(self._offset_y))

    def update(self, dt: float) -> None:
        """Advance the shake timer and compute new offset.

        Args:
            dt: Delta time since last frame in seconds.
        """
        self._elapsed += dt
        if self.finished:
            self._offset_x = 0.0
            self._offset_y = 0.0
            return
        # Decay factor: linear ramp from 1.0 to 0.0
        decay = 1.0 - (self._elapsed / self.duration)
        self._offset_x = random.uniform(-self.intensity, self.intensity) * decay
        self._offset_y = random.uniform(-self.intensity, self.intensity) * decay


# ---------------------------------------------------------------------------
# Floating damage numbers
# ---------------------------------------------------------------------------


@dataclass
class FloatingNumber:
    """A number that rises and fades on screen.

    Usage::

        fn = FloatingNumber(x=200, y=300, value=6, colour=RED)
        # Each frame:
        fn.update(dt)
        fn.render(surface, font)
    """

    x: int
    """Horizontal position in pixels."""
    y: int
    """Vertical starting position in pixels."""
    value: int
    """The number to display (damage dealt, HP healed, etc.)."""
    colour: tuple[int, int, int] = config.PHOSPHOR_BRIGHT
    """Text colour."""
    duration: float = 0.8
    """Total animation duration in seconds."""
    rise_speed: float = 60.0
    """Pixels per second the number rises."""
    _elapsed: float = 0.0

    @property
    def finished(self) -> bool:
        """Whether the animation has completed."""
        return self._elapsed >= self.duration

    @property
    def alpha(self) -> int:
        """Current alpha (0-255) based on animation progress."""
        if self.finished:
            return 0
        progress = self._elapsed / self.duration
        # Fade in first 20%, then fade out over remaining 80%
        if progress < 0.2:
            return int(255 * (progress / 0.2))
        return int(255 * (1 - (progress - 0.2) / 0.8))

    @property
    def current_y(self) -> int:
        """Current vertical position."""
        return self.y - int(self.rise_speed * self._elapsed)

    def update(self, dt: float) -> None:
        """Advance the animation timer.

        Args:
            dt: Delta time since last frame in seconds.
        """
        self._elapsed += dt

    def render(
        self,
        surface: pygame.Surface,
        font: pygame.font.Font,
    ) -> None:
        """Render the floating number with current alpha.

        Args:
            surface: Target surface.
            font: Font to render the number with.
        """
        if self.finished:
            return
        text = str(abs(self.value))
        raw_surf = font.render(text, True, self.colour)
        # Apply alpha via a separate surface
        alpha_surf = pygame.Surface(raw_surf.get_size(), pygame.SRCALPHA)
        alpha_surf.fill((*self.colour, self.alpha))
        raw_surf.blit(alpha_surf, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        x = self.x - raw_surf.get_width() // 2
        surface.blit(raw_surf, (x, self.current_y))


# ---------------------------------------------------------------------------
# Static burst (full-screen noise)
# ---------------------------------------------------------------------------


@dataclass
class StaticBurst:
    """Full-screen static noise that fades over time.

    Usage::

        static = StaticBurst(duration=0.4)
        # Each frame:
        static.update(dt)
        static.render(surface)
    """

    duration: float = 0.4
    """Total duration in seconds."""
    intensity: float = 1.0
    """Starting opacity (1.0 = fully opaque noise)."""
    _elapsed: float = 0.0
    _noise_surface: pygame.Surface | None = None

    @property
    def finished(self) -> bool:
        """Whether the static burst has completed."""
        return self._elapsed >= self.duration

    def update(self, dt: float, surface_size: tuple[int, int]) -> None:
        """Advance the timer and regenerate noise.

        Args:
            dt: Delta time since last frame in seconds.
            surface_size: (width, height) of the target surface.
        """
        self._elapsed += dt
        if not self.finished:
            w, h = surface_size
            self._noise_surface = pygame.Surface((w, h))
            # Generate random noise pixels
            px_array = pygame.PixelArray(self._noise_surface)
            for x in range(0, w, 2):  # Skip every other for performance
                for y in range(0, h, 2):
                    v = random.randint(0, 60)
                    px_array[x, y] = (v, v + 10, v, 255)  # type: ignore[index]
            del px_array

    def render(self, surface: pygame.Surface) -> None:
        """Blit the noise overlay with fading alpha.

        Args:
            surface: Target surface to overlay.
        """
        if self.finished or self._noise_surface is None:
            return
        decay = 1.0 - (self._elapsed / self.duration)
        alpha = int(255 * self.intensity * decay)
        if alpha <= 0:
            return
        self._noise_surface.set_alpha(alpha)
        surface.blit(self._noise_surface, (0, 0))


# ---------------------------------------------------------------------------
# Signal fade (to black)
# ---------------------------------------------------------------------------


@dataclass
class SignalFade:
    """Fades the screen to black (or from black back to normal).

    Usage::

        fade = SignalFade(duration=0.5, fade_in=True)
        # Each frame:
        fade.update(dt)
        fade.render(surface)
    """

    duration: float = 0.5
    """Total fade duration in seconds."""
    fade_in: bool = False
    """If ``True``, fade from black to clear.  If ``False``, clear to black."""
    _elapsed: float = 0.0
    _black_surface: pygame.Surface | None = None

    @property
    def finished(self) -> bool:
        """Whether the fade has completed."""
        return self._elapsed >= self.duration

    @property
    def alpha(self) -> int:
        """Current overlay alpha (0-255)."""
        if self.finished:
            return 255 if not self.fade_in else 0
        progress = self._elapsed / self.duration
        return int(255 * (1 - progress if self.fade_in else progress))

    def update(self, dt: float, surface_size: tuple[int, int]) -> None:
        """Advance the fade timer.

        Args:
            dt: Delta time since last frame in seconds.
            surface_size: (width, height) for black surface creation.
        """
        self._elapsed += dt
        if self._black_surface is None:
            w, h = surface_size
            self._black_surface = pygame.Surface((w, h))
            self._black_surface.fill((0, 0, 0))

    def render(self, surface: pygame.Surface) -> None:
        """Blit the black overlay at current alpha.

        Args:
            surface: Target surface.
        """
        if self.finished and not self.fade_in:
            # Full black
            if self._black_surface is not None:
                surface.blit(self._black_surface, (0, 0))
            return
        if self._black_surface is None:
            return
        self._black_surface.set_alpha(self.alpha)
        surface.blit(self._black_surface, (0, 0))


# ---------------------------------------------------------------------------
# Phosphor glow (halation around bright pixels)
# ---------------------------------------------------------------------------


class PhosphorGlow:
    """Creates a soft green halo around bright (phosphor green) text.

    This is a pre-computed effect: a blurred copy of the green text is
    rendered behind the sharp text to simulate CRT phosphor persistence.

    Usage::

        glow = PhosphorGlow()
        # When rendering text:
        glow_surf = glow.make_glow(text_surface)
        surface.blit(glow_surf, pos)
        surface.blit(text_surface, pos)
    """

    def __init__(self, spread: int = 2, alpha: int = 40) -> None:
        """Create a PhosphorGlow renderer.

        Args:
            spread: How many pixels the glow extends beyond the text.
            alpha: Base glow opacity (0-255).
        """
        self.spread = spread
        self.alpha = alpha

    def make_glow(self, text_surface: pygame.Surface) -> pygame.Surface:
        """Create a blurred glow copy of *text_surface*.

        Args:
            text_surface: The sharp text surface (must use colour key or
                alpha for transparency).

        Returns:
            A larger surface with the glow layer.
        """
        w, h = text_surface.get_size()
        glow_w = w + self.spread * 2
        glow_h = h + self.spread * 2
        glow_surf = pygame.Surface((glow_w, glow_h), pygame.SRCALPHA)

        # Draw multiple offset copies for blur effect
        offsets = [
            (-1, -1),
            (0, -1),
            (1, -1),
            (-1, 0),
            (1, 0),
            (-1, 1),
            (0, 1),
            (1, 1),
            (-2, 0),
            (2, 0),
            (0, -2),
            (0, 2),
        ]
        for ox, oy in offsets:
            glow_surf.blit(text_surface, (self.spread + ox, self.spread + oy))

        # Tint green and set alpha
        green_tint = pygame.Surface((glow_w, glow_h), pygame.SRCALPHA)
        green_tint.fill((*config.PHOSPHOR_GREEN, self.alpha))
        glow_surf.blit(green_tint, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        return glow_surf
