"""Mission types and enemy composition pools.

Each mission type defines a distinct combat scenario with unique
objectives, enemy compositions, narrative text, and reward scaling.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from enum import Enum, auto

from src.models.encounter import Encounter, EncounterType, EnemySpawn

# ---------------------------------------------------------------------------
# Mission Type enum
# ---------------------------------------------------------------------------


class MissionType(Enum):
    """Distinct combat mission scenarios."""

    PATROL = auto()  #: Standard enemy patrol engagement
    ASSAULT = auto()  #: Attack fortified position
    DEFENSE = auto()  #: Hold position against waves
    EXTRACTION = auto()  #: Reach extraction point under fire
    SABOTAGE = auto()  #: Destroy enemy infrastructure
    ELITE = auto()  #: Elite enemy commander
    BOSS = auto()  #: Floor boss encounter
    AMBUSH = auto()  #: Surprise attack from multiple vectors


# ---------------------------------------------------------------------------
# Enemy pools by floor range
# ---------------------------------------------------------------------------

# Available enemy mech IDs by floor range.
_ENEMY_POOLS: dict[tuple[int, int], list[str]] = {
    (1, 5): ["cc_bastion", "cc_sentinel"],
    (6, 10): ["cc_bastion", "cc_sentinel", "cc_warden"],
    (11, 15): ["cc_bastion", "cc_siege", "cc_warden", "cc_sentinel"],
    (16, 20): ["cc_siege", "cc_warden", "cc_sentinel", "cc_bastion"],
    (21, 25): ["cc_siege", "cc_warden", "cc_bastion"],
}

# Boss enemy IDs
_BOSS_ENEMIES: dict[int, str] = {
    5: "cc_warden",
    10: "cc_siege",
    15: "cc_bastion",
    20: "cc_siege",
    25: "cc_warden",
}

# Elite enemy IDs
_ELITE_ENEMIES = ["cc_siege", "cc_warden"]


# ---------------------------------------------------------------------------
# Mission narrative text pools
# ---------------------------------------------------------------------------

_PATROL_TEXT = [
    "Enemy patrol detected on the perimeter. Light resistance expected.",
    "Scout drones report hostile movement in sector. Standard patrol formation.",
    "Crimson Compact patrol route intersects our drop zone. Engagement advised.",
    "Routine sweep identifies enemy patrol. Minimal threat assessment.",
    "Perimeter sensors detect hostile mech signatures. Standard engagement protocols.",
]

_ASSAULT_TEXT = [
    "Fortified enemy position identified. Heavy resistance expected.",
    "Assault target confirmed. Enemy fortifications detected.",
    "Command authorises assault on fortified position. Expect heavy resistance.",
    "Enemy strongpoint located. Breach and clear orders authorised.",
    "Strike team briefed on assault objectives. Enemy entrenchment confirmed.",
]

_DEFENSE_TEXT = [
    "Hold this position. Enemy counter-attack imminent.",
    "Defensive orders received. Hold the line at all costs.",
    "Enemy forces mobilising for counter-offensive. Prepare defensive posture.",
    "Forward operating base under threat. Defensive perimeter required.",
    "Relay station needs protection. Hold until reinforcements arrive.",
]

_EXTRACTION_TEXT = [
    "Extraction point compromised. Fight your way to the evac zone.",
    "Downed pilot signal detected. Reach their position and extract under fire.",
    "Supply cache located behind enemy lines. Retrieve and extract.",
    "Allied unit pinned down. Break through and escort to safety.",
    "Intel package located in hostile territory. Secure and extract.",
]

_SABOTAGE_TEXT = [
    "Enemy communications relay identified. Destroy the infrastructure.",
    "Ammo depot coordinates confirmed. Sabotage operations authorised.",
    "Enemy supply line vulnerable. Disrupt their logistics.",
    "Shield generator location identified. Disable it to weaken their defences.",
    "Command bunker structural weakness detected. Bring it down.",
]

_ELITE_TEXT = [
    "Elite enemy commander detected in sector. High threat level.",
    "Crimson Compact ace pilot signature identified. Engage with extreme caution.",
    "Veteran enemy unit operating in this sector. Expect superior tactics.",
    "Command warns of elite hostile in the area. Maximum combat readiness.",
    "High-value enemy target confirmed. Priority elimination orders.",
]

_BOSS_TEXT = [
    "BOSS ENCOUNTER: Crimson Compact Commander detected. All units engage.",
    "FINAL THREAT: Enemy warlord commanding this outpost. Eliminate to secure the sector.",
    "CRITICAL: Fortress commander mobilising defences. Decapitation strike authorised.",
    "OMEGA PRIORITY: Enemy field marshal identified. Mission success requires elimination.",
    "SUPREME THREAT: Compact general commanding from forward bunker. End this war.",
]

_AMBUSH_TEXT = [
    "WARNING: Enemy forces converging from multiple vectors. Ambush in progress.",
    "Contact from multiple bearings. Enemy pincer movement detected.",
    "Trap sprung — hostiles closing from all sides. Fight your way out.",
    "Surprise contact — enemy prepared killing zone. Break the encirclement.",
    "Multiple hostile signatures approaching. Coordinated ambush formation.",
]

# Success / failure text
_SUCCESS_TEXT = [
    "Sector secured. Hostiles eliminated.",
    "Mission objectives complete. Area is clear.",
    "Target neutralised. Position is secure.",
    "Enemy forces routed. Area under our control.",
    "Objectives achieved. Awaiting further orders.",
]

_BOSS_SUCCESS = [
    "Commander eliminated. The outpost falls.",
    "Warlord destroyed. Enemy command structure collapses.",
    "Field marshal neutralised. Sector is liberated.",
    "Enemy general defeated. Victory is ours.",
]


# ---------------------------------------------------------------------------
# Mission generation helpers
# ---------------------------------------------------------------------------


def _pick(pool: list[str]) -> str:
    return random.choice(pool)


def _enemy_positions(
    count: int, min_col: int = 6, max_col: int = 10, min_row: int = 1, max_row: int = 8
) -> list[tuple[int, int]]:
    """Generate non-overlapping enemy positions."""
    positions: set[tuple[int, int]] = set()
    attempts = 0
    while len(positions) < count and attempts < 100:
        pos = (random.randint(min_col, max_col), random.randint(min_row, max_row))
        positions.add(pos)
        attempts += 1
    return list(positions)


@dataclass
class MissionSpec:
    """Specification for generating a combat mission encounter.

    Attributes:
        mission_type: The type of mission to generate.
        enemy_count: Number of enemies to spawn.
        narrative_pool: List of possible narrative text strings.
        success_pool: List of success text strings.
        credit_base: Base credit reward.
        credit_per_enemy: Additional credits per enemy killed.
        card_pick: Number of directive cards rewarded.
    """

    mission_type: MissionType
    enemy_count: int
    narrative_pool: list[str]
    success_pool: list[str]
    credit_base: int
    credit_per_enemy: int
    card_pick: int


# Mission specifications
_MISSION_SPECS: dict[MissionType, MissionSpec] = {
    MissionType.PATROL: MissionSpec(
        mission_type=MissionType.PATROL,
        enemy_count=2,
        narrative_pool=_PATROL_TEXT,
        success_pool=_SUCCESS_TEXT,
        credit_base=40,
        credit_per_enemy=15,
        card_pick=1,
    ),
    MissionType.ASSAULT: MissionSpec(
        mission_type=MissionType.ASSAULT,
        enemy_count=3,
        narrative_pool=_ASSAULT_TEXT,
        success_pool=_SUCCESS_TEXT,
        credit_base=60,
        credit_per_enemy=20,
        card_pick=2,
    ),
    MissionType.DEFENSE: MissionSpec(
        mission_type=MissionType.DEFENSE,
        enemy_count=3,
        narrative_pool=_DEFENSE_TEXT,
        success_pool=_SUCCESS_TEXT,
        credit_base=55,
        credit_per_enemy=18,
        card_pick=1,
    ),
    MissionType.EXTRACTION: MissionSpec(
        mission_type=MissionType.EXTRACTION,
        enemy_count=2,
        narrative_pool=_EXTRACTION_TEXT,
        success_pool=_SUCCESS_TEXT,
        credit_base=50,
        credit_per_enemy=15,
        card_pick=1,
    ),
    MissionType.SABOTAGE: MissionSpec(
        mission_type=MissionType.SABOTAGE,
        enemy_count=2,
        narrative_pool=_SABOTAGE_TEXT,
        success_pool=_SUCCESS_TEXT,
        credit_base=55,
        credit_per_enemy=20,
        card_pick=2,
    ),
    MissionType.ELITE: MissionSpec(
        mission_type=MissionType.ELITE,
        enemy_count=2,
        narrative_pool=_ELITE_TEXT,
        success_pool=_SUCCESS_TEXT,
        credit_base=80,
        credit_per_enemy=25,
        card_pick=2,
    ),
    MissionType.BOSS: MissionSpec(
        mission_type=MissionType.BOSS,
        enemy_count=3,
        narrative_pool=_BOSS_TEXT,
        success_pool=_BOSS_SUCCESS,
        credit_base=150,
        credit_per_enemy=40,
        card_pick=3,
    ),
    MissionType.AMBUSH: MissionSpec(
        mission_type=MissionType.AMBUSH,
        enemy_count=4,
        narrative_pool=_AMBUSH_TEXT,
        success_pool=_SUCCESS_TEXT,
        credit_base=70,
        credit_per_enemy=20,
        card_pick=2,
    ),
}


# ---------------------------------------------------------------------------
# Floor-based mission scheduling
# ---------------------------------------------------------------------------

# Which mission types can appear on which floor ranges.
# Higher floors get more dangerous mission types.
_FLOOR_MISSIONS: dict[tuple[int, int], list[MissionType]] = {
    (1, 3): [MissionType.PATROL],
    (4, 5): [MissionType.PATROL, MissionType.ASSAULT],
    (6, 8): [MissionType.PATROL, MissionType.ASSAULT, MissionType.DEFENSE],
    (9, 10): [
        MissionType.PATROL,
        MissionType.ASSAULT,
        MissionType.DEFENSE,
        MissionType.EXTRACTION,
    ],
    (11, 13): [
        MissionType.PATROL,
        MissionType.ASSAULT,
        MissionType.DEFENSE,
        MissionType.EXTRACTION,
        MissionType.SABOTAGE,
    ],
    (14, 15): [
        MissionType.ASSAULT,
        MissionType.DEFENSE,
        MissionType.EXTRACTION,
        MissionType.SABOTAGE,
        MissionType.ELITE,
    ],
    (16, 18): [
        MissionType.ASSAULT,
        MissionType.DEFENSE,
        MissionType.EXTRACTION,
        MissionType.SABOTAGE,
        MissionType.ELITE,
        MissionType.AMBUSH,
    ],
    (19, 20): [
        MissionType.ASSAULT,
        MissionType.DEFENSE,
        MissionType.ELITE,
        MissionType.AMBUSH,
    ],
    (21, 24): [
        MissionType.ASSAULT,
        MissionType.ELITE,
        MissionType.AMBUSH,
        MissionType.SABOTAGE,
    ],
    (25, 25): [MissionType.BOSS],
}


def get_mission_types_for_floor(floor_num: int) -> list[MissionType]:
    """Return possible mission types for a given floor.

    Args:
        floor_num: Current floor (1-25).

    Returns:
        List of MissionType values available on this floor.
    """
    for (lo, hi), types in _FLOOR_MISSIONS.items():
        if lo <= floor_num <= hi:
            return list(types)
    return [MissionType.PATROL]


def is_boss_floor(floor_num: int) -> bool:
    """Check if this floor has a boss encounter."""
    return floor_num in _BOSS_ENEMIES


def get_boss_enemy_id(floor_num: int) -> str:
    """Get the boss enemy ID for a boss floor.

    Args:
        floor_num: Current floor (1-25).

    Returns:
        Enemy mech frame ID for the boss.

    Raises:
        KeyError: If floor is not a boss floor.
    """
    return _BOSS_ENEMIES[floor_num]


# ---------------------------------------------------------------------------
# Encounter generation
# ---------------------------------------------------------------------------


def generate_combat_encounter(
    floor_num: int,
    mission_type: MissionType | None = None,
    force_boss: bool = False,
) -> Encounter:
    """Generate a combat encounter for the given floor.

    Args:
        floor_num: Current floor (1-25).
        mission_type: Override mission type. Random if None.
        force_boss: Force a boss encounter regardless of floor.

    Returns:
        A fully configured Encounter with enemies, narrative, and rewards.
    """
    # Determine if this is a boss
    is_boss = force_boss or is_boss_floor(floor_num)

    # Select mission type
    if mission_type is None:
        if is_boss:
            mtype = MissionType.BOSS
        else:
            available = get_mission_types_for_floor(floor_num)
            mtype = random.choice(available)
    else:
        mtype = mission_type

    spec = _MISSION_SPECS[mtype]

    # Determine enemy count (scale slightly with floor)
    enemy_count = spec.enemy_count
    if floor_num > 15:
        enemy_count = min(enemy_count + 1, 5)

    # Select enemy pool
    if is_boss:
        boss_id = get_boss_enemy_id(floor_num)
        enemies = [EnemySpawn(mech_id=boss_id, grid_col=9, grid_row=5)]
        # Boss gets escorts
        pool = _ENEMY_POOLS.get((1, 5), [])
        for _ in range(2):
            col = random.randint(7, 10)
            row = random.randint(3, 7)
            enemies.append(
                EnemySpawn(
                    mech_id=random.choice(pool) if pool else "cc_bastion",
                    grid_col=col,
                    grid_row=row,
                )
            )
    else:
        # Get enemy pool for this floor
        pool_key = None
        for (lo, hi), pool in _ENEMY_POOLS.items():
            if lo <= floor_num <= hi:
                pool_key = pool
                break
        if pool_key is None:
            pool_key = ["cc_bastion"]

        positions = _enemy_positions(enemy_count)
        enemies = []
        for i, (col, row) in enumerate(positions):
            # Elite encounters have tougher enemies
            if mtype == MissionType.ELITE and i == 0:
                mech_id = random.choice(_ELITE_ENEMIES)
            else:
                mech_id = random.choice(pool_key)
            enemies.append(EnemySpawn(mech_id=mech_id, grid_col=col, grid_row=row))

    # Scale rewards with floor
    credits = spec.credit_base + (floor_num * 5)
    narrative = _pick(spec.narrative_pool)

    return Encounter(
        id=f"combat_f{floor_num:02d}_{mtype.name.lower()}",
        encounter_type=EncounterType.COMBAT,
        narrative_text=narrative,
        enemies=enemies,
        rewards={"credits": credits, "card_pick": spec.card_pick},
    )


def generate_event_encounter(floor_num: int) -> Encounter:
    """Generate a narrative event encounter.

    Args:
        floor_num: Current floor (1-25).

    Returns:
        An Event-type Encounter with choices.
    """
    event_templates = [
        {
            "id": f"event_f{floor_num:02d}_distress",
            "text": (
                f"> INCOMING TRANSMISSION — Floor {floor_num:02d}\n"
                f"  DISTRESS SIGNAL: Allied recon unit pinned down.\n"
                f"  Requesting immediate support or extraction orders."
            ),
            "choices": [
                {"text": "Deploy rescue team (risk casualties)", "outcome_id": "rescue_ally"},
                {"text": "Maintain position (gain intel)", "outcome_id": "gather_intel"},
                {"text": "Ignore signal (preserve resources)", "outcome_id": "ignore_distress"},
            ],
        },
        {
            "id": f"event_f{floor_num:02d}_intercept",
            "text": (
                f"> INTERCEPTED COMMS — Floor {floor_num:02d}\n"
                f"  Crimson Compact transmission decrypted.\n"
                f"  Contents: Reinforcement schedule and supply route data."
            ),
            "choices": [
                {"text": "Ambush supply convoy (+credits, risk)", "outcome_id": "ambush_convoy"},
                {"text": "Share intel with FSA (+reputation)", "outcome_id": "share_intel"},
                {"text": "Archive for later (no immediate effect)", "outcome_id": "archive_intel"},
            ],
        },
        {
            "id": f"event_f{floor_num:02d}_defectors",
            "text": (
                f"> UNSCHEDULED CONTACT — Floor {floor_num:02d}\n"
                f"  CC pilot requesting asylum. Claims to have\n"
                f"  critical intelligence on enemy operations."
            ),
            "choices": [
                {"text": "Accept defector (+rebel reputation)", "outcome_id": "accept_defector"},
                {"text": "Interrogate then release (safe)", "outcome_id": "interrogate"},
                {"text": "Turn over to FSA command (+FSA rep)", "outcome_id": "turn_over"},
            ],
        },
        {
            "id": f"event_f{floor_num:02d}_salvage",
            "text": (
                f"> BATTLEFIELD SURVEY — Floor {floor_num:02d}\n"
                f"  Wreckage from previous engagement surveyed.\n"
                f"  Recoverable parts and intelligence detected."
            ),
            "choices": [
                {"text": "Salvage everything (+equipment)", "outcome_id": "full_salvage"},
                {"text": "Take only weapons (+credits)", "outcome_id": "weapon_salvage"},
                {"text": "Leave it (avoid detection)", "outcome_id": "leave_salvage"},
            ],
        },
        {
            "id": f"event_f{floor_num:02d}_civilian",
            "text": (
                f"> CIVILIAN CONTACT — Floor {floor_num:02d}\n"
                f"  Local population requesting protection.\n"
                f"  They offer supplies and shelter in exchange."
            ),
            "choices": [
                {
                    "text": "Establish outpost (+ongoing benefits)",
                    "outcome_id": "establish_outpost",
                },
                {"text": "Take supplies and move on (+credits)", "outcome_id": "take_supplies"},
                {"text": "Cannot spare resources (decline)", "outcome_id": "decline_civilian"},
            ],
        },
    ]

    template = random.choice(event_templates)
    return Encounter(
        id=str(template["id"]),
        encounter_type=EncounterType.EVENT,
        narrative_text=str(template["text"]),
        choices=template["choices"],  # type: ignore[arg-type]
        rewards={"credits": 10 + floor_num * 3, "card_pick": 1},
    )


def generate_merchant_encounter(floor_num: int) -> Encounter:
    """Generate a merchant/supply depot encounter.

    Args:
        floor_num: Current floor (1-25).

    Returns:
        A Merchant-type Encounter.
    """
    return Encounter(
        id=f"merchant_f{floor_num:02d}",
        encounter_type=EncounterType.MERCHANT,
        narrative_text=(
            f"> SUPPLY DEPOT ONLINE — Floor {floor_num:02d}\n"
            f"  FSA forward supply cache detected.\n"
            f"  Available: ammunition, repair kits, intel packages."
        ),
        rewards={"credits": 0, "card_pick": 2},
    )


def generate_rest_encounter(floor_num: int) -> Encounter:
    """Generate a rest/R&R encounter.

    Args:
        floor_num: Current floor (1-25).

    Returns:
        A Rest-type Encounter.
    """
    rest_texts = [
        f"> FORWARD CAMP — Floor {floor_num:02d}\n"
        f"  Safe zone established. Mechanics performing maintenance.\n"
        f"  Crew reports: systems nominal, ready for next deployment.",
        f"> R&R STATION — Floor {floor_num:02d}\n"
        f"  Temporary cease-fire window. Field medics on standby.\n"
        f"  Rest and resupply before next engagement.",
        f"> SAFE HAVEN — Floor {floor_num:02d}\n"
        f"  Perimeter secure. Downtime authorised.\n"
        f"  Use this opportunity to recover and prepare.",
        f"> BIVOUAC SITE — Floor {floor_num:02d}\n"
        f"  Sheltered position. Engineering team available.\n"
        f"  Repairs in progress. Stand by for next orders.",
    ]
    return Encounter(
        id=f"rest_f{floor_num:02d}",
        encounter_type=EncounterType.REST,
        narrative_text=random.choice(rest_texts),
        rewards={"credits": 10, "card_pick": 0},
    )
