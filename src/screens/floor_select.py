"""Floor selection screen — choose the next encounter on the current floor.

The Coordinator reviews available encounters (assault, salvage/event, rest)
and selects which to engage.  After combat, rewards are processed and the
player returns to this screen or advances to the next floor.

Lore framing:  The tactical feed shows multiple contact signals on the
current sector map.  The Coordinator selects which to engage first.
"""

from __future__ import annotations

from collections.abc import Callable

import pygame
from typing_extensions import assert_never

from src import config
from src.core.terminal import TerminalRenderer
from src.models.campaign import Campaign
from src.models.encounter import Encounter, EncounterType
from src.screens.base_screen import Screen
from src.systems.progression import FloorProgression
from src.ui.button import TerminalButton
from src.ui.layout import refresh, sx, sy
from src.ui.text import pad


class FloorSelectionScreen(Screen):
    """The encounter selection screen for the current floor."""

    def __init__(
        self,
        renderer: TerminalRenderer,
        campaign: Campaign,
        progression: FloorProgression,
        on_select: Callable[[Encounter], None] | None = None,
    ) -> None:
        """Create the FloorSelectionScreen.

        Args:
            renderer: The CRT terminal renderer.
            campaign: Current campaign state.
            progression: Floor progression manager.
            on_select: Callback invoked when an encounter is selected.
        """
        super().__init__(renderer)
        self._campaign = campaign
        self._progression = progression
        self.on_select = on_select
        self._font: pygame.font.Font | None = None
        self._small_font: pygame.font.Font | None = None
        self._mouse_pos: tuple[int, int] | None = None
        self._buttons: list[TerminalButton] = []
        self._encounters: list[Encounter] = []

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def on_enter(self) -> None:
        """Initialise fonts and layout."""
        self._font = pygame.font.SysFont("consolas", config.FONT_SIZE)
        self._small_font = pygame.font.SysFont("consolas", config.FONT_SIZE_SMALL)
        self._encounters = self._progression.get_encounters() or []
        self._build_buttons()

    def _build_buttons(self) -> None:
        """Create encounter selection buttons with risk/reward labels."""
        self._buttons.clear()
        font = self._font
        if font is None:
            return

        w, _ = self.display.get_size()
        btn_w = sx(400)
        btn_h = sy(50)
        btn_x = (w - btn_w) // 2
        y_start = sy(120)
        spacing = sy(60)

        for i, enc in enumerate(self._encounters):
            # Build label with risk/reward info
            if enc.encounter_type == EncounterType.COMBAT:
                label = "[ASSAULT] Enemy Patrol"
                risk = "HIGH"
                reward_label = ""
                rewards = enc.rewards
                if rewards.get("credits", 0) > 0:
                    reward_label = f"  CR:{pad(rewards['credits'], 4)}"
                if rewards.get("card_pick", 0) > 0:
                    reward_label += f"  CARDS:+{rewards['card_pick']}"
                label = f"{label}  RISK:{risk}{reward_label}"
            elif enc.encounter_type == EncounterType.MERCHANT:
                label = "[SUPPLY] Depot Signal"
                reward_label = "  RISK:LOW  TRADE"
                label = f"{label}{reward_label}"
            elif enc.encounter_type == EncounterType.EVENT:
                label = "[SIGNAL] Unknown Transmission"
                reward_label = "  RISK:VARIES  INTEL"
                label = f"{label}{reward_label}"
            elif enc.encounter_type == EncounterType.REST:
                label = "[R&R] Forward Camp"
                reward_label = "  RISK:NONE  REPAIR"
                label = f"{label}{reward_label}"
            else:
                assert_never(enc.encounter_type)
            btn = TerminalButton(
                btn_x,
                y_start + i * spacing,
                btn_w,
                btn_h,
                label=label,
                on_click=self._make_select_callback(enc),
            )
            self._buttons.append(btn)

    def _make_select_callback(self, enc: Encounter) -> Callable[[], None]:
        """Create a closure for encounter selection."""

        def callback() -> None:
            self._on_select(enc)

        return callback

    def _on_select(self, encounter: Encounter) -> None:
        """Handle encounter selection."""
        if self.on_select is not None:
            self.on_select(encounter)

    # ------------------------------------------------------------------
    # Events
    # ------------------------------------------------------------------

    def handle_event(self, event: pygame.event.Event) -> None:
        """Handle mouse movement and clicks."""
        if event.type == pygame.MOUSEMOTION:
            self._mouse_pos = event.pos
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._mouse_pos = event.pos
            for btn in self._buttons:
                btn.set_hover(self._mouse_pos)
                btn.click()

    def update(self, dt: float) -> None:
        """Update hover state."""
        for btn in self._buttons:
            btn.set_hover(self._mouse_pos)

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def render(self) -> None:
        """Draw the floor selection screen."""
        surface = self.display
        font = self._font
        small_font = self._small_font
        assert font is not None
        assert small_font is not None

        refresh(surface)
        w, h = surface.get_size()
        c = self._campaign

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
        top_text = (
            f"> SELECT NEXT TARGET"
            f"{'':>{w // 3}}"
            f"Floor {c.current_floor} - {c.outpost_name}"
            f"    CR:{pad(c.current_credits, 4)}"
        )
        top_surf = font.render(top_text, True, config.PHOSPHOR_GREEN)
        surface.blit(top_surf, (sx(40), sy(66)))

        # === Divider ===
        pygame.draw.line(surface, config.PHOSPHOR_DIM, (sx(40), sy(96)), (w - sx(40), sy(96)))

        # === Narrative intro ===
        template = self._progression.get_floor_template()
        if template and template.narrative_intro:
            intro_surf = small_font.render(
                f"> {template.narrative_intro}",
                True,
                config.PHOSPHOR_DIM,
            )
            surface.blit(intro_surf, (sx(60), sy(104)))

        # === Encounter panel ===
        panel_x = (w - sx(460)) // 2
        panel_y = sy(110)
        panel_w = sx(460)
        panel_h = sy(70) + len(self._encounters) * sy(60)
        pygame.draw.rect(surface, config.PHOSPHOR_DIM, (panel_x, panel_y, panel_w, panel_h), 1)
        panel_title = font.render("> ENCOUNTERS", True, config.PHOSPHOR_GREEN)
        surface.blit(panel_title, (panel_x + sx(12), panel_y + sy(4)))

        # === Buttons ===
        for btn in self._buttons:
            btn.render(surface, font)

        # === Floor progress indicator ===
        progress_text = f"PROGRESS: {pad(c.floors_cleared, 3)}/025 FLOORS CLEARED"
        prog_surf = small_font.render(progress_text, True, config.PHOSPHOR_DIM)
        surface.blit(
            prog_surf,
            (w // 2 - prog_surf.get_width() // 2, h - sy(40)),
        )
