"""Full game flow — wires all screens together into a playable game.

This module creates the Game instance, loads all game data, and sets up
the screen transition callbacks that connect:

    MainMenu → MechSelect → ShipMenu → FloorSelect → Combat → Victory
                                                                    → ShipMenu (next floor)
                                                        → GameOver

The Game class manages the screen stack, and each screen has callbacks
that push/pop screens as needed.
"""

from __future__ import annotations

import logging
import random
import traceback
from contextlib import suppress
from pathlib import Path

import pygame

from src.core.audio import SoundManager
from src.core.monitor_frame import MonitorFrame
from src.core.terminal import TerminalRenderer
from src.core.transitions import (
    make_brief,
    make_deployment,
    make_signal_acquire,
    make_signal_lost,
)
from src.game import Game
from src.models.campaign import Campaign
from src.models.data_loader import load_all_data
from src.models.grid import CombatGrid
from src.models.grid_layouts import get_random_layout
from src.models.mech import MechFrame
from src.screens.boot_screen import BootScreen
from src.screens.combat import CombatScreen
from src.screens.event_screen import EventScreen
from src.screens.floor_select import FloorSelectionScreen
from src.screens.game_over import GameOverScreen
from src.screens.main_menu import MainMenu
from src.screens.mech_select import MechSelect
from src.screens.pause_screen import PauseScreen
from src.screens.ship_menu import ShipMenu
from src.screens.transition_screen import TransitionScreen
from src.screens.victory import VictoryScreen
from src.systems.combat import CombatState, MechOnGrid
from src.systems.narrative import NarrativeEngine
from src.systems.progression import FloorProgression

logger = logging.getLogger(__name__)
_ERROR_LOG = Path("crash.log")


def _make_combat_grid(
    floor_num: int = 1, is_boss: bool = False, is_elite: bool = False
) -> CombatGrid:
    """Generate a combat grid using the layout template system.

    Args:
        floor_num: Current floor (1-25), determines terrain variety.
        is_boss: Boss encounter — selects boss arena layouts.
        is_elite: Elite encounter — selects challenging layouts.

    Returns:
        A fully validated CombatGrid with terrain from a named layout.
    """
    layout = get_random_layout(floor_num, is_boss, is_elite)
    return layout.build_grid()


def _create_combat_state(
    player_mech: MechOnGrid,
    enemy_mechs: list[tuple[str, int, int]],
    grid: CombatGrid,
) -> CombatState:
    """Create a CombatState with player and enemy mechs."""
    from src.models.faction import Faction, IFFShape
    from src.models.mech import DeployedMech

    mechs = [player_mech]
    for mech_id, col, row in enemy_mechs:
        enemy_frame = MechFrame(
            id=mech_id,
            name="CC Unit",
            faction=Faction.CRIMSON_COMPACT,
            hp=15,
            overload=8,
            iff_shape=IFFShape.SQUARE,
            starting_directives=["rifle_fire", "rifle_fire", "advance"],
        )
        enemy = DeployedMech(
            frame=enemy_frame,
            pilot_callsign="HOSTILE",
            pilot_type="aggressive",
            max_hp=enemy_frame.hp,
            max_ol=enemy_frame.overload,
            current_hp=enemy_frame.hp,
            current_ol=0,
            deck=list(enemy_frame.starting_directives),
        )
        mechs.append(MechOnGrid(mech=enemy, col=col, row=row, friendly=False))
    return CombatState(grid=grid, mechs=mechs)


