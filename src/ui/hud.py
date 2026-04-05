"""Combat HUD — the in-combat tactical feed.

Renders the engagement display the Coordinator sees during combat::

    > FSA-TD-47                                       CH:01 // LINK ACTIVE
    ════════════════════════════════════════════════════════════════════
    ────────────────────────────────────────────────────────────────────
    ALPHA          HP:025/030  OL:04/12  EN:03/03  DECK:12  CR:0150
    YOUR TURN                                              [END TURN]
    ────────────────────────────────────────────────────────────────────

    > FRIENDLY UNITS                > HOSTILE CONTACTS
      ◈ ALPHA-1    HP:025/030  [ENGAGED]  ◆ HOSTILE-A  HP:015/020  [ACTIVE]
      ◈ BRAVO-1    HP:030/030  [STANDBY]  ◆ HOSTILE-B  HP:020/020  [ACTIVE]

    > PHASE: COMBAT
"""

from __future__ import annotations

import pygame

from src import config
from src.ui.layout import refresh, s, sx, sy
from src.ui.mech_view import MechView
from src.ui.text import pad


class CombatHUD:
    """The full combat HUD overlay.

    Composed of:
    - **Top bezel**: "> FSA-TD-47" left, "CH:01 // LINK ACTIVE" right
    - **Thick + thin dividers** matching MainMenu style
    - **Top bar**: callsign, HP, OL, energy, deck count, credits
    - **Party panel**: friendly mech views (left side)
    - **Enemy panel**: hostile mech views (right side)
    - **Phase label**: current turn phase
    - **End Turn button**
    """

    def __init__(
        self,
        screen_width: int,
        screen_height: int,
    ) -> None:
        """Create a CombatHUD.

        Args:
            screen_width: Display width.
            screen_height: Display height.
        """
        self._screen_width = screen_width
        self._screen_height = screen_height
        self._phase: str = "COMBAT"
        self._turn_label: str = "YOUR TURN"
        self._credits: int = 150
        self._deck_count: int = 0
        self._energy: int = 3
        self._max_energy: int = 3

        # Player stat line (top bar)
        self._player_callsign: str = "—"
        self._player_hp: int = 0
        self._player_max_hp: int = 1
        self._player_ol: int = 0
        self._player_max_ol: int = 1

        # Panels — positions defined in base 1920x1080, scaled at render time
        self._party_panel_rect = s(20, 120, 560, 400)
        self._enemy_panel_rect = s(620, 120, 560, 400)

        # Mech views (populated each render cycle)
        self._friendlies: list[MechView] = []
        self._hostiles: list[MechView] = []

        # Phase label position (bottom-left)
        self._phase_pos = (sx(20), sy(1040))

    # ------------------------------------------------------------------
    # State updates
    # ------------------------------------------------------------------

    def set_phase(self, phase: str) -> None:
        """Set the current turn phase label."""
        self._phase = phase

    def set_turn_label(self, label: str) -> None:
        """Set whose turn it is (e.g. ``YOUR TURN``, ``ENEMY TURN``)."""
        self._turn_label = label

    def set_player_stats(
        self,
        callsign: str,
        hp: int,
        max_hp: int,
        ol: int,
        max_ol: int,
    ) -> None:
        """Update the top-bar player stats."""
        self._player_callsign = callsign
        self._player_hp = hp
        self._player_max_hp = max(1, max_hp)
        self._player_ol = ol
        self._player_max_ol = max(1, max_ol)

    def set_resources(
        self,
        credits_: int,
        deck_count: int,
        energy: int,
        max_energy: int,
    ) -> None:
        """Update resource counters."""
        self._credits = credits_
        self._deck_count = deck_count
        self._energy = energy
        self._max_energy = max_energy

    def set_friendlies(self, mechs: list[MechView]) -> None:
        """Set the friendly mech views for the party panel."""
        self._friendlies = mechs

    def set_hostiles(self, mechs: list[MechView]) -> None:
        """Set the hostile mech views for the enemy panel."""
        self._hostiles = mechs

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def render(
        self,
        surface: pygame.Surface,
        font: pygame.font.Font,
        small_font: pygame.font.Font,
    ) -> None:
        """Draw the full HUD overlay.

        Args:
            surface: Target surface.
            font: Primary font for the top bar and labels.
            small_font: Smaller font for mech view details.
        """
        w = self._screen_width
        refresh(surface)

        # === Top bezel — match MainMenu style ===
        left = font.render("> FSA-TD-47", True, config.PHOSPHOR_GREEN)
        right = font.render("CH:01 // LINK ACTIVE", True, config.PHOSPHOR_DIM)
        surface.blit(left, (sx(40), sy(20)))
        surface.blit(right, (w - right.get_width() - sx(40), sy(20)))

        # Thick + thin divider
        pygame.draw.line(
            surface,
            config.PHOSPHOR_GREEN,
            (sx(40), sy(50)),
            (w - sx(40), sy(50)),
            2,
        )
        pygame.draw.line(
            surface,
            config.PHOSPHOR_DIM,
            (sx(40), sy(56)),
            (w - sx(40), sy(56)),
        )

        # === Top bar ===
        top_col = config.PHOSPHOR_GREEN
        top_text = (
            f"{self._player_callsign.upper():<14s}"
            f" HP:{pad(self._player_hp)}/{pad(self._player_max_hp)}"
            f"  OL:{pad(self._player_ol)}/{pad(self._player_max_ol)}"
            f"  EN:{pad(self._energy)}/{pad(self._max_energy)}"
            f"  DECK:{pad(self._deck_count)}"
            f"  CR:{pad(self._credits, 4)}"
        )
        top_surf = font.render(top_text, True, top_col)
        surface.blit(top_surf, (sx(40), sy(66)))

        # Turn label
        turn_col = config.PHOSPHOR_BRIGHT
        turn_surf = font.render(self._turn_label, True, turn_col)
        turn_x = w - turn_surf.get_width() - sx(40)
        surface.blit(turn_surf, (turn_x, sy(66)))

        # Divider line below top bar
        pygame.draw.line(surface, config.PHOSPHOR_DIM, (sx(40), sy(96)), (w - sx(40), sy(96)))

        # === Panels ===
        party_rect = self._party_panel_rect
        enemy_rect = self._enemy_panel_rect

        # Friendly panel
        pygame.draw.rect(surface, config.PHOSPHOR_DIM, party_rect, 1)
        party_title = font.render("> FRIENDLY UNITS", True, config.PHOSPHOR_GREEN)
        surface.blit(party_title, (party_rect[0] + sx(8), party_rect[1] + sy(4)))

        # Enemy panel
        pygame.draw.rect(surface, config.PHOSPHOR_DIM, enemy_rect, 1)
        enemy_title = font.render("> HOSTILE CONTACTS", True, config.PHOSPHOR_GREEN)
        surface.blit(enemy_title, (enemy_rect[0] + sx(8), enemy_rect[1] + sy(4)))

        # Friendly mech views
        y_off = party_rect[1] + sy(28)
        for mv in self._friendlies:
            mv.rect.x = party_rect[0] + sx(8)
            mv.rect.y = y_off
            mv.render(surface, font, small_font)
            y_off += mv.rect.height + sy(4)

        # Hostile mech views
        y_off = enemy_rect[1] + sy(28)
        for mv in self._hostiles:
            mv.rect.x = enemy_rect[0] + sx(8)
            mv.rect.y = y_off
            mv.render(surface, font, small_font)
            y_off += mv.rect.height + sy(4)

        # === Phase label ===
        phase_text = f"> PHASE: {self._phase}"
        phase_surf = small_font.render(phase_text, True, config.PHOSPHOR_DIM)
        surface.blit(phase_surf, self._phase_pos)
