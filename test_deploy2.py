import traceback
try:
    from src.models.data_loader import load_all_data
    from src.systems.deckbuilder import build_deployed_mech

    data = load_all_data()
    frame = data.get_mech('fsa_bastion')
    pilot = data.get_pilot('aggressive')
    deployed = build_deployed_mech(frame, pilot, data)

    with open('t6.txt', 'w') as f:
        f.write('Deployed: %s\n' % deployed.pilot_callsign)
        f.write('HP: %d/%d\n' % (deployed.current_hp, deployed.max_hp))
        f.write('OL: %d/%d\n' % (deployed.current_ol, deployed.max_ol))
        f.write('Deck: %d cards\n' % len(deployed.deck))
        f.write('Weapon bonus: %d\n' % deployed.weapon_bonus)
        f.write('Evasion: %d\n' % deployed.evasion)
        for i, did in enumerate(deployed.deck[:10]):
            f.write('  %d: %s\n' % (i, did))
except Exception as e:
    with open('t6.txt', 'w') as f:
        traceback.print_exc(file=f)
