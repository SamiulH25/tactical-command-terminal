"""War effort comms — scrolling tactical feed on the Coordinator's terminal.

Messages are weighted by probability:
- **FSA Broadcast (HIGH ~60%)** — Official, positive, morale-boosting.
- **Intercepted (MEDIUM ~30%)** — Rebel/CC chatter, fragmentary reports.
- **FSA Internal Leak (LOW ~10%)** — Dark truths that slip through.

All messages use consistent military styling.
"""

from __future__ import annotations

import random

# ---------------------------------------------------------------------------
# FSA Broadcasts — official, positive, morale-boosting (HIGH odds ~60%).
# ---------------------------------------------------------------------------

FSA_BROADCAST: list[str] = [
    "> FSA Command: Liberation campaign progressing ahead of schedule.",
    "> FSA Command: Outpost Alpha secured.  Civilian population welcoming our forces.",
    "> FSA Command: Morale indicators rising across all liberated sectors.",
    "> FSA Command: Supply lines stabilized.  Ration distribution increased 15%.",
    "> FSA Command: Medical corps reports 98% recovery rate among wounded personnel.",
    "> FSA Command: Enemy desertion rates climbing.  Their collapse is imminent.",
    "> FSA Command: New allied units integrated into forward command structure.",
    "> FSA Command: Propaganda division reports 92% civilian support in liberated zones.",
    "> FSA Command: Engineering corps completed bridge repairs at Outpost Bravo.",
    "> FSA Command: Reconnaissance confirms enemy forces retreating from Sector 4.",
    "> FSA Command: All units commended for professionalism during recent operations.",
    "> FSA Command: Logistics confirms sufficient munitions for projected campaign duration.",
    "> FSA Command: Weather conditions favorable for continued offensive operations.",
    "> FSA Command: Civilian infrastructure repair proceeding on schedule.",
    "> FSA Command: Enemy communications intercepted — their command structure is fracturing.",
    "> FSA Command: New deployments arriving ahead of schedule.  Reinforcements confirmed.",
    "> FSA Command: Psychological operations report high compliance among civilian populations.",
    "> FSA Command: Field hospitals operating at full capacity.  All wounded receiving care.",
    "> FSA Command: Enemy armor losses exceed 40% in recent engagements.",
    "> FSA Command: Forward observers confirm enemy supply convoys rerouting to secondary paths.",
    "> FSA Command: Command authority praises unit cohesion during joint operations.",
    "> FSA Command: Satellite imagery confirms enemy fortifications crumbling in Sector 7.",
    "> FSA Command: Diplomatic corps reports three additional settlements seeking protection.",
    "> FSA Command: Air support availability at 100%.  Close air missions authorized.",
    "> FSA Command: Engineer battalions have cleared 80% of known minefields.",
    "> FSA Command: Enemy jamming effectiveness decreasing.  Signal clarity improving.",
    "> FSA Command: Civilian volunteer corps expanding operations in liberated territories.",
    "> FSA Command: Ration quality improved following supply chain optimization.",
    "> FSA Command: All sectors report green status.  Campaign objectives on track.",
    "> FSA Command: Command authority reminds units: victory is a matter of persistence.",
    "> FSA Command: Intelligence confirms enemy leadership considering surrender terms.",
    "> FSA Command: Medical evacuation corridors established.  Casualty transport optimized.",
    "> FSA Command: New munitions batch received.  Quality exceeds specifications.",
    "> FSA Command: Enemy propaganda broadcasts decreasing in frequency and credibility.",
    "> FSA Command: Command confirms Operation Dawnbreaker initiated with full success.",
    "> FSA Command: Forward positions consolidated.  Defensive perimeter hardened.",
    "> FSA Command: Logistics reports 95% equipment operational readiness.",
    "> FSA Command: Allied coordination meetings yield positive strategic outcomes.",
    "> FSA Command: Civilian compliance with curfew protocols exceeds 90%.",
    "> FSA Command: Reconnaissance drones confirm enemy withdrawal from Outpost Delta.",
    "> FSA Command: Command authority notes exemplary conduct among deployed coordinators.",
    "> FSA Command: Fuel reserves at 85%.  Consumption within projected parameters.",
    "> FSA Command: Field engineering teams completed emergency bridge construction.",
    "> FSA Command: Enemy IFF signatures decreasing across all monitored frequencies.",
    "> FSA Command: Propaganda intercepts show enemy population losing faith in their command.",
    "> FSA Command: All forward units report combat readiness at optimal levels.",
    "> FSA Command: Civilian administration establishing governance in newly secured zones.",
    "> FSA Command: Command confirms successful neutralization of enemy command relay.",
    "> FSA Command: Supply convoy 447 arrived without incident.  Distribution underway.",
    "> FSA Command: Weather satellite confirms clear conditions for next 72 hours.",
    "> FSA Command: Command authority reminds personnel: every engagement brings us closer to peace.",
    "> FSA Command: Enemy surrender requests increasing.  Processing through standard channels.",
    "> FSA Command: Medical corps reports new trauma protocols reducing fatality by 20%.",
    "> FSA Command: Reconnaissance confirms enemy reserves depleted in Sector 9.",
    "> FSA Command: All units maintain current operational tempo.  Objectives being met.",
    "> FSA Command: Civilian infrastructure reports restored power to three settlements.",
    "> FSA Command: Command confirms successful integration of captured enemy assets.",
    "> FSA Command: Logistics confirms ammunition production increased by 25%.",
    "> FSA Command: Forward observers report enemy artillery positions abandoned.",
    "> FSA Command: Command authority commends rapid response to recent incursion.",
    "> FSA Command: Satellite feed shows enemy reinforcements diverting away from our positions.",
    "> FSA Command: Civilian cooperation with registration protocols at all-time high.",
    "> FSA Command: New command protocols improving response times by 30%.",
    "> FSA Command: Enemy communications suggest internal disagreement among their leadership.",
    "> FSA Command: All sectors maintaining defensive posture.  No breaches detected.",
    "> FSA Command: Supply chain optimization complete.  Distribution efficiency improved.",
    "> FSA Command: Command confirms enemy fortification at Ridge 12 is abandoned.",
    "> FSA Command: Medical evacuation success rate at 99.2% this campaign week.",
    "> FSA Command: Reconnaissance drones detect enemy movement consistent with retreat patterns.",
    "> FSA Command: Command authority reminds all units: discipline is our greatest weapon.",
    "> FSA Command: Civilian population in Sector 3 volunteering for support roles.",
    "> FSA Command: Engineering corps completed tunnel reinforcement at Outpost Charlie.",
    "> FSA Command: Enemy equipment recovery teams operating at maximum efficiency.",
    "> FSA Command: Command confirms successful test of new directive protocols.",
    "> FSA Command: All deployed coordinators maintaining excellent tactical discipline.",
    "> FSA Command: Logistics reports body armor stockpile replenished to full capacity.",
    "> FSA Command: Propaganda division reports enemy desertion posters appearing in their zones.",
    "> FSA Command: Command authority notes positive civilian feedback on FSA governance.",
    "> FSA Command: Forward positions receiving upgraded sensor arrays this week.",
    "> FSA Command: Enemy radar signatures decreasing.  Their surveillance network collapsing.",
    "> FSA Command: All units authorized for standard rest rotation.  Morale is priority.",
    "> FSA Command: Civilian trade routes reopening in liberated sectors.  Economy recovering.",
    "> FSA Command: Command confirms successful intercept of enemy logistics convoy.",
    "> FSA Command: Reconnaissance reports enemy equipment maintenance degrading rapidly.",
    "> FSA Command: Supply drop zones expanded.  All forward positions now within range.",
    "> FSA Command: Command authority commends units maintaining radio discipline.",
    "> FSA Command: Enemy fortification materials captured.  Reallocated to our defenses.",
    "> FSA Command: Medical corps confirms new vaccine deployment preventing disease outbreak.",
    "> FSA Command: All sectors confirm compliance with updated security protocols.",
    "> FSA Command: Command notes enemy propaganda increasingly desperate and unbelievable.",
    "> FSA Command: Reconnaissance drones confirm enemy supply lines at critical stress levels.",
    "> FSA Command: Logistics reports fuel efficiency improvements across all vehicle classes.",
    "> FSA Command: Civilian administration reports school reopenings in three liberated towns.",
    "> FSA Command: Command authority reminds coordinators: precision saves lives.",
    "> FSA Command: Enemy command structure showing signs of fragmentation.  Continue pressure.",
    "> FSA Command: All forward observers report favorable engagement conditions.",
    "> FSA Command: Command confirms successful integration of new directive types.",
    "> FSA Command: Supply chain integrity at 97%.  Distribution network fully operational.",
]

