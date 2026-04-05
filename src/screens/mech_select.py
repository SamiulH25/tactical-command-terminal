"""Mech Select — Deployment Wizard screen.

Four-step wizard with persistent preview panel and faction selection.
Mechs, pilots, and equipment are filtered by faction availability and
unlock status.  Locked content displays with a floor requirement tag.

All positions defined in 1920x1080 base coordinates and scaled proportionally.
"""

from __future__ import annotations

import logging
from collections.abc import Callable

import pygame

from src import config
from src.core.terminal import TerminalRenderer
from src.models.campaign import Campaign
from src.models.data_loader import GameData
from src.models.faction import FACTION_COLOUR, Faction
from src.models.mech import MechFrame
from src.models.pilot import Pilot
from src.screens.base_screen import Screen
from src.ui.button import TerminalButton
from src.ui.layout import refresh, s, sx, sy
from src.ui.panel import Panel
from src.ui.text import pad, ratio_bar
from src.ui.war_comms_widget import WarCommsWidget

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_IFF_SYMBOLS: dict[str, str] = {
    "SQUARE": "\u25c8",
    "DIAMOND": "\u25c6",
    "HEXAGON": "\u2b22",
    "CIRCLE_CROSS": "\u25c9",
    "CHEVRON": "\u27e9",
    "TRIANGLE": "\u25b2",
    "RECTANGLE": "\u25ac",
    "CIRCLE": "\u25cf",
    "CROSS": "\u271b",
}

_STEP_LABELS: dict[int, str] = {
    1: "FACTION SELECTION",
    2: "UNIT SELECTION",
    3: "OPERATOR ASSIGNMENT",
    4: "EQUIPMENT LOADOUT",
    5: "DEPLOYMENT CONFIRMATION",
}

_SLOT_NAMES: dict[str, str] = {
    "weapon": "WEAPON",
    "armor": "ARMOUR",
    "utility": "UTILITY",
}

# Minimum floors cleared to unlock each faction.
_FACTION_UNLOCK_FLOORS: dict[Faction, int] = {
    Faction.FSA: 0,
    Faction.CRIMSON_COMPACT: 5,
    Faction.REBEL: 10,
}

# Minimum floors cleared to unlock each mech within its faction.
# Key: mech_id, Value: floors required (0 = available from start).
_MECH_UNLOCK_FLOORS: dict[str, int] = {
    # FSA
    "fsa_bastion": 0,
    "fsa_raptor": 0,
    "fsa_anvil": 2,
    "fsa_warden": 4,
    "fsa_wraith": 7,
    # CC
    "cc_bastion": 5,
    "cc_sentinel": 6,
    "cc_siege": 8,
    "cc_warden": 10,
    # Rebel
    "rebel_ghost": 10,
    "rebel_rustbucket": 12,
    "rebel_warlord": 15,
}

# Equipment filtered by faction defaults (all equipment is FSA by default).
# Key: equipment_id, Value: faction that can use it.
_EQUIPMENT_FACTION: dict[str, Faction] = {
    # FSA
    "autocannon_mk1": Faction.FSA,
    "rifle_mk1": Faction.FSA,
    "heavy_cannon_mk1": Faction.FSA,
    "precision_rifle": Faction.FSA,
    "light_plating": Faction.FSA,
    "medium_plating": Faction.FSA,
    "heavy_plating": Faction.FSA,
    "reinforced_joints": Faction.FSA,
    "stealth_coating": Faction.FSA,
    "field_medic": Faction.FSA,
    "sensor_array": Faction.FSA,
    "ammo_feeder": Faction.FSA,
    "shield_generator": Faction.FSA,
    "optical_camouflage": Faction.FSA,
}

# Pilots — all pilots are available to FSA.  CC and Rebel pilots
# would be added as separate entries if the game had faction-specific pilots.
# For now, all pilots are FSA-aligned.
_PILOT_FACTION: dict[str, Faction] = {
    "aggressive": Faction.FSA,
    "defensive": Faction.FSA,
    "tactical": Faction.FSA,
    "scout": Faction.FSA,
    "engineer": Faction.FSA,
}


