"""Shared pytest fixtures for the test suite."""

import pygame
import pytest


@pytest.fixture(scope="session", autouse=True)
def _init_pygame() -> None:
    """Ensure Pygame (including fonts) is initialised for all tests."""
    pygame.init()