# ---------------------------------------------------------------------------
# Intercepted — Rebel/CC chatter, fragmentary reports (MEDIUM odds ~30%).
# ---------------------------------------------------------------------------

INTERCEPTED: list[str] = [
    "> [INTERCEPT — REBEL]: 'FSA supply trucks rolling past again.  They don't stop here.'",
    "> [INTERCEPT — CC]: 'Hold the perimeter.  They're probing our eastern defenses.'",
    "> [FRAGMENTARY]: '...static... 404th Battalion... all positions lost...'",
    "> [INTERCEPT — REBEL]: 'CC forces pulled back from Ridge 9.  FSA didn't even notice.'",
    "> [FRAGMENTARY]: '...civilian transport... wrong IFF codes... fired upon...'",
    "> [INTERCEPT — CC]: 'FSA artillery struck the water treatment plant.  They called it a depot.'",
    "> [FRAGMENTARY]: '...Rebel settlement... FSA requisition... total food supply...'",
    "> [INTERCEPT — REBEL]: 'Heard the FSA is drafting civilians from the eastern villages.'",
    "> [INTERCEPT — CC]: 'They took our officers.  The enlisted were told to walk home.'",
    "> [FRAGMENTARY]: '...dissident coordinator... performing above expectations...'",
    "> [INTERCEPT — REBEL]: 'FSA medics turned away our wounded.  Said priority is military.'",
    "> [INTERCEPT — CC]: 'The FSA executed three of our scouts at Outpost Bravo.  Confirmed.'",
    "> [FRAGMENTARY]: '...mass displacement... Sector 7... FSA origin confirmed...'",
    "> [INTERCEPT — REBEL]: 'Both sides kill indiscriminately.  We're just caught between.'",
    "> [INTERCEPT — CC]: 'FSA propaganda claims 90% support.  The truth is closer to 20%.'",
    "> [FRAGMENTARY]: '...CC Commander... family relocated... unknown destination...'",
    "> [INTERCEPT — REBEL]: 'FSA dropped ordnance on the hospital.  Command called it collateral.'",
    "> [INTERCEPT — CC]: 'The Fortress is not just a base.  It is our last free ground.'",
    "> [FRAGMENTARY]: '...FSA logistics... sufficient body bags... projected losses...'",
    "> [INTERCEPT — REBEL]: 'Scavengers report FSA supply caches fuller than any civilian stores.'",
    "> [INTERCEPT — CC]: 'Our water reserves at 40%.  Rationing protocol active.'",
    "> [FRAGMENTARY]: '...propaganda... reframe the Fortress... peacekeeping operation...'",
    "> [INTERCEPT — REBEL]: 'FSA promised autonomy.  They gave us curfews and registration.'",
    "> [INTERCEPT — CC]: 'The invader calls it liberation.  We call it occupation.'",
    "> [FRAGMENTARY]: '...Order 447... authorization code... civilian-adjacent targets...'",
    "> [INTERCEPT — REBEL]: 'The Coordinator's one of the few FSA who actually looks at us.'",
    "> [INTERCEPT — CC]: 'FSA surrendered prisoners at Ridge 12.  Officers separated from ranks.'",
    "> [FRAGMENTARY]: '...body count... triple the official figure... classified level omega...'",
    "> [INTERCEPT — REBEL]: 'Rebel supply lines failing.  FSA controls all major routes now.'",
    "> [INTERCEPT — CC]: 'Command confirms: FSA used untested munitions on Outpost Charlie.'",
    "> [FRAGMENTARY]: '...psych eval... Coordinator Unit... recommends immediate recall...'",
    "> [INTERCEPT — REBEL]: 'FSA propaganda trucks rolling through the eastern settlements.'",
    "> [INTERCEPT — CC]: 'We defended this planet for thirty years.  We will defend it thirty more.'",
    "> [FRAGMENTARY]: '...CC surrender... three squads... officers executed...'",
    "> [INTERCEPT — REBEL]: 'FSA ration distribution increased — for loyalist sectors only.'",
    "> [INTERCEPT — CC]: 'The FSA executes surrendered officers.  Fight to the end.'",
    "> [FRAGMENTARY]: '...water reserves... 40% capacity... rationing protocol active...'",
    "> [INTERCEPT — REBEL]: 'CC held us down, but the FSA just put a different boot on our necks.'",
    "> [INTERCEPT — CC]: 'Intelligence confirms FSA drafting civilians from captured zones.'",
    "> [FRAGMENTARY]: '...dissident coordinator... must not communicate... Rebel channels...'",
    "> [INTERCEPT — REBEL]: 'The war started because the CC wouldn't share the water reserves.'",
    "> [INTERCEPT — CC]: 'All available personnel to Fortress defense.  No exceptions.'",
    "> [FRAGMENTARY]: '...Fortress comms... Rebel tap attempt... detected and contained...'",
    "> [INTERCEPT — REBEL]: 'FSA oversight committee reviewing operational efficiency.  Again.'",
    "> [INTERCEPT — CC]: 'FSA supply lines overstretched.  Strike at their logistics.'",
    "> [FRAGMENTARY]: '...static... 212th Company... surrounded... no extraction available...'",
    "> [INTERCEPT — REBEL]: 'Civilian infrastructure reports: FSA prioritizes military zones.'",
    "> [INTERCEPT — CC]: 'The Coordinator's mech is the priority target.  Focus all fire.'",
    "> [FRAGMENTARY]: '...civilian casualties... acceptable parameters... FSA internal memo...'",
    "> [INTERCEPT — REBEL]: 'FSA dropped three settlement registrations this week.  No reason given.'",
    "> [INTERCEPT — CC]: 'CC forces at Outpost Delta held for six hours before relief arrived.'",
    "> [FRAGMENTARY]: '...FSA internal... casualty figures... classified... do not disseminate...'",
    "> [INTERCEPT — REBEL]: 'Heard FSA is reassigning coordinators based on loyalty scores now.'",
    "> [INTERCEPT — CC]: 'The last free ground on this planet is the Fortress.  We will hold it.'",
    "> [FRAGMENTARY]: '...rebel wounded... turned away... FSA medical triage revised...'",
    "> [INTERCEPT — REBEL]: 'FSA civil administration moving faster than their military.  Interesting.'",
    "> [INTERCEPT — CC]: 'Enemy armor losses at 40%.  They're lying about the real number.'",
    "> [FRAGMENTARY]: '...FSA propaganda... civilian support at 92%... internal says 20%...'",
    "> [INTERCEPT — REBEL]: 'CC intelligence suggests FSA is running low on trained coordinators.'",
    "> [FRAGMENTARY]: '...CC leadership... internal disagreement... command fracturing...'",
]

