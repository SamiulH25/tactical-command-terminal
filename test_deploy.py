import traceback
try:
    from src.models.data_loader import load_all_data
    data = load_all_data()
    with open('t5.txt', 'w') as f:
        f.write('OK: %d mechs\n' % len(data.mech_frames))
except Exception as e:
    with open('t5.txt', 'w') as f:
        traceback.print_exc(file=f)
