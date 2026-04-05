"""Entry point for Tactical Command Terminal.

Bootstraps the Pygame-CE framework, constructs the Game state machine,
and runs the main loop.  The game is presented inside a physical monitor
frame — the player IS the Coordinator looking at their command terminal.

All initialisation errors are caught and reported.
"""

from __future__ import annotations

import logging
import sys
import traceback
from pathlib import Path

import pygame

from src import config
from src.core.monitor_frame import MonitorFrame
from src.core.terminal import TerminalRenderer
from src.game_flow import run_game

logger = logging.getLogger(__name__)
_ERROR_LOG = Path("crash.log")


def _init_pygame() -> tuple[pygame.Surface, MonitorFrame, TerminalRenderer]:
    """Initialize Pygame and create the monitor frame + renderer."""
    flags = pygame.FULLSCREEN if config.FULLSCREEN else 0
    pygame.init()
    display = pygame.display.set_mode(
        (config.SCREEN_WIDTH, config.SCREEN_HEIGHT),
        flags,
    )
    pygame.display.set_caption("Tactical Command Terminal")
    logger.info(
        "Pygame-CE initialised — %dx%d @ %d fps %s",
        config.SCREEN_WIDTH,
        config.SCREEN_HEIGHT,
        config.TARGET_FPS,
        "(fullscreen)" if config.FULLSCREEN else "(windowed)",
    )

    monitor = MonitorFrame(
        config.SCREEN_WIDTH,
        config.SCREEN_HEIGHT,
        bezel_thickness=config.MONITOR_BEZEL,
    )

    renderer = TerminalRenderer(monitor.game_surface)

    return display, monitor, renderer


def main() -> int:
    """Run the game loop and return exit code."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    try:
        display, monitor, renderer = _init_pygame()
        run_game(display, monitor, renderer)
        return 0
    except pygame.error as exc:
        with _ERROR_LOG.open("w") as f:
            traceback.print_exc(file=f)
        logger.critical("Pygame initialization failed: %s", exc)
        return 1
    except Exception as exc:
        with _ERROR_LOG.open("w") as f:
            traceback.print_exc(file=f)
        logger.critical("Unhandled exception during startup: %s", exc)
        return 1
    finally:
        pygame.quit()


if __name__ == "__main__":
    sys.exit(main())
