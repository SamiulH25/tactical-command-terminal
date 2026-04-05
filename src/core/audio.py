"""Audio manager — SFX playback and CRT background hum.

Generates all sound effects programmatically using Pygame's mixer so the
game works without external audio assets.  Sounds are simple waveforms:
- **Keypress**: Short noise burst (white noise, 50ms)
- **Beep**: Sine wave at 800Hz, 100ms
- **Static burst**: Filtered noise burst, 300ms
- **CRT hum**: Low-frequency oscillator (60Hz hum), looped
- **Engagement**: Rising tone sweep, 500ms
- **Victory**: Three-note ascending chord

Lore framing:  All audio is diegetic terminal hardware sounds — keyboard
switches, warning beeps, radio static, and power supply hum.
"""

from __future__ import annotations

import logging
import math

import numpy as np
import pygame

logger = logging.getLogger(__name__)

_SAMPLE_RATE: int = 22050
_DEFAULT_VOLUME: float = 0.3


def _generate_tone(
    frequency: float,
    duration: float,
    volume: float = _DEFAULT_VOLUME,
    waveform: str = "sine",
    fade_out: float = 0.0,
) -> pygame.mixer.Sound:
    """Generate a simple waveform sound.

    Args:
        frequency: Frequency in Hz.
        duration: Duration in seconds.
        volume: Amplitude scale (0.0-1.0).
        waveform: ``"sine"`` or ``"noise"``.
        fade_out: Duration of fade-out tail in seconds.

    Returns:
        A Pygame Sound object.
    """
    n_samples = int(_SAMPLE_RATE * duration)
    t = np.linspace(0, duration, n_samples, endpoint=False)

    if waveform == "sine":
        samples = np.sin(2 * math.pi * frequency * t)
    elif waveform == "noise":
        samples = np.random.uniform(-1, 1, n_samples)
    else:
        samples = np.zeros(n_samples)

    # Apply fade out
    if fade_out > 0:
        fade_n = int(_SAMPLE_RATE * fade_out)
        fade_samples = min(fade_n, len(samples))
        fade_curve = np.linspace(1.0, 0.0, fade_samples)
        samples[-fade_samples:] *= fade_curve

    # Scale to 16-bit
    samples = (samples * volume * 32767).astype(np.int16)
    # Stereo
    stereo = np.column_stack((samples, samples))
    return pygame.mixer.Sound(stereo)  # type: ignore[arg-type,return-value]


def _generate_sweep(
    freq_start: float,
    freq_end: float,
    duration: float,
    volume: float = _DEFAULT_VOLUME,
) -> pygame.mixer.Sound:
    """Generate a frequency sweep (rising or falling tone).

    Args:
        freq_start: Starting frequency in Hz.
        freq_end: Ending frequency in Hz.
        duration: Duration in seconds.
        volume: Amplitude scale (0.0-1.0).

    Returns:
        A Pygame Sound object.
    """
    n_samples = int(_SAMPLE_RATE * duration)
    t = np.linspace(0, duration, n_samples, endpoint=False)
    # Linear frequency ramp
    phase = 2 * math.pi * (freq_start * t + (freq_end - freq_start) * t**2 / (2 * duration))
    samples = np.sin(phase)
    samples *= volume * 32767
    samples = samples.astype(np.int16)
    stereo = np.column_stack((samples, samples))
    return pygame.mixer.Sound(stereo)  # type: ignore[arg-type,return-value]


