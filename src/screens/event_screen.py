"""Event screen — narrative choices rendered as a terminal display.

The Coordinator receives an intercepted transmission or sensor report
and must choose how to respond.  Choices affect faction reputation,
credits, and may rescue allies.

Lore-accurate format::

    > INCOMING TRANSMISSION — OUTPOST ALPHA
    ───────────────────────────────────────────────
    > INTERCEPTED SIGNAL

    Unidentified broadcast on emergency frequency.
    Signal degrades and reconstructs...

    [1] INVESTIGATE
    [2] IGNORE
    [3] JAM THE SIGNAL

    > Awaiting orders...
"""

from __future__ import annotations

from collections.abc import Callable

import pygame

from src import config
from src.core.terminal import TerminalRenderer
from src.models.campaign import Campaign
from src.screens.base_screen import Screen
from src.systems.narrative import EventChoice, NarrativeEngine, NarrativeEvent, Outcome
from src.ui.button import TerminalButton
from src.ui.panel import Panel


class EventScreen(Screen):
    """A branching narrative event screen."""

    def __init__(
        self,
        renderer: TerminalRenderer,
        campaign: Campaign,
        event: NarrativeEvent,
        narrative_engine: NarrativeEngine,
        on_complete: Callable[[Outcome], None] | None = None,
    ) -> None:
        """Create the EventScreen.

        Args:
            renderer: The CRT terminal renderer.
            campaign: Current campaign state.
            event: The narrative event to present.
            narrative_engine: Engine for resolving choices.
            on_complete: Callback invoked with the chosen Outcome.
        """
        super().__init__(renderer)
        self._campaign = campaign
        self._event = event
        self._engine = narrative_engine
        self.on_complete = on_complete
        self._font: pygame.font.Font | None = None
        self._small_font: pygame.font.Font | None = None
        self._mouse_pos: tuple[int, int] | None = None
        self._buttons: list[TerminalButton] = []
        self._outcome_text: str = ""

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def on_enter(self) -> None:
        """Initialise fonts and layout."""
        self._font = pygame.font.SysFont("consolas", config.FONT_SIZE)
        self._small_font = pygame.font.SysFont("consolas", config.FONT_SIZE_SMALL)
        self._build_buttons()

    def _build_buttons(self) -> None:
        """Create choice buttons from available choices."""
        self._buttons.clear()
        font = self._font
        if font is None:
            return

        w, _ = self.display.get_size()
        btn_w = 340
        btn_h = 40
        btn_x = (w - btn_w) // 2
        y_start = 300
        spacing = 50

        choices = self._event.get_available_choices(self._campaign)
        for i, choice in enumerate(choices):
            label = f"[{i + 1}] {choice.text.upper()}"
            btn = TerminalButton(
                btn_x,
                y_start + i * spacing,
                btn_w,
                btn_h,
                label=label,
                on_click=self._make_choice_callback(choice),
            )
            self._buttons.append(btn)

    def _make_choice_callback(self, choice: EventChoice) -> Callable[[], None]:
        """Create a typed callback for a choice."""

        def callback() -> None:
            outcome = self._engine.resolve_choice(self._event, choice)
            self._outcome_text = outcome.narrative_text
            if self.on_complete is not None:
                self.on_complete(outcome)

        return callback

    # ------------------------------------------------------------------
    # Events
    # ------------------------------------------------------------------

    def handle_event(self, event: pygame.event.Event) -> None:
        """Handle mouse clicks."""
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
        """Draw the event screen."""
        surface = self.display
        font = self._font
        small_font = self._small_font
        assert font is not None
        assert small_font is not None

        w, h = surface.get_size()

        # === Top bezel ===
        left = font.render("> FSA-TD-47", True, config.PHOSPHOR_GREEN)
        right = font.render("CH:01 // LINK ACTIVE", True, config.PHOSPHOR_DIM)
        surface.blit(left, (30, 16))
        surface.blit(right, (w - right.get_width() - 30, 16))
        pygame.draw.line(surface, config.PHOSPHOR_DIM, (30, 42), (w - 30, 42))

        # === Event title ===
        title = font.render(f"> {self._event.title.upper()}", True, config.PHOSPHOR_BRIGHT)
        surface.blit(title, ((w - title.get_width()) // 2, 60))

        # === Divider ===
        pygame.draw.line(surface, config.PHOSPHOR_GREEN, (200, 90), (w - 200, 90))

        # === Narrative text ===
        nar_lines = self._event.narrative_text.split("\n")
        y = 110
        for line in nar_lines:
            surf = small_font.render(f"> {line}", True, config.PHOSPHOR_GREEN)
            surface.blit(surf, ((w - surf.get_width()) // 2, y))
            y += surf.get_height() + 8

        # === Outcome text (after choice) ===
        if self._outcome_text:
            y += 10
            pygame.draw.line(surface, config.PHOSPHOR_DIM, (200, y), (w - 200, y))
            y += 10
            outcome_surf = small_font.render(f"> {self._outcome_text}", True, config.COLOR_WARNING)
            surface.blit(outcome_surf, ((w - outcome_surf.get_width()) // 2, y))

        # === Choice panel ===
        panel_h = 50 + len(self._buttons) * 50
        panel_y = 300
        panel = Panel((w - 400) // 2, panel_y, 400, panel_h, "AWAITING ORDERS")
        panel.render(surface, font, font)

        # === Buttons ===
        for btn in self._buttons:
            btn.render(surface, font)

        # === Footer ===
        footer = small_font.render("[AUTHORIZED PERSONNEL ONLY]", True, config.PHOSPHOR_DIM)
        surface.blit(footer, ((w - footer.get_width()) // 2, h - 30))
