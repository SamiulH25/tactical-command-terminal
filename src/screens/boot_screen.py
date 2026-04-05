"""Boot sequence screen — simulated terminal startup before the main menu.

Displays a staged boot sequence with typing text, progress bars, and
system check messages.  Skippable with any keypress.  Auto-advances
to the main menu when complete.

Boot sequence format::

    > FSA TACTICAL TERMINAL v2.7.1
    > POST INITIATED...
    > MEMORY TEST: 65536K OK
    > NEURAL UPLINK: ESTABLISHING...
    > ENCRYPTION MODULE: LOADED
    > AUTHENTICATING OPERATOR...
    > IDENTITY CONFIRMED: COORDINATOR
    > DOWNLOADING TACTICAL DATABASE...
    > WAR ROOM COMMS: ONLINE
    > LINK ACTIVE
"""

from __future__ import annotations

from collections.abc import Callable
from typing import ClassVar

import pygame

from src import config
from src.core.terminal import TerminalRenderer
from src.screens.base_screen import Screen
from src.ui.layout import sx, sy


class BootScreen(Screen):
    """A simulated computer boot sequence shown before the main menu."""

    #: Individual boot lines with display timing (ms delay after each line).
    BOOT_LINES: ClassVar[list[tuple[str, int]]] = [
        ("> FSA TACTICAL TERMINAL v2.7.1", 300),
        ("", 100),
        ("> BIOS POST INITIATED...", 200),
        ("> MEMORY TEST: 65536K OK", 250),
        ("> CRYSTAL ARRAY: NOMINAL", 200),
        ("", 100),
        ("> NEURAL UPLINK: ESTABLISHING...", 600),
        ("> NEURAL UPLINK: ESTABLISHED", 200),
        ("> ENCRYPTION MODULE: AES-512-GCM LOADED", 300),
        ("> QUANTUM ENTANGLEMENT: SYNCED", 250),
        ("", 100),
        ("> AUTHENTICATING OPERATOR...", 500),
        ("> BIOMETRIC SCAN: COMPLETE", 300),
        ("> IDENTITY CONFIRMED: COORDINATOR", 400),
        ("> CLEARANCE: OMEGA-7", 250),
        ("", 100),
        ("> DOWNLOADING TACTICAL DATABASE...", 700),
        ("> 12 MECH FRAMES LOADED", 200),
        ("> 16 DIRECTIVES INDEXED", 200),
        ("> 14 EQUIPMENT MODULES VERIFIED", 200),
        ("> 5 PILOT PROFILES SYNCED", 200),
        ("", 100),
        ("> WAR ROOM COMMS: ONLINE", 300),
        ("> FSA BROADCAST CHANNEL: ACTIVE", 250),
        ("> INTERCEPT CHANNELS: MONITORING", 250),
        ("", 100),
        ("> SIGNAL RE-ACQUIRED", 300),
        ("> LINK ACTIVE", 500),
        ("", 200),
        ("> HELLO, COORDINATOR.", 800),
        ("", 300),
        ("> SYSTEM BY BOB2142", 2500),
    ]

    def __init__(
        self,
        renderer: TerminalRenderer,
        on_complete: Callable[[], None] | None = None,
        on_boot_sound: Callable[[], None] | None = None,
    ) -> None:
        """Create the BootScreen.

        Args:
            renderer: The CRT terminal renderer.
            on_complete: Callback invoked when the boot sequence ends.
            on_boot_sound: Callback to play the boot sound effect.
        """
        super().__init__(renderer)
        self._on_boot_sound = on_boot_sound
        self.on_complete = on_complete
        self._font: pygame.font.Font | None = None
        self._small_font: pygame.font.Font | None = None
        self._line_index: int = 0
        self._char_index: int = 0
        self._line_timer: float = 0.0
        self._total_elapsed: float = 0.0
        self._type_speed: float = 0.04  # seconds per character
        self._complete: bool = False

    def on_enter(self) -> None:
        """Initialise fonts and start the first boot line."""
        self._font = pygame.font.SysFont("consolas", config.FONT_SIZE)
        self._small_font = pygame.font.SysFont("consolas", config.FONT_SIZE_SMALL)
        self._line_index = 0
        self._char_index = 0
        self._line_timer = 0.0
        self._total_elapsed = 0.0
        self._complete = False
        if self._on_boot_sound is not None:
            self._on_boot_sound()

    def handle_event(self, event: pygame.event.Event) -> None:
        """Skip the boot sequence with any key or mouse click."""
        if event.type == pygame.KEYDOWN or (
            event.type == pygame.MOUSEBUTTONDOWN and event.button == 1
        ):
            self._complete = True

    def update(self, dt: float) -> None:
        """Advance the boot typing animation."""
        if self._complete:
            if self.on_complete is not None:
                self.on_complete()
            return

        self._total_elapsed += dt
        self._line_timer -= dt

        if self._line_timer <= 0 and self._line_index < len(self.BOOT_LINES):
            line, delay = self.BOOT_LINES[self._line_index]

            if line == "":
                # Blank line — just advance
                self._line_index += 1
                self._char_index = 0
                self._line_timer = delay / 1000.0
            elif self._char_index < len(line):
                # Type characters one at a time
                chars_to_type = max(1, int(dt / self._type_speed))
                self._char_index = min(self._char_index + chars_to_type, len(line))
                self._line_timer = self._type_speed

                if self._char_index >= len(line):
                    # Line fully typed — schedule next line
                    self._line_index += 1
                    self._char_index = 0
                    self._line_timer = delay / 1000.0
            else:
                self._line_index += 1
                self._char_index = 0
                self._line_timer = delay / 1000.0

        # Check if all lines are done
        if self._line_index >= len(self.BOOT_LINES):
            self._complete = True
            if self.on_complete is not None:
                self.on_complete()

    def render(self) -> None:
        """Draw the boot text with typing animation."""
        surface = self.display
        font = self._font
        small_font = self._small_font
        assert font is not None

        w, h = surface.get_size()
        surface.fill(config.COLOR_BG)

        # Subtle static noise
        import random

        if self._total_elapsed < 1.0:
            noise_count = int(200 * (1 - self._total_elapsed))
            for _ in range(noise_count):
                x = random.randint(0, w - 1)
                y = random.randint(0, h - 1)
                surface.set_at(
                    (x, y),
                    (
                        random.randint(10, 40),
                        random.randint(20, 60),
                        random.randint(5, 20),
                    ),
                )

        # Build the visible text so far
        visible_lines: list[str] = []
        for i, (line_text, _delay) in enumerate(self.BOOT_LINES):
            if i < self._line_index:
                visible_lines.append(line_text)
            elif i == self._line_index:
                visible_lines.append(line_text[: self._char_index])
                # Blinking cursor on current line
                break

        # Render lines — scroll if text exceeds available space
        line_height = font.get_height() + 8
        start_y = sy(80)
        max_text_y = sy(980)

        # Blinking cursor on the last line
        cursor_visible = int(self._total_elapsed * 3) % 2 == 0

        # Scroll offset: push earlier lines off the top once we run out of room
        total_lines = len(visible_lines)
        max_visible_lines = (max_text_y - start_y) // line_height
        scroll_offset = max(0, total_lines - max_visible_lines)

        for i, line in enumerate(visible_lines):
            adjusted_index = i - scroll_offset
            if adjusted_index < 0:
                continue
            y = start_y + adjusted_index * line_height

            if i == len(visible_lines) - 1 and self._line_index < len(self.BOOT_LINES):
                # Current line — use typing color
                col = config.PHOSPHOR_GREEN
            elif "HELLO, COORDINATOR" in line or "BOB2142" in line:
                col = config.PHOSPHOR_BRIGHT
            else:
                col = config.PHOSPHOR_DIM

            text_surf = font.render(line, True, col)
            x = sx(200)
            surface.blit(text_surf, (x, y))

            # Draw cursor on the active line
            if (
                i == len(visible_lines) - 1
                and self._line_index < len(self.BOOT_LINES)
                and cursor_visible
            ):
                cursor_x = x + text_surf.get_width() + 2
                cursor_w = sx(10)
                cursor_h = line_height - 4
                pygame.draw.rect(
                    surface,
                    config.PHOSPHOR_GREEN,
                    (cursor_x, y + 2, cursor_w, cursor_h),
                )

        # Progress bar at bottom
        progress = min(1.0, self._line_index / len(self.BOOT_LINES))
        bar_w = sx(400)
        bar_h = 4
        bar_x = sx(760)
        bar_y = sy(1000)

        pygame.draw.rect(surface, config.PHOSPHOR_DIM, (bar_x, bar_y, bar_w, bar_h))
        fill_w = int(bar_w * progress)
        if fill_w > 0:
            pygame.draw.rect(surface, config.PHOSPHOR_GREEN, (bar_x, bar_y, fill_w, bar_h))

        # Loading label
        if small_font is not None:
            label = small_font.render(
                f"> INITIALIZING... {int(progress * 100)}%",
                True,
                config.PHOSPHOR_DIM,
            )
            surface.blit(label, (sx(760), bar_y - 24))