class SoundManager:
    """Manages all game sound effects and ambient audio.

    All sounds are generated at construction time.  If the mixer is
    unavailable, all methods become no-ops.
    """

    def __init__(self, volume: float = _DEFAULT_VOLUME) -> None:
        """Create a SoundManager and generate all sounds.

        Args:
            volume: Master volume (0.0-1.0).
        """
        self._volume = volume
        self._initialised = False
        self._hum_channel: pygame.mixer.Channel | None = None

        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(_SAMPLE_RATE, -16, 2, 512)
            self._initialised = True
        except pygame.error:
            logger.warning("Audio mixer unavailable — running silent")
            return  # type: ignore[unreachable]

        # Generate sounds
        self.keypress = _generate_tone(400, 0.05, volume, waveform="noise", fade_out=0.02)
        self.beep = _generate_tone(800, 0.1, volume, waveform="sine")
        self.error_beep = _generate_tone(300, 0.15, volume, waveform="sine")
        self.static_burst = _generate_tone(0, 0.3, volume * 0.5, waveform="noise", fade_out=0.15)
        self.engagement = _generate_sweep(200, 600, 0.5, volume * 0.6)
        self.victory = self._make_victory_chord(volume)
        self.boot_sequence = self._make_boot_sound(volume)

        # CRT hum — low-frequency looping tone
        self._hum_sound = _generate_tone(60, 2.0, volume * 0.15, waveform="sine")

    @property
    def initialised(self) -> bool:
        """Whether the audio system is available."""
        return self._initialised

    def _make_victory_chord(self, volume: float) -> pygame.mixer.Sound:
        """Generate a three-note ascending victory chord.

        Notes: C4 (261.6 Hz), E4 (329.6 Hz), G4 (392.0 Hz).
        """
        notes = [261.6, 329.6, 392.0]
        note_dur = 0.2
        gap = 0.05
        total_dur = len(notes) * (note_dur + gap)
        n_samples = int(_SAMPLE_RATE * total_dur)
        samples = np.zeros(n_samples, dtype=np.float64)

        for i, freq in enumerate(notes):
            start = int(_SAMPLE_RATE * i * (note_dur + gap))
            n_note = int(_SAMPLE_RATE * note_dur)
            t = np.linspace(0, note_dur, n_note, endpoint=False)
            note = np.sin(2 * math.pi * freq * t) * 0.7
            # Fade out tail
            fade_n = int(_SAMPLE_RATE * 0.08)
            note[-fade_n:] *= np.linspace(1.0, 0.0, fade_n)
            samples[start : start + n_note] += note

        samples *= volume * 32767
        samples = np.clip(samples, -32767, 32767).astype(np.int16)
        stereo = np.column_stack((samples, samples))
        return pygame.mixer.Sound(stereo)  # type: ignore[arg-type,return-value]

    def _make_boot_sound(self, volume: float) -> pygame.mixer.Sound:
        """Generate a terminal boot-up sound.

        A short ascending power-on sweep followed by a confirmation beep.
        """
        # Power-on sweep: 100 Hz → 800 Hz over 0.4s
        sweep_dur = 0.4
        beep_dur = 0.15
        gap = 0.1
        total_dur = sweep_dur + gap + beep_dur

        n_samples = int(_SAMPLE_RATE * total_dur)
        samples = np.zeros(n_samples, dtype=np.float64)

        # Sweep portion
        n_sweep = int(_SAMPLE_RATE * sweep_dur)
        t_sweep = np.linspace(0, sweep_dur, n_sweep, endpoint=False)
        phase = 2 * math.pi * (100 * t_sweep + (800 - 100) * t_sweep**2 / (2 * sweep_dur))
        samples[:n_sweep] = np.sin(phase) * 0.4

        # Beep portion
        beep_start = int(_SAMPLE_RATE * (sweep_dur + gap))
        n_beep = int(_SAMPLE_RATE * beep_dur)
        t_beep = np.linspace(0, beep_dur, n_beep, endpoint=False)
        samples[beep_start : beep_start + n_beep] = np.sin(2 * math.pi * 1200 * t_beep) * 0.3

        # Fade out tail
        fade_n = int(_SAMPLE_RATE * 0.05)
        samples[-fade_n:] *= np.linspace(1.0, 0.0, fade_n)

        samples *= volume * 32767
        samples = np.clip(samples, -32767, 32767).astype(np.int16)
        stereo = np.column_stack((samples, samples))
        return pygame.mixer.Sound(stereo)  # type: ignore[arg-type,return-value]

    # ------------------------------------------------------------------
    # Playback
    # ------------------------------------------------------------------

    def play_keypress(self) -> None:
        """Play a keyboard click sound."""
        if self._initialised:
            self.keypress.play()

    def play_beep(self) -> None:
        """Play a terminal beep."""
        if self._initialised:
            self.beep.play()

    def play_error(self) -> None:
        """Play an error/warning beep."""
        if self._initialised:
            self.error_beep.play()

    def play_static(self) -> None:
        """Play radio static burst (for transitions)."""
        if self._initialised:
            self.static_burst.play()

    def play_engagement(self) -> None:
        """Play combat engagement sound."""
        if self._initialised:
            self.engagement.play()

    def play_boot(self) -> None:
        """Play terminal boot sequence sound."""
        if self._initialised:
            self.boot_sequence.play()

    def play_victory(self) -> None:
        """Play victory chord."""
        if self._initialised:
            self.victory.play()

    def start_hum(self) -> None:
        """Start the CRT background hum (looping)."""
        if not self._initialised:
            return
        self._hum_channel = self._hum_sound.play(-1)  # Loop forever

    def stop_hum(self) -> None:
        """Stop the CRT background hum."""
        if self._hum_channel is not None:
            self._hum_channel.stop()
            self._hum_channel = None

    def set_volume(self, volume: float) -> None:
        """Set master volume.

        Args:
            volume: 0.0 (silent) to 1.0 (full).
        """
        self._volume = max(0.0, min(1.0, volume))
        pygame.mixer.music.set_volume(self._volume)
