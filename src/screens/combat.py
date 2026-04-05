"""Combat screen — the primary engagement display.

Renders the tactical feed as the Coordinator sees it through degraded
telemetry: grid with terrain markers, geometric IFF symbols for units,
directive entries as terminal commands, and the full combat HUD overlay.

Lore-accurate flow::

    > ENGAGEMENT DETECTED
    > SWITCHING TO TACTICAL FEED...
    > LINK ESTABLISHED

    [Grid with IFF symbols and terrain]
    [Directive entries on the right]
    [HUD overlay: top bar, party/enemy panels]
"""

from __future__ import annotations

import math
from collections.abc import Callable

import pygame

from src import config
from src.core.terminal import TerminalRenderer
from src.models.campaign import Campaign
from src.models.card import TargetPattern
from src.models.data_loader import GameData
from src.screens.base_screen import Screen
from src.systems.combat import CombatPhase, CombatState, MechOnGrid
from src.systems.combat_comms import CombatComms
from src.ui.card_view import DirectiveView
from src.ui.grid_view import GridView
from src.ui.hud import CombatHUD
from src.ui.layout import refresh
from src.ui.mech_view import MechView


class CombatScreen(Screen):
    """The in-combat screen — tactical engagement feed."""

    def __init__(
        self,
        renderer: TerminalRenderer,
        combat_state: CombatState,
        game_data: GameData,
        campaign: Campaign,
        floor: int = 1,
        on_complete: Callable[[CombatState], None] | None = None,
    ) -> None:
        """Create the CombatScreen.

        Args:
            renderer: The CRT terminal renderer.
            combat_state: Pre-initialised combat state with mechs placed.
            game_data: Loaded game data for directive look-up.
            campaign: Current campaign state (for comms context).
            floor: Current campaign floor number.
            on_complete: Callback invoked when combat ends.
        """
        super().__init__(renderer)
        self.combat = combat_state
        self.game_data = game_data
        self.on_complete = on_complete
        self._font: pygame.font.Font | None = None
        self._small_font: pygame.font.Font | None = None
        self._mouse_pos: tuple[int, int] | None = None
        self._hand_views: list[DirectiveView] = []
        self._grid_view: GridView | None = None
        self._hud: CombatHUD | None = None
        self._selected_hand_index: int = -1
        self._phase_text: str = ""
        self._phase_text_timer: float = 0.0
        self._last_target: tuple[int, int] | None = None

        # Combat comms — flavour text feed
        self._comms = CombatComms(campaign)
        self._floor = floor
        self._comms_log: list[str] = []
        self._comms_timer: float = 0.0
        self._comms_interval: float = 4.0  # Seconds between ambient comms

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def on_enter(self) -> None:
        """Initialise fonts, UI components, and begin combat."""
        refresh(self.display)
        self._font = pygame.font.SysFont("consolas", config.FONT_SIZE)
        self._small_font = pygame.font.SysFont("consolas", config.FONT_SIZE_SMALL)
        self.combat.begin_combat()
        self._build_ui()
        self._phase_text = "> ENGAGEMENT DETECTED // LINK ESTABLISHED"
        self._phase_text_timer = 2.0

        # Start comms with engagement message
        self._comms.start_combat(self.combat, self._floor)
        msg = self._comms.get_message("engagement_start")
        if msg:
            self._comms_log.append(msg)

    def _build_ui(self) -> None:
        """Construct the grid view, HUD, and hand layout."""
        w, h = self.display.get_size()
        font = self._font
        assert font is not None

        # Grid view — left/center portion, below HUD panels
        # HUD panels occupy y=36..196 (160px tall), so grid starts at y=200
        grid_w = w - 360
        grid_h = h - 200
        self._grid_view = GridView(10, 200, grid_w, grid_h, self.combat.grid)

        # Place mechs on the grid
        for mg in self.combat.mechs:
            if mg.mech.is_alive:
                self._grid_view.place_unit(mg.col, mg.row, mg.mech, mg.friendly)

        # HUD
        self._hud = CombatHUD(w, h)

    # ------------------------------------------------------------------
    # Hand management
    # ------------------------------------------------------------------

    def _rebuild_hand_views(self) -> None:
        """Rebuild directive views from the current hand."""
        self._hand_views.clear()
        if self._font is None:
            return
        w = self.display.get_size()[0]
        x_start = w - 340
        y_start = 50
        for i, did in enumerate(self.combat.hand):
            d = self.game_data.get_directive(did)
            if d is None:
                continue
            weapon_bonus = 0
            ol_discount = 0
            # Use the primary friendly mech's stats
            if self.combat.friendlies:
                fm = self.combat.friendlies[0].mech
                weapon_bonus = fm.weapon_bonus
                ol_discount = fm.ol_discount
            dv = DirectiveView(
                x_start,
                y_start + i * 60,
                320,
                d,
                weapon_bonus=weapon_bonus,
                ol_discount=ol_discount,
            )
            self._hand_views.append(dv)

    # ------------------------------------------------------------------
    # Events
    # ------------------------------------------------------------------

    def handle_event(self, event: pygame.event.Event) -> None:
        """Handle mouse clicks for directive selection and combat actions."""
        if event.type == pygame.MOUSEMOTION:
            self._mouse_pos = event.pos
            # Update hover on hand views
            for dv in self._hand_views:
                dv.set_hover(self._mouse_pos)

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._mouse_pos = event.pos
            # Click on a directive in hand
            for i, dv in enumerate(self._hand_views):
                dv.set_hover(self._mouse_pos)
                if dv.hovered:
                    self._play_directive(i)
                    return
            # Click on the grid — if in targeting phase, resolve directive
            if self.combat.phase == CombatPhase.PLAYER_DIRECTIVE_SELECT and self._grid_view:
                cell = self._grid_view.pixel_to_cell(event.pos[0], event.pos[1])
                if cell is not None:
                    self._last_target = cell

    def _play_directive(self, hand_index: int) -> None:
        """Play the selected directive and resolve combat."""
        if self.combat.phase != CombatPhase.PLAYER_DIRECTIVE_SELECT:
            return

        directive_id = self.combat.hand[hand_index]
        directive = self.game_data.directives.get(directive_id)

        target_col, target_row = None, None

        if directive is not None:
            pattern = directive.pattern
            rng = directive.range_

            # For targeted directives, use last clicked cell
            if (
                pattern
                in (
                    TargetPattern.SINGLE,
                    TargetPattern.LINE,
                    TargetPattern.AREA,
                    TargetPattern.CONE,
                )
                and rng > 0
            ):
                if self._last_target is not None:
                    target_col, target_row = self._last_target
                else:
                    # Auto-target nearest enemy if no target clicked
                    target_col, target_row = self._auto_target()

        self.combat.play_directive(
            hand_index,
            game_data=self.game_data,
            target_col=target_col,
            target_row=target_row,
        )
        self._rebuild_hand_views()

        # Check if combat ended
        if self.combat.check_completion() is not None:
            return

        # If hand is empty, end turn
        if not self.combat.hand:
            self.combat.end_player_turn()

    def _auto_target(self) -> tuple[int, int]:
        """Find the nearest enemy to auto-target."""
        enemies = self.combat.hostiles
        if not enemies:
            return (8, 5)  # fallback
        nearest = enemies[0]
        for e in enemies[1:]:
            if _dist_to_player(e) < _dist_to_player(nearest):
                nearest = e
        return (nearest.col, nearest.row)

    def update(self, dt: float) -> None:
        """Update phase text timer, comms, and check combat state."""
        if self._phase_text_timer > 0:
            self._phase_text_timer -= dt
            if self._phase_text_timer <= 0:
                self._phase_text = ""

        # Ambient comms timer
        self._comms_timer += dt
        if self._comms_timer >= self._comms_interval:
            self._comms_timer = 0.0
            msg = self._comms.get_message("ambient")
            if msg:
                self._comms_log.append(msg)
                # Keep log to last 6 messages
                if len(self._comms_log) > 6:
                    self._comms_log = self._comms_log[-6:]

        # Rebuild hand views each frame to match state
        self._rebuild_hand_views()

        # Check combat completion
        result = self.combat.check_completion()
        if result is not None and self.on_complete is not None:
            self.on_complete(self.combat)

    def _push_comms(self, event: str, **kwargs: float) -> None:
        """Push a combat event message to the comms log."""
        msg = self._comms.get_message(event, **kwargs)
        if msg:
            self._comms_log.append(msg)
            if len(self._comms_log) > 6:
                self._comms_log = self._comms_log[-6:]

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def render(self) -> None:
        """Draw the full combat screen."""
        surface = self.display
        font = self._font
        small_font = self._small_font
        assert font is not None
        assert small_font is not None
        assert self._grid_view is not None
        assert self._hud is not None

        w, h = surface.get_size()

        # === Grid ===
        self._grid_view.render(surface, font, small_font)

        # === Hand / Directive panel ===
        panel_x = w - 360
        panel_w = 350
        # Panel background
        bg_surf = pygame.Surface((panel_w, h))
        bg_surf.fill(config.COLOR_PANEL_BG)
        surface.blit(bg_surf, (panel_x, 0))
        # Panel border
        pygame.draw.line(surface, config.PHOSPHOR_GREEN, (panel_x, 0), (panel_x, h), 1)

        # Panel title
        title_surf = font.render("> DIRECTIVE QUEUE", True, config.PHOSPHOR_GREEN)
        surface.blit(title_surf, (panel_x + 10, 10))

        # Energy display
        en_text = (
            f"  EN: {self.combat.energy}/{self.combat.max_energy}"
            f"  DECK: {len(self.combat.draw_pile):02d}"
            f"  DISCARD: {len(self.combat.discard_pile):02d}"
        )
        en_surf = small_font.render(en_text, True, config.PHOSPHOR_DIM)
        surface.blit(en_surf, (panel_x + 10, 34))

        # Render hand views
        for dv in self._hand_views:
            dv.render(surface, font, small_font)

        # Phase text (temporary overlay)
        if self._phase_text:
            min(1.0, self._phase_text_timer)
            phase_surf = font.render(self._phase_text, True, config.PHOSPHOR_BRIGHT)
            px = (w - phase_surf.get_width()) // 2
            py = h // 2 - phase_surf.get_height() // 2
            surface.blit(phase_surf, (px, py))

        # === HUD Overlay ===
        self._update_hud()
        self._hud.render(surface, font, small_font)

        # === Comms Log (bottom-left, below grid) ===
        self._render_comms_log(surface, small_font, w, h)

    def _render_comms_log(
        self,
        surface: pygame.Surface,
        small_font: pygame.font.Font,
        w: int,
        h: int,
    ) -> None:
        """Render the combat comms log at the bottom of the screen."""
        if not self._comms_log:
            return

        comms_x = 10
        comms_y = h - len(self._comms_log) * 20 - 16
        comms_w = w - 380  # Leave room for directive panel

        # Background panel
        bg_h = len(self._comms_log) * 20 + 24
        bg_surf = pygame.Surface((comms_w, bg_h), pygame.SRCALPHA)
        bg_surf.fill((8, 12, 4, 180))
        surface.blit(bg_surf, (comms_x, comms_y - 4))
        pygame.draw.rect(
            surface,
            config.PHOSPHOR_DIM,
            (comms_x, comms_y - 4, comms_w, bg_h),
            1,
        )

        # Title
        title_surf = small_font.render("> COMMS FEED", True, config.PHOSPHOR_GREEN)
        surface.blit(title_surf, (comms_x + 8, comms_y))

        # Messages
        for i, msg in enumerate(self._comms_log[-6:]):
            msg_surf = small_font.render(msg, True, config.PHOSPHOR_DIM)
            surface.blit(msg_surf, (comms_x + 8, comms_y + 20 + i * 20))

    def _update_hud(self) -> None:
        """Sync the HUD with current combat state."""
        if self._hud is None:
            return
        c = self.combat
        # Phase label
        phase_map = {
            CombatPhase.PLAYER_DIRECTIVE_SELECT: "DIRECTIVE SELECT",
            CombatPhase.PLAYER_TARGETING: "TARGETING",
            CombatPhase.PLAYER_ANIMATING: "RESOLVING",
            CombatPhase.ENEMY_TURN: "ENEMY TURN",
            CombatPhase.COMBAT_COMPLETE: "COMPLETE",
        }
        self._hud.set_phase(
            phase_map.get(c.phase or CombatPhase.PLAYER_DIRECTIVE_SELECT, "UNKNOWN")
        )

        # Turn label
        if c.phase == CombatPhase.ENEMY_TURN:
            self._hud.set_turn_label("ENEMY TURN")
        else:
            self._hud.set_turn_label("YOUR TURN")

        # Player stats (primary friendly)
        if c.friendlies:
            pm = c.friendlies[0].mech
            self._hud.set_player_stats(
                pm.pilot_callsign,
                pm.current_hp,
                pm.max_hp,
                pm.current_ol,
                pm.max_ol,
            )
        else:
            self._hud.set_player_stats("NO SIGNAL", 0, 1, 0, 1)

        self._hud.set_resources(
            c.friendlies[0].mech.frame.faction.value
            if c.friendlies
            else 0,  # placeholder for credits
            len(c.draw_pile) + len(c.hand),
            c.energy,
            c.max_energy,
        )

        # Friendly mech views
        friendlies: list[MechView] = []
        for i, mg in enumerate(c.friendlies):
            mv = MechView(10, 60 + i * 52, mg.mech, mg.mech.pilot_callsign, friendly=True)
            friendlies.append(mv)
        self._hud.set_friendlies(friendlies)

        # Hostile mech views
        hostiles: list[MechView] = []
        for i, mg in enumerate(c.hostiles):
            mv = MechView(10, 60 + i * 52, mg.mech, "HOSTILE", friendly=False)
            hostiles.append(mv)
        self._hud.set_hostiles(hostiles)


def _dist_to_player(mg: MechOnGrid) -> float:
    """Distance from a mech to the player's position.

    Args:
        mg: MechOnGrid instance.

    Returns:
        Euclidean distance to player (first friendly).
    """
    return math.sqrt(mg.col**2 + mg.row**2)