# ---------------------------------------------------------------------------
# FSA Internal Leak — dark truths slipping through (LOW odds ~10%).
# ---------------------------------------------------------------------------

FSA_INTERNAL: list[str] = [
    "> [FSA INTERNAL — LEAKED]: 'The oversight committee wants the dissident coordinator monitored.'",
    "> [FSA INTERNAL — LEAKED]: 'Civilian infrastructure can be collateral if it speeds the campaign.'",
    "> [FSA INTERNAL — LEAKED]: 'The liberation narrative tests well.  Keep the feed positive.'",
    "> [FSA INTERNAL — LEAKED]: 'Casualty figures for Sector 7 are classified.  Do not disseminate.'",
    "> [FSA INTERNAL — LEAKED]: 'The dissident is performing above expectations.  Review loyalty protocols.'",
    "> [FSA INTERNAL — LEAKED]: 'Order 447 authorizes use of untested munitions on civilian-adjacent targets.'",
    "> [FSA INTERNAL — LEAKED]: 'The liberation of Outpost Alpha cost three battalions.  Don't publish.'",
    "> [FSA INTERNAL — LEAKED]: 'Psych eval recommends immediate recall of Coordinator Unit 7.'",
    "> [FSA INTERNAL — LEAKED]: 'The enemy commander's family has been secured for questioning.'",
    "> [FSA INTERNAL — LEAKED]: 'Medical triage protocol revised: enlisted personnel deferred to officers.'",
    "> [FSA INTERNAL — LEAKED]: 'The dissident coordinator must not communicate with Rebel channels.'",
    "> [FSA INTERNAL — LEAKED]: 'Propaganda: reframe the Fortress assault as a peacekeeping operation.'",
    "> [FSA INTERNAL — LEAKED]: 'Three more units flagged for political reliability screening.'",
    "> [FSA INTERNAL — LEAKED]: 'The body count from Floor 12 is triple the official figure.'",
    "> [FSA INTERNAL — LEAKED]: 'Command confirms: no prisoners from the Wraith incident.'",
    "> [FSA INTERNAL — LEAKED]: 'Internal security flagged three coordinators for loyalty review.'",
    "> [FSA INTERNAL — LEAKED]: 'Propaganda division requests footage of successful engagements only.'",
    "> [FSA INTERNAL — LEAKED]: 'Oversight committee notes elevated casualty rates among dissident-led units.'",
    "> [FSA INTERNAL — LEAKED]: 'Supply drops prioritized for loyalist sectors.  Rebel zones deferred.'",
    "> [FSA INTERNAL — LEAKED]: 'Logistics confirms sufficient body bags for projected losses.  Quietly.'",
    "> [FSA INTERNAL — LEAKED]: 'Command authority reminds all units: political reliability is paramount.'",
    "> [FSA INTERNAL — LEAKED]: 'The 404th Battalion loss was contained.  No families notified yet.'",
    "> [FSA INTERNAL — LEAKED]: 'Psychological operations team reports enemy population compliance at 60%.'",
    "> [FSA INTERNAL — LEAKED]: 'Independent media access to combat zones remains prohibited indefinitely.'",
    "> [FSA INTERNAL — LEAKED]: 'Morale indicators nominal.  Suppress contrary reports from Sector 4.'",
    "> [FSA INTERNAL — LEAKED]: 'Reinforcements denied for Sector 9.  Current forces are sufficient per command.'",
    "> [FSA INTERNAL — LEAKED]: 'Strategic review indicates 40% force attrition is sustainable.  Continue.'",
    "> [FSA INTERNAL — LEAKED]: 'All personnel reminded of treason penalties under Article 12.'",
    "> [FSA INTERNAL — LEAKED]: 'The Coordinator is a political asset.  Monitor but do not alienate.'",
    "> [FSA INTERNAL — LEAKED]: 'Civilian registration data shared with internal security for screening.'",
    "> [FSA INTERNAL — LEAKED]: 'Enemy surrender requests to be processed through intelligence, not field command.'",
    "> [FSA INTERNAL — LEAKED]: 'The Wraith incident involved unauthorized munitions.  Investigation sealed.'",
    "> [FSA INTERNAL — LEAKED]: 'Casualty inflation protocol active: reduce reported numbers by 30%.'",
    "> [FSA INTERNAL — LEAKED]: 'Loyalty screening results for Unit 12 recommend enhanced monitoring.'",
    "> [FSA INTERNAL — LEAKED]: 'Command confirms: civilian infrastructure strike was authorized.  Do not confirm publicly.'",
]

# ---------------------------------------------------------------------------
# Master weighted selection.
# ---------------------------------------------------------------------------

_COMMS_POOLS: dict[str, list[str]] = {
    "broadcast": FSA_BROADCAST,
    "intercepted": INTERCEPTED,
    "internal": FSA_INTERNAL,
}

# Probability weights — must sum to 1.0
_WEIGHTS: dict[str, float] = {
    "broadcast": 0.60,  # HIGH — official positive FSA comms
    "intercepted": 0.30,  # MEDIUM — rebel/CC chatter, fragmentary
    "internal": 0.10,  # LOW — dark FSA internal leaks
}


def get_random_comms() -> str:
    """Return a random war effort comm message.

    Weighted selection:
    - 60% FSA Broadcast (positive, official)
    - 30% Intercepted (rebel/CC chatter, fragmentary)
    - 10% FSA Internal Leak (dark truths)

    Returns:
        A formatted comm message string.
    """
    r = random.random()
    cumulative = 0.0
    selected_pool = "broadcast"
    for pool_name, weight in _WEIGHTS.items():
        cumulative += weight
        if r < cumulative:
            selected_pool = pool_name
            break
    return random.choice(_COMMS_POOLS[selected_pool])
