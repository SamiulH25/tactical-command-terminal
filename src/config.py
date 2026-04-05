"""Global configuration constants for Tactical Command Terminal.

All magic numbers and tunable parameters live here.
Values may be overridden at runtime for testing purposes.
"""

# ---------------------------------------------------------------------------
# Display
# ---------------------------------------------------------------------------

#: Horizontal resolution in pixels.  The game content is 1920x1080;
#: the window wraps it in a monitor bezel.
SCREEN_WIDTH: int = 1920

#: Vertical resolution in pixels.
SCREEN_HEIGHT: int = 1080

#: Frames per second target for the main loop.
TARGET_FPS: int = 60

#: Fullscreen mode — ``True`` for exclusive fullscreen, ``False`` for windowed.
FULLSCREEN: bool = False

#: Monitor bezel thickness in pixels.  Provides a subtle border around
#: the game content to simulate a physical monitor frame.
MONITOR_BEZEL: int = 20

# ---------------------------------------------------------------------------
# Fonts
# ---------------------------------------------------------------------------

#: Primary monospace terminal font file path (relative to project root).
#: Falls back to system monospace if unavailable.
FONT_PATH: str = "assets/fonts/terminus.ttf"

#: Base font size for body text in pixels.  Scaled for 1080p.
FONT_SIZE: int = 20

#: Font size for headers and panel titles.
FONT_SIZE_HEADER: int = 26

#: Font size for small labels and footers.
FONT_SIZE_SMALL: int = 16

# ---------------------------------------------------------------------------
# CRT Effects
# ---------------------------------------------------------------------------

#: Scanline opacity — alpha value for dark horizontal lines (0-255).
#: Higher values make scanlines more visible and oppressive.
SCANLINE_ALPHA: int = 90

#: Scanline spacing — every Nth row gets a darkened line.
#: 2 = every other row (classic CRT look).
SCANLINE_SPACING: int = 2

#: Flicker intensity — max percentage brightness oscillation per frame.
#: Higher values make the screen pulse more noticeably.
FLICKER_INTENSITY: float = 0.08

#: Flicker frequency in Hz — how often brightness oscillates.
#: 3 Hz mimics power-line hum interference.
FLICKER_FREQUENCY: float = 3.0

#: Vignette darkness at screen edges (0.0 = none, 1.0 = fully black).
#: Simulates CRT tube falloff at the edges.
VIGNETTE_STRENGTH: float = 0.4

#: Chromatic aberration offset in pixels per color channel.
#: 0 = no aberration, 1-2 = subtle RGB channel splitting.
CHROMATIC_ABERRATION: float = 1.2

#: Barrel distortion intensity (0.0 = flat, 0.3 = heavy CRT curve).
#: Currently disabled — row-shift approximation breaks surface content.
BARREL_DISTORTION: float = 0.0

#: Noise grain opacity (0.0-1.0).  Per-frame animated film grain.
NOISE_GRAIN_OPACITY: float = 0.06

#: Phosphor bloom spread in pixels.  How far bright text "glows".
PHOSPHOR_BLOOM_SPREAD: int = 3

#: Phosphor bloom intensity (0.0-1.0).  Brightness of the glow.
PHOSPHOR_BLOOM_INTENSITY: float = 0.5

#: Afterimage persistence (0.0-1.0).  Previous frame lingers as ghost.
AFTERIMAGE_STRENGTH: float = 0.12

#: Signal glitch probability per frame (0.0 = never, 1.0 = always).
#: A glitch is a horizontal tracking line that briefly appears.
SIGNAL_GLITCH_CHANCE: float = 0.003

# ---------------------------------------------------------------------------
# Terminal colour palette — green-phosphor CRT
# ---------------------------------------------------------------------------

#: Primary terminal text colour — green phosphor.
PHOSPHOR_GREEN: tuple[int, int, int] = (38, 217, 64)

#: Dimmed text — inactive labels, secondary info.
PHOSPHOR_DIM: tuple[int, int, int] = (20, 115, 38)

#: Bright text — hover states, active elements.
PHOSPHOR_BRIGHT: tuple[int, int, int] = (51, 255, 87)

#: Enemy / hostile indicator colour.
COLOR_ENEMY: tuple[int, int, int] = (230, 51, 51)

#: Warning / overload indicator colour — amber.
COLOR_WARNING: tuple[int, int, int] = (217, 140, 26)

#: Friendly unit indicator colour — cyan.
COLOR_FRIENDLY: tuple[int, int, int] = (51, 204, 153)

#: Disabled / locked content colour.
COLOR_DISABLED: tuple[int, int, int] = (102, 102, 102)

#: Screen background colour — near-black.
COLOR_BG: tuple[int, int, int] = (5, 8, 3)

#: Panel background colour — dark green-black.
COLOR_PANEL_BG: tuple[int, int, int] = (8, 12, 4)
