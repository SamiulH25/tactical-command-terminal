"""User configuration — volume, CRT effects, and display settings.

The config file is stored in the project root as ``config.json``.  If it
doesn't exist, defaults are used.  Changes are saved on write.

Settings:
- ``master_volume``: 0.0-1.0
- ``crt_effects``: bool — enable/disable scanlines and flicker
- ``font_size``: int — override default font size
- ``window_scale``: float — 1.0 = native, 0.5 = half resolution
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

_CONFIG_PATH: Path = Path("config.json")


@dataclass
class UserConfig:
    """User-adjustable game settings.

    Invariants:
    - ``master_volume`` is in [0.0, 1.0].
    - ``font_size`` is positive.
    - ``window_scale`` is in [0.25, 2.0].
    """

    master_volume: float = 0.5
    """Master audio volume (0.0 = silent, 1.0 = full)."""

    crt_effects: bool = True
    """Enable CRT effects (scanlines, flicker)."""

    font_size: int = 16
    """Override default font size in pixels."""

    window_scale: float = 1.0
    """Display scale factor (1.0 = native resolution)."""

    def validate(self) -> None:
        """Raise ``ValueError`` if any setting is out of range.

        Raises:
            ValueError: If any field is outside its valid range.
        """
        if not (0.0 <= self.master_volume <= 1.0):
            raise ValueError(f"master_volume {self.master_volume} out of range [0.0, 1.0]")
        if self.font_size <= 0:
            raise ValueError(f"font_size {self.font_size} must be positive")
        if not (0.25 <= self.window_scale <= 2.0):
            raise ValueError(f"window_scale {self.window_scale} out of range [0.25, 2.0]")


def load_config(path: Path | None = None) -> UserConfig:
    """Load user configuration from disk.

    If the file doesn't exist or is invalid, returns defaults.

    Args:
        path: Optional override path.  Defaults to ``config.json``.

    Returns:
        A validated UserConfig object.
    """
    config_path = path or _CONFIG_PATH
    if not config_path.is_file():
        logger.info("No config file found — using defaults")
        return UserConfig()

    try:
        with config_path.open("r", encoding="utf-8") as fh:
            raw: dict[str, object] = json.load(fh)
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("Config file corrupt — using defaults: %s", exc)
        return UserConfig()

    try:
        cfg = UserConfig(
            master_volume=float(raw.get("master_volume", 0.5)),  # type: ignore[arg-type]
            crt_effects=bool(raw.get("crt_effects", True)),
            font_size=int(raw.get("font_size", 16)),  # type: ignore[call-overload]
            window_scale=float(raw.get("window_scale", 1.0)),  # type: ignore[arg-type]
        )
        cfg.validate()
        return cfg
    except (ValueError, TypeError) as exc:
        logger.warning("Config values invalid — using defaults: %s", exc)
        return UserConfig()


def save_config(config: UserConfig, path: Path | None = None) -> None:
    """Save user configuration to disk.

    Args:
        config: The config to save.
        path: Optional override path.  Defaults to ``config.json``.
    """
    config.validate()
    config_path = path or _CONFIG_PATH
    try:
        with config_path.open("w", encoding="utf-8") as fh:
            json.dump(asdict(config), fh, indent=2)
        logger.info("Config saved to %s", config_path)
    except OSError as exc:
        logger.error("Failed to save config: %s", exc)