class MechSelect(Screen):
    """Deployment Wizard with faction selection, progression unlocks,
    and persistent preview panel."""

    def __init__(
        self,
        renderer: TerminalRenderer,
        game_data: GameData,
        campaign: Campaign,
        on_deploy: Callable[[MechFrame, str, dict[str, str | None]], None] | None = None,
    ) -> None:
        super().__init__(renderer)
        self._game_data = game_data
        self._campaign = campaign
        self.on_deploy = on_deploy

        self._step = 1
        self._max_steps = 5
        self._selected_faction: Faction = Faction.FSA
        self._selected_frame: MechFrame | None = None
        self._selected_pilot: Pilot | None = None
        self._equipment: dict[str, str | None] = {
            "weapon": None,
            "armor": None,
            "utility": None,
        }
        self._equip_open_slot: str | None = None
        self._equip_scroll: dict[str, int] = {
            "weapon": 0,
            "armor": 0,
            "utility": 0,
        }

        self._font: pygame.font.Font | None = None
        self._small_font: pygame.font.Font | None = None
        self._header_font: pygame.font.Font | None = None
        self._mouse_pos: tuple[int, int] | None = None
        self._step_buttons: list[TerminalButton] = []
        self._nav_buttons: list[TerminalButton] = []
        self._faction_buttons: list[TerminalButton] = []
        self._preview_panel: Panel | None = None
        self._content_panel: Panel | None = None
        self._cursor_visible: bool = True
        self._cursor_timer: float = 0.0
        self._war_comms = WarCommsWidget()

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def on_enter(self) -> None:
        """Initialise mech select screen."""
        self._step = 1
        self._selected_faction = Faction.FSA
        self._selected_frame = None
        self._selected_pilot = None
        self._equipment = {"weapon": None, "armor": None, "utility": None}
        self._equip_open_slot = None
        self._equip_scroll = {"weapon": 0, "armor": 0, "utility": 0}
        self._font = pygame.font.SysFont("consolas", config.FONT_SIZE)
        self._small_font = pygame.font.SysFont("consolas", config.FONT_SIZE_SMALL)
        self._header_font = pygame.font.SysFont("consolas", config.FONT_SIZE_HEADER)
        self._cursor_visible = True
        self._cursor_timer = 0.0
        self._war_comms.set_fonts(self._font, self._small_font)
        self._build_panels()
        self._build_faction_buttons()
        self._build_step_buttons()
        self._build_nav_buttons()
        logger.info(
            "MechSelect entered — faction=%s, mechs_available=%d, floors_cleared=%d",
            self._selected_faction.name,
            len(self._get_faction_mechns(self._selected_faction)),
            self._campaign.floors_cleared,
        )

    def _is_faction_unlocked(self, faction: Faction) -> bool:
        required = _FACTION_UNLOCK_FLOORS.get(faction, 99)
        return self._campaign.floors_cleared >= required

    def _is_mech_unlocked(self, mech: MechFrame) -> bool:
        required = _MECH_UNLOCK_FLOORS.get(mech.id, 99)
        return self._campaign.floors_cleared >= required

    def _get_faction_mechns(self, faction: Faction) -> list[MechFrame]:
        return [m for m in self._game_data.mech_frames if m.faction == faction]

    def _get_faction_color(self, faction: Faction) -> tuple[int, int, int]:
        return FACTION_COLOUR.get(faction, config.PHOSPHOR_GREEN)

    def _build_panels(self) -> None:
        refresh(self.display)
        _w, _h = self.display.get_size()
        self._content_panel = Panel(*s(20, 100, 1100, 850))
        self._preview_panel = Panel(*s(1150, 100, 350, 850), "DEPLOYMENT SUMMARY")

    def _build_faction_buttons(self) -> None:
        self._faction_buttons.clear()
        refresh(self.display)
        font = self._font
        if font is None:
            return

        btn_w, btn_h = 200, 32
        x_start = sx(40)
        y = sy(104)
        spacing = sx(10)

        for i, faction in enumerate(Faction):
            unlocked = self._is_faction_unlocked(faction)
            label = faction.name.replace("_", " ")
            if not unlocked:
                floors_needed = _FACTION_UNLOCK_FLOORS.get(faction, 0)
                label = f"{label} [F{floors_needed:02d}]"
            if faction == self._selected_faction:
                label = f"> {label}"

            btn = TerminalButton(
                x_start + i * (btn_w + spacing),
                y,
                btn_w,
                btn_h,
                label=label,
                on_click=lambda f=faction: self._select_faction(f),
                enabled=unlocked,
            )
            self._faction_buttons.append(btn)

    def _build_step_buttons(self) -> None:
        self._step_buttons.clear()
        font = self._font
        if font is None:
            return
        cp = self._content_panel
        assert cp is not None
        refresh(self.display)

        btn_w, btn_h = 320, 32
        btn_x, y_start = cp.rect.left + sx(20), cp.rect.top + sy(40)

        if self._step == 1:
            self._build_faction_content(cp, btn_x, y_start, btn_h)
        elif self._step == 2:
            self._build_unit_buttons(cp, btn_x, y_start, btn_w, btn_h)
        elif self._step == 3:
            self._build_pilot_buttons(cp, btn_x, y_start, btn_w, btn_h)
        elif self._step == 4:
            self._build_equipment_buttons(cp, btn_x, y_start, btn_h)
        elif self._step == 5:
            self._build_confirmation_content(cp, btn_x, y_start, btn_h)

    def _build_faction_content(self, cp: Panel, btn_x: int, y_start: int, btn_h: int) -> None:
        """Show faction descriptions and unlock requirements."""
        small_font = self._small_font
        if small_font is None:
            return
        logger.debug("Building faction content for step %d", self._step)

        faction_descs: dict[Faction, str] = {
            Faction.FSA: (
                "Free Systems Alliance — your home faction.\n"
                "  Standard-issue mechs and reliable equipment.\n"
                "  Full access to all tactical directives."
            ),
            Faction.CRIMSON_COMPACT: (
                "Crimson Compact — captured enemy technology.\n"
                "  Heavy armor and bombardment focus.\n"
                "  Requires Floor 05 clearance to access."
            ),
            Faction.REBEL: (
                "Rebel scavengers — improvised battlefield tech.\n"
                "  High evasion, unpredictable but dangerous.\n"
                "  Requires Floor 10 clearance to access."
            ),
        }

        y = y_start
        max_y = cp.rect.bottom - sy(24)
        for faction in Faction:
            if y + btn_h > max_y:
                logger.warning(
                    "Faction content overflow at %s — y=%d exceeds max_y=%d",
                    faction.name,
                    y,
                    max_y,
                )
                break

            unlocked = self._is_faction_unlocked(faction)
            label = faction.name.replace("_", " ").upper()
            if faction == self._selected_faction and unlocked:
                label = f"> {label} [SELECTED]"
            elif not unlocked:
                needed = _FACTION_UNLOCK_FLOORS.get(faction, 0)
                label = f"{label} [LOCKED — Floor {needed:02d} Required]"
            elif faction == self._selected_faction:
                label = f"> {label} [SELECTED]"
            else:
                label = f"{label} [SELECT]"

            self._step_buttons.append(
                TerminalButton(
                    btn_x,
                    y,
                    sx(400),
                    btn_h,
                    label=label,
                    on_click=lambda f=faction: self._select_faction(f),
                    enabled=unlocked,
                )
            )

            # Description below button — with bounds checking
            desc = faction_descs.get(faction, "")
            for line in desc.split("\n"):
                if y + btn_h + sy(16) > max_y:
                    break
                desc_surf = small_font.render(line, True, config.PHOSPHOR_DIM)
                self.display.blit(desc_surf, (btn_x + sx(4), y + btn_h + 2))
                y += sy(16)

            y += sy(12)

        logger.info(
            "Faction content complete — %d buttons, final y=%d, max_y=%d",
            len(self._step_buttons),
            y,
            max_y,
        )

    def _build_unit_buttons(
        self, cp: Panel, btn_x: int, y_start: int, btn_w: int, btn_h: int
    ) -> None:
        """Build mech selection buttons with bounds checking."""
        mechs = self._get_faction_mechns(self._selected_faction)
        max_y = cp.rect.bottom - sy(24)
        logger.info(
            "Building unit buttons — faction=%s, mechs=%d",
            self._selected_faction.name,
            len(mechs),
        )

        for i, mech in enumerate(mechs):
            btn_y = y_start + i * sy(38)
            if btn_y + btn_h > max_y:
                logger.warning("Unit button %d overflow — y=%d exceeds max_y=%d", i, btn_y, max_y)
                break

            unlocked = self._is_mech_unlocked(mech)
            selected = self._selected_frame == mech
            status = "[SELECTED]" if selected else "[SELECT]"

            if not unlocked:
                needed = _MECH_UNLOCK_FLOORS.get(mech.id, 0)
                status = f"[LOCKED — Floor {needed:02d}]"

            label = (
                f"[{i + 1}] {mech.name.upper():<14s} "
                f"HP:{pad(mech.hp)}  OL:{pad(mech.overload)}  {status}"
            )
            self._step_buttons.append(
                TerminalButton(
                    btn_x,
                    btn_y,
                    btn_w,
                    btn_h,
                    label=label,
                    on_click=lambda m=mech: self._select_unit(m),
                    enabled=unlocked,
                )
            )

        logger.debug("Created %d unit buttons", len(self._step_buttons))

    def _build_pilot_buttons(
        self, cp: Panel, btn_x: int, y_start: int, btn_w: int, btn_h: int
    ) -> None:
        """Build pilot selection buttons with bounds checking."""
        pilot_types = [
            ("aggressive", "Aggressive — +2 DMG, +Suppressing Fire"),
            ("defensive", "Defensive — +5 HP, +2 OL, +Fortify"),
            ("tactical", "Tactical — +4 OL, +5 EVA, +Overwatch"),
            ("scout", "Scout — +1 DMG, +10 EVA, +Scan"),
            ("engineer", "Engineer — +3 HP, +Patch Up"),
        ]
        max_y = cp.rect.bottom - sy(24)
        logger.debug("Building pilot buttons — %d pilot types", len(pilot_types))

        count = 0
        for _i, (pkey, desc) in enumerate(pilot_types):
            pilot = self._game_data.get_pilot(pkey)
            if pilot is None:
                logger.warning("Pilot type %s not found in game data", pkey)
                continue

            btn_y = y_start + count * sy(38)
            if btn_y + btn_h > max_y:
                logger.warning("Pilot button overflow — y=%d exceeds max_y=%d", btn_y, max_y)
                break

            selected = (
                self._selected_pilot is not None and self._selected_pilot.operator_type == pkey
            )
            status = "[SELECTED]" if selected else "[SELECT]"
            label = f"[{count + 1}] {desc:<44s} {status}"
            self._step_buttons.append(
                TerminalButton(
                    btn_x,
                    btn_y,
                    btn_w + sx(60),
                    btn_h,
                    label=label,
                    on_click=lambda pk=pkey: self._select_pilot(pk),
                )
            )
            count += 1

        logger.debug("Created %d pilot buttons", count)

    def _build_equipment_buttons(
        self,
        cp: Panel,
        btn_x: int,
        y_start: int,
        btn_h: int,
    ) -> None:
        """Build slot buttons with proper vertical spacing for expanded
        dropdowns.  Each expanded section pushes subsequent slots down."""
        refresh(self.display)
        max_y = cp.rect.bottom - sy(24)
        btn_h_header = sy(30)
        btn_h_item = sy(28)
        items_visible = max(2, (max_y - y_start - sy(100)) // btn_h_item)
        logger.debug(
            "Building equipment buttons — max_y=%d, items_visible=%d",
            max_y,
            items_visible,
        )

        y = y_start
        for slot in ("weapon", "armor", "utility"):
            eq_id = self._equipment.get(slot)
            eq_name = "(None)"
            if eq_id:
                eq = self._game_data.get_equipment(eq_id)
                if eq:
                    eq_name = eq.name
            arrow = "\u25bc" if self._equip_open_slot == slot else "\u25b6"
            header_label = f"  {arrow} {_SLOT_NAMES[slot]:>8s}: {eq_name}"
            self._step_buttons.append(
                TerminalButton(
                    btn_x,
                    y,
                    sx(360),
                    btn_h_header,
                    label=header_label,
                    on_click=lambda s=slot: self._toggle_slot(s),
                )
            )
            section_height = btn_h_header + sy(4)

            if self._equip_open_slot == slot:
                items = [eq for eq in self._game_data.equipment if eq.slot == slot]
                scroll = self._equip_scroll.get(slot, 0)
                logger.debug(
                    "Expanded slot %s — items=%d, scroll=%d",
                    slot,
                    len(items),
                    scroll,
                )
                visible_count = 0
                for i in range(items_visible):
                    idx = scroll + i
                    if idx >= len(items):
                        break
                    item_y = y + section_height + visible_count * btn_h_item
                    if item_y + btn_h_item > max_y:
                        logger.warning(
                            "Equipment item overflow — slot=%s, item_y=%d, max_y=%d",
                            slot,
                            item_y,
                            max_y,
                        )
                        break
                    visible_count += 1
                    eq = items[idx]
                    sel = self._equipment.get(slot) == eq.id
                    status = "[EQUIPPED]" if sel else "[SELECT]"
                    label = f"      {eq.name:<20s} {status}"
                    self._step_buttons.append(
                        TerminalButton(
                            btn_x + sx(10),
                            item_y,
                            sx(330),
                            btn_h_item - 2,
                            label=label,
                            on_click=lambda s=slot, eid=eq.id: self._select_equipment(s, eid),
                        )
                    )

                none_y = y + section_height + visible_count * btn_h_item
                if none_y + btn_h_item <= max_y:
                    visible_count += 1
                    none_sel = self._equipment.get(slot) is None
                    none_status = "[DEFAULT]" if none_sel else "[SELECT]"
                    self._step_buttons.append(
                        TerminalButton(
                            btn_x + sx(10),
                            none_y,
                            sx(330),
                            btn_h_item - 2,
                            label=f"      {'(None)':<20s} {none_status}",
                            on_click=lambda s=slot: self._select_equipment(s, None),
                        )
                    )

                section_height += visible_count * btn_h_item + sy(6)

            y += section_height

    def _build_confirmation_content(self, cp: Panel, btn_x: int, y_start: int, btn_h: int) -> None:
        """Show deployment confirmation with lore-accurate details."""
        refresh(self.display)
        font = self._font
        if font is None:
            return

        mech_name = self._selected_frame.name.upper() if self._selected_frame else "UNKNOWN"
        pilot_name = self._selected_pilot.callsign if self._selected_pilot else "UNASSIGNED"
        logger.info(
            "Building confirmation — mech=%s, pilot=%s",
            mech_name,
            pilot_name,
        )

        lines = [
            "> DEPLOYMENT AUTHORIZED",
            f"  UNIT: {mech_name}",
            f"  OPERATOR: {pilot_name}",
            "  DROP ZONE: Outpost Alpha",
            "  ESTIMATED OPPOSITION: MODERATE",
        ]
        y = y_start
        max_y = cp.rect.bottom - sy(24)
        for line in lines:
            if y + sy(28) > max_y:
                logger.warning("Confirmation text overflow at y=%d", y)
                break
            surf = font.render(line, True, config.PHOSPHOR_GREEN)
            self.display.blit(surf, (btn_x, y))
            y += sy(28)

        # Confirm deployment button
        self._step_buttons.append(
            TerminalButton(
                btn_x,
                y + sy(12),
                sx(360),
                btn_h,
                "[CONFIRM DEPLOYMENT]",
                on_click=self._on_deploy,
                enabled=self._selected_frame is not None,
            )
        )

    def _build_nav_buttons(self) -> None:
        """Build navigation buttons with bounds checking."""
        self._nav_buttons.clear()
        refresh(self.display)
        # Step 5 uses inline confirm button — skip nav buttons
        if self._step == 5:
            return
        w, _ = self.display.get_size()
        can_back = self._step > 1
        can_next = self._step < self._max_steps and self._is_step_valid()
        logger.debug(
            "Building nav buttons — step=%d, can_back=%s, can_next=%s",
            self._step,
            can_back,
            can_next,
        )

        self._nav_buttons.append(
            TerminalButton(
                w - sx(260),
                sy(500),
                sx(100),
                sy(36),
                "[< BACK]",
                on_click=self._on_back,
                enabled=can_back,
            )
        )
        if self._step < self._max_steps:
            self._nav_buttons.append(
                TerminalButton(
                    w - sx(150),
                    sy(500),
                    sx(100),
                    sy(36),
                    "[NEXT >]",
                    on_click=self._on_next,
                    enabled=can_next,
                )
            )
        else:
            self._nav_buttons.append(
                TerminalButton(
                    w - sx(150),
                    sy(500),
                    sx(100),
                    sy(36),
                    "[DEPLOY >]",
                    on_click=self._on_deploy,
                    enabled=self._selected_frame is not None,
                )
            )

    def _is_step_valid(self) -> bool:
        if self._step == 2:
            return self._selected_frame is not None
        if self._step == 3:
            return self._selected_pilot is not None
        return True

    def _select_faction(self, faction: Faction) -> None:
        if not self._is_faction_unlocked(faction):
            return
        self._selected_faction = faction
        self._selected_frame = None  # Reset mech when faction changes
        self._build_faction_buttons()
        self._build_step_buttons()
        self._build_nav_buttons()

    def _select_unit(self, mech: MechFrame) -> None:
        if not self._is_mech_unlocked(mech):
            return
        self._selected_frame = mech
        self._build_step_buttons()
        self._build_nav_buttons()

    def _select_pilot(self, pilot_key: str) -> None:
        pilot = self._game_data.get_pilot(pilot_key)
        if pilot is not None:
            self._selected_pilot = pilot
            self._build_step_buttons()
            self._build_nav_buttons()

    def _select_equipment(self, slot: str, equip_id: str | None) -> None:
        self._equipment[slot] = equip_id
        self._build_step_buttons()

    def _toggle_slot(self, slot: str) -> None:
        if self._equip_open_slot == slot:
            self._equip_open_slot = None
        else:
            self._equip_open_slot = slot
            self._equip_scroll[slot] = 0
        self._build_step_buttons()

    def _on_next(self) -> None:
        if self._step < self._max_steps and self._is_step_valid():
            self._step += 1
            self._build_step_buttons()
            self._build_nav_buttons()

    def _on_back(self) -> None:
        if self._step > 1:
            self._step -= 1
            self._build_step_buttons()
            self._build_nav_buttons()

    def _on_deploy(self) -> None:
        """Deploy selected mech and transition to ship menu."""
        if self._selected_frame is not None and self.on_deploy is not None:
            pilot_type = (
                self._selected_pilot.operator_type if self._selected_pilot else "aggressive"
            )
            logger.info(
                "Deploying — frame=%s, pilot=%s, equipment=%s",
                self._selected_frame.id,
                pilot_type,
                self._equipment,
            )
            self.on_deploy(self._selected_frame, pilot_type, dict(self._equipment))
        else:
            logger.warning(
                "Deploy attempted with frame=%s, on_deploy_cb=%s",
                self._selected_frame,
                self.on_deploy is not None,
            )

    # ------------------------------------------------------------------
    # Events
    # ------------------------------------------------------------------

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEMOTION:
            self._mouse_pos = event.pos
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._mouse_pos = event.pos
            for btn in self._step_buttons + self._nav_buttons + self._faction_buttons:
                btn.set_hover(self._mouse_pos)
                if btn.click():
                    return
        elif event.type == pygame.MOUSEWHEEL and self._step == 4:
            if self._equip_open_slot:
                self._equip_scroll[self._equip_open_slot] = max(
                    0,
                    self._equip_scroll[self._equip_open_slot] - event.y * 2,
                )
                self._build_step_buttons()
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP and self._step == 4:
                if self._equip_open_slot:
                    self._equip_scroll[self._equip_open_slot] = max(
                        0,
                        self._equip_scroll[self._equip_open_slot] - 1,
                    )
                    self._build_step_buttons()
            elif event.key == pygame.K_DOWN and self._step == 4 and self._equip_open_slot:
                self._equip_scroll[self._equip_open_slot] += 1
                self._build_step_buttons()
            elif event.key in (pygame.K_1, pygame.K_2, pygame.K_3):
                idx = event.key - pygame.K_1
                if idx < len(self._faction_buttons):
                    self._faction_buttons[idx].click()

    def update(self, dt: float) -> None:
        for btn in self._step_buttons + self._nav_buttons + self._faction_buttons:
            btn.set_hover(self._mouse_pos)
        self._cursor_timer += dt
        if self._cursor_timer >= 0.6:
            self._cursor_timer = 0.0
            self._cursor_visible = not self._cursor_visible
        self._war_comms.update(dt)

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def render(self) -> None:
        surface = self.display
        refresh(surface)
        font = self._font
        small_font = self._small_font
        header_font = self._header_font
        assert font is not None
        assert small_font is not None
        assert header_font is not None

        w, h = surface.get_size()

        # Top bezel — match MainMenu style
        left = font.render("> FSA-TD-47", True, config.PHOSPHOR_GREEN)
        right = font.render("CH:01 // LINK ACTIVE", True, config.PHOSPHOR_DIM)
        surface.blit(left, (sx(40), sy(20)))
        surface.blit(right, (w - right.get_width() - sx(40), sy(20)))
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

        # Step header
        step_text = (
            f"> DEPLOYMENT WIZARD    STEP {self._step}/{self._max_steps}: "
            f"{_STEP_LABELS.get(self._step, '')}"
        )
        step_surf = font.render(step_text, True, config.PHOSPHOR_GREEN)
        surface.blit(step_surf, (sx(40), sy(66)))
        pygame.draw.line(surface, config.PHOSPHOR_GREEN, (sx(40), sy(96)), (w - sx(40), sy(96)))

        # Faction buttons (always visible)
        for btn in self._faction_buttons:
            btn.render(surface, font)

        # Content panel
        cp = self._content_panel
        assert cp is not None
        cp.render(surface, font, header_font)

        if self._step == 1:
            title = font.render("> FACTION ACCESS", True, config.PHOSPHOR_GREEN)
            surface.blit(title, (cp.rect.left + sx(16), cp.rect.top + sy(4)))
        elif self._step == 2:
            title = font.render("> AVAILABLE UNITS", True, config.PHOSPHOR_GREEN)
            surface.blit(title, (cp.rect.left + sx(16), cp.rect.top + sy(4)))
        elif self._step == 3:
            title = font.render("> ASSIGN OPERATOR", True, config.PHOSPHOR_GREEN)
            surface.blit(title, (cp.rect.left + sx(16), cp.rect.top + sy(4)))
        elif self._step == 4 and self._equip_open_slot:
            items = [eq for eq in self._game_data.equipment if eq.slot == self._equip_open_slot]
            total = len(items) + 1
            scroll = self._equip_scroll.get(self._equip_open_slot, 0)
            hint = (
                f"  [{scroll + 1}-{min(scroll + 8, total)}/{total}]  UP/DOWN keys or scroll wheel"
            )
            surface.blit(
                small_font.render(hint, True, config.PHOSPHOR_DIM),
                (cp.rect.left + sx(16), cp.rect.bottom - sy(18)),
            )
        elif self._step == 5:
            title = font.render("> DEPLOYMENT CONFIRMATION", True, config.PHOSPHOR_GREEN)
            surface.blit(title, (cp.rect.left + sx(16), cp.rect.top + sy(4)))

        for btn in self._step_buttons:
            btn.render(surface, font)

        # Preview panel
        pp = self._preview_panel
        assert pp is not None
        pp.render(surface, font, header_font)
        self._render_preview(surface, font, small_font)

        # Navigation
        for btn in self._nav_buttons:
            btn.render(surface, font)

        # Flavour text below content panel
        mp = cp.rect
        flavour_y = mp.bottom + sy(8)
        flavour_lines = [
            f"> CLEARANCE: {self._campaign.floors_cleared:03d} FLOORS",
            f"> FACTION: {self._selected_faction.name.replace('_', ' ').upper()}",
        ]
        for line in flavour_lines:
            fsurf = small_font.render(line, True, config.PHOSPHOR_DIM)
            surface.blit(fsurf, (mp.left + sx(30), flavour_y))
            flavour_y += sy(20)

        # War effort comms — bottom right, below flavour text
        comms_w = sx(700)
        comms_h = sy(100)
        comms_x = w - sx(730)
        comms_y = h - comms_h - sy(8)
        self._war_comms.render(surface, comms_x, comms_y, comms_w, comms_h)

    def _render_preview(
        self,
        surface: pygame.Surface,
        font: pygame.font.Font,
        small_font: pygame.font.Font,
    ) -> None:
        """Render preview panel content with bounds checking."""
        pp = self._preview_panel
        assert pp is not None
        x = pp.rect.left + sx(12)
        y = pp.rect.top + sy(24)
        max_y = pp.rect.bottom - sy(8)

        if self._selected_frame is None:
            surface.blit(
                small_font.render("  No unit selected", True, config.PHOSPHOR_DIM),
                (x, y),
            )
            return

        mech = self._selected_frame
        iff_sym = _IFF_SYMBOLS.get(mech.iff_shape.name, "?")
        iff_col = self._get_faction_color(self._selected_faction)

        if y + sy(24) > max_y:
            return
        surface.blit(font.render(iff_sym, True, iff_col), (x, y))
        surface.blit(
            font.render(mech.name.upper(), True, config.PHOSPHOR_GREEN),
            (x + sx(24), y),
        )
        y += sy(24)

        op_name = "—"
        if self._selected_pilot:
            op_name = self._selected_pilot.callsign
        if y + sy(20) <= max_y:
            surface.blit(
                small_font.render(f"  OP: {op_name}", True, config.PHOSPHOR_GREEN),
                (x, y),
            )
        y += sy(20)

        for slot in ("weapon", "armor", "utility"):
            eq_id = self._equipment.get(slot)
            eq_name = "(None)"
            if eq_id:
                eq = self._game_data.get_equipment(eq_id)
                if eq:
                    eq_name = eq.name
            if y + sy(18) <= max_y:
                surface.blit(
                    small_font.render(
                        f"  {_SLOT_NAMES[slot]:<8s}: {eq_name}",
                        True,
                        config.PHOSPHOR_DIM,
                    ),
                    (x, y),
                )
            y += sy(18)

        y += sy(8)

        pilot_bonus_hp = 0
        pilot_bonus_ol = 0
        pilot_bonus_dmg = 0
        if self._selected_pilot:
            pilot_bonus_hp = self._selected_pilot.hp_bonus
            pilot_bonus_ol = self._selected_pilot.ol_bonus
            pilot_bonus_dmg = self._selected_pilot.damage_bonus

        eq_hp = 0
        eq_eva = 0
        eq_ol_disc = 0
        for slot in ("weapon", "armor", "utility"):
            eq_id = self._equipment.get(slot)
            if eq_id:
                eq = self._game_data.get_equipment(eq_id)
                if eq:
                    eq_hp += eq.hp_bonus
                    eq_eva += eq.evasion_bonus
                    eq_ol_disc += eq.ol_discount
                    if eq.slot == "weapon":
                        pilot_bonus_dmg += eq.damage_bonus

        total_hp = mech.hp + pilot_bonus_hp + eq_hp
        total_ol = mech.overload + pilot_bonus_ol
        total_eva = mech.evasion + eq_eva

        hp_bar = ratio_bar(total_hp, total_hp, bar_width=16)
        if y + sy(18) <= max_y:
            surface.blit(
                small_font.render(f"  HP: {hp_bar}  {total_hp:03d}", True, config.PHOSPHOR_GREEN),
                (x, y),
            )
        y += sy(18)

        ol_bar = ratio_bar(0, total_ol, bar_width=16)
        if y + sy(18) <= max_y:
            surface.blit(
                small_font.render(f"  OL: {ol_bar}  {total_ol:02d}", True, config.COLOR_WARNING),
                (x, y),
            )
        y += sy(18)

        for line in [
            f"  EVA: {total_eva:+d}%",
            f"  DMG: +{pilot_bonus_dmg}",
            f"  OL-: -{eq_ol_disc}",
            f"  CARDS: {len(mech.starting_directives):02d}",
        ]:
            if y + sy(16) <= max_y:
                surface.blit(small_font.render(line, True, config.PHOSPHOR_DIM), (x, y))
            y += sy(16)

        if mech.trait and y < max_y:
            trait_parts = mech.trait.split(":", 1)
            tag = trait_parts[0].strip().upper()
            desc = trait_parts[1].strip() if len(trait_parts) > 1 else mech.trait
            surface.blit(
                small_font.render(f"  [{tag}] {desc}", True, config.PHOSPHOR_DIM),
                (x, y),
            )