def run_game(
    display: pygame.Surface,
    monitor: MonitorFrame,
    renderer: TerminalRenderer,
) -> None:
    """Run the full game loop with all screens wired.

    Args:
        display: The Pygame display surface (full window).
        monitor: The monitor frame for compositing.
        renderer: The CRT terminal renderer.
    """
    from src.systems.deckbuilder import build_deployed_mech

    game_data = load_all_data()
    game = Game(renderer, display, monitor=monitor)
    campaign = Campaign()
    audio = SoundManager()
    audio.start_hum()

    # We store mutable state here so nested closures can update it.
    ctx: dict[str, object] = {"mech": None}

    # --- Screen transition helpers ---

    def go_to_mech_select() -> None:
        """Transition from MainMenu to MechSelect with phosphor flicker."""

        def show_mech_select() -> None:
            game.replace_screen(
                MechSelect(
                    renderer,
                    game_data,
                    campaign,
                    on_deploy=_on_deploy,
                )
            )

        ts = TransitionScreen(
            renderer,
            make_signal_acquire(),
            on_complete=show_mech_select,
        )
        game.replace_screen(ts)

    def _on_deploy(
        frame: MechFrame,
        pilot_type: str,
        equipment: dict[str, str | None],
    ) -> None:
        """Deploy selected mech with equipment and go to ShipMenu."""
        try:
            pilot = game_data.get_pilot(pilot_type)
            assert pilot is not None
            deployed = build_deployed_mech(frame, pilot, game_data)
            campaign.current_floor = 1
            ctx["mech"] = deployed

            def show_ship() -> None:
                ship = ShipMenu(
                    renderer,
                    campaign,
                    mech=deployed,
                    on_assault=lambda: go_to_floor_select(),
                    on_salvage=lambda: go_to_floor_select(),
                    on_rest=lambda: go_to_floor_select(),
                )
                game.replace_screen(ship)

            ts = TransitionScreen(
                renderer,
                make_deployment(),
                on_complete=show_ship,
            )
            game.replace_screen(ts)
        except Exception:
            with _ERROR_LOG.open("w") as f:
                traceback.print_exc(file=f)
            raise

    def go_to_floor_select() -> None:
        """Transition from ShipMenu to FloorSelectionScreen."""
        mech = ctx.get("mech")
        if mech is None:
            logger.warning("No deployed mech found")
            return

        progression = FloorProgression(campaign)

        def on_encounter_select(encounter) -> None:  # type: ignore[no-untyped-def]
            from src.models.encounter import EncounterType

            if encounter.encounter_type == EncounterType.COMBAT:
                _start_combat(mech, progression, encounter)
            elif encounter.encounter_type == EncounterType.REST:
                heal = mech.heal(5)
                campaign.current_credits += 10
                logger.info("Rest: healed %d HP", heal)
                _return_to_ship(mech)
            elif encounter.encounter_type == EncounterType.MERCHANT:
                logger.info("Merchant encounter (placeholder)")
                _return_to_ship(mech)
            elif encounter.encounter_type == EncounterType.EVENT:
                _show_event(encounter, mech, progression)

        def show_floor_select() -> None:
            game.replace_screen(
                FloorSelectionScreen(
                    renderer,
                    campaign,
                    progression,
                    on_select=on_encounter_select,
                )
            )

        ts = TransitionScreen(
            renderer,
            make_brief(),
            on_complete=show_floor_select,
        )
        game.replace_screen(ts)

    def _return_to_main() -> None:
        """Transition back to the main menu with signal acquire."""

        def show_main() -> None:
            game.replace_screen(main_menu)

        ts = TransitionScreen(
            renderer,
            make_signal_lost(victory=False),
            on_complete=show_main,
        )
        game.replace_screen(ts)

    def _return_to_ship(mech) -> None:  # type: ignore[no-untyped-def]
        """Transition back to ShipMenu with a brief phosphor flicker."""

        def show_ship() -> None:
            ship = ShipMenu(
                renderer,
                campaign,
                mech=mech,
                on_assault=lambda: go_to_floor_select(),
                on_salvage=lambda: go_to_floor_select(),
                on_rest=lambda: go_to_floor_select(),
            )
            game.replace_screen(ship)

        ts = TransitionScreen(
            renderer,
            make_brief(),
            on_complete=show_ship,
        )
        game.replace_screen(ts)

    def _start_combat(mech, progression, encounter=None):  # type: ignore[no-untyped-def]
        """Start a combat encounter using mission system data.

        Args:
            mech: The player's deployed mech.
            progression: The floor progression manager.
            encounter: Optional Encounter object with enemy spawns.
        """
        floor_num = campaign.current_floor
        is_boss = floor_num in (5, 10, 15, 20, 25)
        is_elite = "elite" in encounter.id if encounter else False

        grid = _make_combat_grid(floor_num, is_boss, is_elite)
        player_mech = MechOnGrid(mech=mech, col=2, row=5, friendly=True)

        # Build enemy list from encounter data or generate defaults
        if encounter is not None and encounter.enemies:
            enemy_tuples = [(e.mech_id, e.grid_col, e.grid_row) for e in encounter.enemies]
        else:
            # Fallback: generate random enemies
            num_enemies = random.randint(1, 2)
            enemy_tuples = [("cc_bastion", 8 + i * 2, 3 + i * 2) for i in range(num_enemies)]

        combat_state = _create_combat_state(player_mech, enemy_tuples, grid)

        def on_combat_complete(final_state) -> None:  # type: ignore[no-untyped-def]
            if final_state.result and final_state.result.victory:
                campaign.current_credits += final_state.result.current_credits_earned
                campaign.enemies_defeated += final_state.result.enemies_defeated
                campaign.cards_played += final_state.result.cards_played

                def show_victory() -> None:
                    victory_screen = VictoryScreen(renderer, campaign, final_state.result)
                    game.replace_screen(victory_screen)

                    def after_victory() -> None:
                        with suppress(ValueError):
                            progression.advance()
                        mech = ctx.get("mech")
                        if mech is not None:
                            _return_to_ship(mech)

                    # Wire the victory button to continue the loop
                    vs = game.current_screen
                    if isinstance(vs, VictoryScreen):
                        vs._btn._on_click = after_victory  # type: ignore[union-attr]

                ts = TransitionScreen(
                    renderer,
                    make_signal_lost(victory=True, outpost_name=campaign.outpost_name),
                    on_complete=show_victory,
                )
                game.replace_screen(ts)
            else:

                def show_game_over() -> None:
                    go_screen = GameOverScreen(renderer, final_state, campaign.floors_cleared)
                    game.replace_screen(go_screen)

                    # Wire redeploy button — restart current floor
                    if isinstance(go_screen, GameOverScreen):
                        go_screen._btn_redeploy._on_click = (  # type: ignore[union-attr]
                            lambda: _return_to_ship(ctx.get("mech")) if ctx.get("mech") else None
                        )
                        # Wire return button — go to main menu
                        go_screen._btn_return._on_click = _return_to_main  # type: ignore[union-attr]

                ts = TransitionScreen(
                    renderer,
                    make_signal_lost(victory=False),
                    on_complete=show_game_over,
                )
                game.replace_screen(ts)

        game.replace_screen(
            CombatScreen(
                renderer,
                combat_state,
                game_data,
                campaign,
                floor=campaign.current_floor,
                on_complete=on_combat_complete,
            )
        )

    def _show_event(encounter, mech, progression):  # type: ignore[no-untyped-def]
        """Show a narrative event."""
        from src.systems.narrative import (
            EventChoice,
            NarrativeEvent,
            Outcome,
        )

        narrative_engine = NarrativeEngine(campaign)
        choices = []
        outcomes = {}
        for i, choice_data in enumerate(encounter.choices):
            outcome_id = choice_data.get("outcome_id", f"outcome_{i}")
            choices.append(
                EventChoice(
                    text=choice_data.get("text", f"Choice {i + 1}"),
                    outcome_id=outcome_id,
                )
            )
            outcomes[outcome_id] = Outcome(
                outcome_id=outcome_id,
                narrative_text=(f"Decision recorded: {choice_data.get('text', 'Unknown')}"),
                reputation_changes={"rebel": random.choice([-5, 0, 5])},
                credits_delta=random.choice([-10, 0, 10]),
            )

        event = NarrativeEvent(
            id=encounter.id,
            title="INTERCEPTED TRANSMISSION",
            narrative_text=encounter.narrative_text,
            choices=choices,
            outcomes=outcomes,
        )

        def on_event_complete(outcome) -> None:  # type: ignore[no-untyped-def]
            campaign.current_credits += outcome.credits_delta
            _return_to_ship(mech)

        game.replace_screen(
            EventScreen(renderer, campaign, event, narrative_engine, on_event_complete)
        )

    # --- Wire MainMenu ---
    main_menu = MainMenu(renderer)
    main_menu.on_new_deployment_cb = go_to_mech_select
    main_menu.on_resume_cb = lambda: None
    main_menu.on_terminate_cb = lambda: pygame.event.post(pygame.Event(pygame.QUIT))

    def show_main_menu() -> None:
        ts = TransitionScreen(
            renderer,
            make_signal_acquire(),
            on_complete=lambda: game.replace_screen(main_menu),
        )
        game.replace_screen(ts)

    # --- Pause handling ---
    # During non-combat screens, Escape pushes PauseScreen.
    # During combat, Escape quits (existing behavior).

    def _try_pause() -> bool:
        """Handle Escape: push pause for non-combat screens, or quit during combat."""
        from src.screens.combat import CombatScreen

        current = game.current_screen
        # Don't pause if we're already on a pause/transition overlay
        if isinstance(current, (PauseScreen, TransitionScreen)):
            return False
        # During combat, let Escape quit as usual
        if isinstance(current, CombatScreen):
            return False
        # Push pause for all other screens
        _push_pause()
        return True

    def _push_pause() -> None:
        """Push the pause screen on top of the current game screen."""
        from src.screens.combat import CombatScreen

        current = game.current_screen

        def do_resume() -> None:
            # Pop the pause screen
            game.pop_screen()

        def do_save() -> None:
            # Placeholder: save campaign state
            logger.info("Save not implemented")

        def do_return_to_base() -> None:
            """Return to the main menu with signal lost transition."""
            game.pop_screen()
            if isinstance(current, CombatScreen):
                return

            def show_main() -> None:
                game.replace_screen(main_menu)

            ts = TransitionScreen(
                renderer,
                make_signal_lost(victory=False),
                on_complete=show_main,
            )
            game.replace_screen(ts)

        pause = PauseScreen(
            renderer,
            campaign,
            on_resume=do_resume,
            on_save=do_save,
            on_return_to_base=do_return_to_base,
        )
        game.push_screen(pause)

    game.on_escape = _try_pause

    # Push BootScreen first; it replaces itself with MainMenu when done
    boot_screen = BootScreen(
        renderer,
        on_complete=show_main_menu,
        on_boot_sound=audio.play_boot,
    )
    game.push_screen(boot_screen)
    game.run(boot_screen)
    audio.stop_hum()
